import sys
import importlib
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest
from fastapi.testclient import TestClient
from fastapi import FastAPI
from fastapi.responses import HTMLResponse

# Add project root to sys.path for imports
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

# Helper to import the main module fresh
def import_main():
    if "main" in sys.modules:
        del sys.modules["main"]
    return importlib.import_module("main")


def test_app_instance_exposed():
    main_mod = import_main()
    assert isinstance(main_mod.app, FastAPI)


def test_get_root_returns_200_and_html():
    main_mod = import_main()
    with patch.object(main_mod.templates, "TemplateResponse") as mock_template:
        mock_template.return_value = HTMLResponse(content="<html>OK</html>", status_code=200)
        client = TestClient(main_mod.app)
        response = client.get("/")
        assert response.status_code == 200
        assert "<html>OK</html>" in response.text
        mock_template.assert_called_once()
        args, kwargs = mock_template.call_args
        assert args[0] == "index.html"
        # ensure request object is passed in context
        assert "request" in kwargs["context"]


def test_get_root_passes_request_to_template():
    main_mod = import_main()
    captured = {}

    def fake_template(name, context):
        captured["name"] = name
        captured["context"] = context
        return HTMLResponse(content="ok")

    with patch.object(main_mod.templates, "TemplateResponse", side_effect=fake_template):
        client = TestClient(main_mod.app)
        client.get("/")
        assert captured["name"] == "index.html"
        assert "request" in captured["context"]
        assert hasattr(captured["context"]["request"], "method")


def test_get_root_missing_template_raises_500():
    main_mod = import_main()
    with patch.object(main_mod.templates, "TemplateResponse", side_effect=FileNotFoundError("missing")):
        client = TestClient(main_mod.app)
        response = client.get("/")
        assert response.status_code == 500


def test_static_file_exists_returns_200_and_content_type(tmp_path):
    # Create temporary static directory with a CSS file
    static_dir = tmp_path / "static"
    static_dir.mkdir()
    css_file = static_dir / "style.css"
    css_file.write_text("body { color: red; }")

    # Change cwd so that FastAPI mounts the temporary directory
    with patch.object(Path, "cwd", return_value=tmp_path):
        main_mod = import_main()
        client = TestClient(main_mod.app)
        response = client.get("/static/style.css")
        assert response.status_code == 200
        assert response.headers["content-type"].startswith("text/css")
        assert "color: red" in response.text


def test_static_file_missing_returns_404(tmp_path):
    static_dir = tmp_path / "static"
    static_dir.mkdir()
    with patch.object(Path, "cwd", return_value=tmp_path):
        main_mod = import_main()
        client = TestClient(main_mod.app)
        response = client.get("/static/missing.js")
        assert response.status_code == 404


def test_static_directory_traversal_is_blocked(tmp_path):
    static_dir = tmp_path / "static"
    static_dir.mkdir()
    # create a file outside static to attempt traversal
    outside_file = tmp_path / "secret.txt"
    outside_file.write_text("top secret")
    with patch.object(Path, "cwd", return_value=tmp_path):
        main_mod = import_main()
        client = TestClient(main_mod.app)
        response = client.get("/static/../secret.txt")
        assert response.status_code in (403, 404)


def test_post_root_returns_405():
    main_mod = import_main()
    client = TestClient(main_mod.app)
    response = client.post("/")
    assert response.status_code == 405


def test_concurrent_get_root_requests():
    main_mod = import_main()
    client = TestClient(main_mod.app)

    def make_request():
        resp = client.get("/")
        assert resp.status_code == 200

    import threading

    threads = [threading.Thread(target=make_request) for _ in range(100)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()


def test_get_root_with_malformed_query():
    main_mod = import_main()
    client = TestClient(main_mod.app)
    response = client.get("/?<>%")
    assert response.status_code == 200


def test_startup_missing_static_directory_raises():
    # Patch os.path.isdir used internally by StaticFiles to simulate missing dir
    with patch("fastapi.staticfiles.os.path.isdir", return_value=False):
        with pytest.raises(RuntimeError):
            import_main()


def test_startup_missing_templates_directory_raises():
    # Patch os.path.isdir used by Jinja2Templates to simulate missing dir
    with patch("fastapi.templating.os.path.isdir", return_value=False):
        with pytest.raises(RuntimeError):
            import_main()


def test_large_header_handled_gracefully():
    main_mod = import_main()
    client = TestClient(main_mod.app)
    large_value = "A" * 9000  # >8KB
    response = client.get("/", headers={"X-Custom-Header": large_value})
    # FastAPI/Starlette will return 200 unless server imposes limit; ensure not 500
    assert response.status_code != 500


def test_static_file_caching_headers(tmp_path):
    static_dir = tmp_path / "static"
    static_dir.mkdir()
    file_path = static_dir / "image.png"
    file_path.write_bytes(b"\x89PNG\r\n\x1a\n")
    with patch.object(Path, "cwd", return_value=tmp_path):
        main_mod = import_main()
        client = TestClient(main_mod.app)
        response = client.get("/static/image.png")
        assert response.status_code == 200
        # Check for typical caching headers
        assert "etag" in response.headers
        assert "cache-control" in response.headers


def test_invalid_http_method_returns_405():
    main_mod = import_main()
    client = TestClient(main_mod.app)
    response = client.request("FOO", "/")
    assert response.status_code == 405