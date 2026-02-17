from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from .routers import branches, cart, products
from .services.file_service import load_json

BASE_DIR = Path(__file__).parent
DATA_DIR = BASE_DIR / "data"
TEMPLATES_DIR = BASE_DIR / "templates"
STATIC_DIR = BASE_DIR / "static"

app = FastAPI(title="Grand Flower Shop")

# Mount static assets
app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

# Include API routers
app.include_router(products.router, prefix="/api", tags=["products"])
app.include_router(branches.router, prefix="/api", tags=["branches"])
app.include_router(cart.router, prefix="/api", tags=["cart"])

# Templates
templates = Jinja2Templates(directory=str(TEMPLATES_DIR))

@app.get("/health")
def health():
    return {"status": "ok"}

@app.get("/")
def home(request: Request):
    products_data = load_json(DATA_DIR / "products.json")
    branches_data = load_json(DATA_DIR / "branches.json")
    return templates.TemplateResponse(
        "index.html",
        {
            "request": request,
            "product_count": len(products_data),
            "branch_count": len(branches_data),
        },
    )

@app.get("/products")
def products_page(request: Request):
    items = load_json(DATA_DIR / "products.json")
    return templates.TemplateResponse(
        "products.html",
        {
            "request": request,
            "products": items,
        },
    )

@app.get("/branches")
def branches_page(request: Request):
    items = load_json(DATA_DIR / "branches.json")
    return templates.TemplateResponse(
        "branches.html",
        {
            "request": request,
            "branches": items,
        },
    )

@app.get("/cart")
def cart_page(request: Request):
    from .services.cart_service import get_cart
    cart = get_cart()
    return templates.TemplateResponse(
        "cart.html",
        {
            "request": request,
            "items": cart.items,
            "total": cart.get_total(),
        },
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000, reload=True)
