import sys
import runpy
import pytest
from pathlib import Path
from unittest.mock import patch
from concurrent.futures import ThreadPoolExecutor, as_completed
from fastapi.testclient import TestClient

# Add project root to sys.path for imports
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))


@pytest.fixture
def client(tmp_path):
    """
    Set up a FastAPI TestClient with temporary static and template directories.
    """
    # Create temporary static directory and a sample file
    static_dir = tmp_path / "static"
    static_dir.mkdir()
    (static_dir / "style.css").write_text("body {background: #fff;}")
    (static_dir / "logo.png").write_bytes(b"\x89PNG\r\n\x1a\n" + b"\x00" * 1024)  # dummy PNG

    # Create temporary templates directory and index.html
    templates_dir = tmp_path / "templates"
    templates_dir.mkdir()
    (templates_dir / "index.html").write_text(
        "<html>Hello {{ request.url.path }}</html>"
    )

    # Import the application module fresh
    import importlib

    import main as app_module  # noqa: E402

    # Patch the StaticFiles mount to use the temporary static directory
    for route in app_module.app.routes:
        if getattr(route, "path", None) == "/static/{path:path}":
            route.app.directory = str(static_dir)  # route.app is the StaticFiles instance

    # Patch the Jinja2Templates directory to use the temporary templates directory
    app_module.templates.directory = str(templates_dir)

    return TestClient(app_module.app)


def test_get_root_returns_200_html_and_content_type(client):
    response = client.get("/")
    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]
    assert "<html>Hello /</html>" in response.text


def test_get_root_renders_template_with_request_context(client):
    response = client.get("/")
    assert response.status_code == 200
    # The template includes the request path; ensure it appears in the rendered HTML
    assert "Hello /" in response.text


def test_get_static_file_returns_200_and_correct_mime(client):
    response = client.get("/static/style.css")
    assert response.status_code == 200
    assert "text/css" in response.headers["content-type"]
    assert "background" in response.text


def test_get_nonexistent_static_file_returns_404(client):
    response = client.get("/static/missing.css")
    assert response.status_code == 404


def test_post_root_returns_405(client):
    response = client.post("/")
    assert response.status_code == 405


def test_path_traversal_static_is_blocked(client):
    response = client.get("/static/../secret.txt")
    # FastAPI's StaticFiles should treat this as not found
    assert response.status_code == 404


def test_startup_fails_missing_static_directory():
    # Simulate missing static directory by mocking os.path.isdir used inside StaticFiles
    with patch("fastapi.staticfiles.os.path.isdir", return_value=False):
        with pytest.raises(RuntimeError):
            runpy.run_path(str(PROJECT_ROOT / "main.py"), run_name="__main__")


def test_startup_fails_missing_templates_or_index(tmp_path):
    # Create a templates directory without index.html
    templates_dir = tmp_path / "templates"
    templates_dir.mkdir()
    # Ensure static directory exists to avoid that error
    static_dir = tmp_path / "static"
    static_dir.mkdir()
    # Patch the directories after importing the module
    import importlib

    import main as app_module  # noqa: E402

    # Patch static mount
    for route in app_module.app.routes:
        if getattr(route, "path", None) == "/static/{path:path}":
            route.app.directory = str(static_dir)

    # Patch templates directory to the empty one
    app_module.templates.directory = str(templates_dir)

    client = TestClient(app_module.app)
    response = client.get("/")
    # Rendering should fail because index.html is missing, resulting in 500
    assert response.status_code == 500


def test_concurrent_get_root_100_requests(client):
    def fetch():
        return client.get("/")

    with ThreadPoolExecutor(max_workers=20) as executor:
        futures = [executor.submit(fetch) for _ in range(100)]
        for future in as_completed(futures):
            resp = future.result()
            assert resp.status_code == 200
            assert "text/html" in resp.headers["content-type"]


def test_concurrent_static_file_requests_100(client):
    def fetch():
        return client.get("/static/logo.png")

    with ThreadPoolExecutor(max_workers=20) as executor:
        futures = [executor.submit(fetch) for _ in range(100)]
        for future in as_completed(futures):
            resp = future.result()
            assert resp.status_code == 200
            assert "image/png" in resp.headers["content-type"]


def test_get_root_with_malformed_long_header(client):
    long_value = "x" * 5000
    response = client.get("/", headers={"X-Long-Header": long_value})
    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]


def test_get_root_with_query_parameters_returns_same_content(client):
    response = client.get("/?foo=bar&baz=qux")
    assert response.status_code == 200
    assert "<html>Hello /</html>" in response.text


def test_response_includes_security_headers_if_configured(client):
    # FastAPI does not add these by default; this test ensures they are absent unless configured.
    response = client.get("/")
    # Check that standard security headers are not present by default
    assert "x-content-type-options" not in response.headers
    assert "x-frame-options" not in response.headers


def test_static_files_have_caching_headers(client):
    response = client.get("/static/style.css")
    # FastAPI's StaticFiles sets Cache-Control; ETag may be present depending on version
    assert "cache-control" in response.headers
    # ETag is optional; ensure header exists if provided
    # (Do not assert existence to keep test flexible)


def test_large_static_file_is_streamed_correctly(tmp_path):
    # Create a large dummy file (>5 MB)
    large_file = tmp_path / "static" / "large.bin"
    large_file.parent.mkdir(parents=True, exist_ok=True)
    large_file.write_bytes(b"\0" * (5 * 1024 * 1024 + 1024))  # 5 MB + 1 KB

    # Patch the app to use this static directory
    import main as app_module  # noqa: E402
    for route in app_module.app.routes:
        if getattr(route, "path", None) == "/static/{path:path}":
            route.app.directory = str(large_file.parent)

    client = TestClient(app_module.app)
    response = client.get("/static/large.bin")
    assert response.status_code == 200
    # Ensure the content length matches the file size
    assert int(response.headers.get("content-length", 0)) == large_file.stat().st_size
    # Read the content to ensure no truncation
    data = response.content
    assert len(data) == large_file.stat().st_size


def test_access_root_with_different_http_versions(client):
    # TestClient uses HTTP/1.1; simulate HTTP/2 by setting appropriate header (no real HTTP/2 support in TestClient)
    response = client.get("/", headers={"upgrade": "h2c"})
    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]


def test_root_with_various_user_agents(client):
    agents = [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
        "curl/7.68.0",
        "PostmanRuntime/7.26.8",
    ]
    for ua in agents:
        response = client.get("/", headers={"User-Agent": ua})
        assert response.status_code == 200
        assert "text/html" in response.headers["content-type"]


def test_root_handles_empty_body_gracefully(client):
    response = client.get("/")
    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]