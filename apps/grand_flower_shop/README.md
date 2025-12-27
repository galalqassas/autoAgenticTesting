# Grand Flower Shop

A world-scale flower shop website backend (FastAPI) with simple server-rendered pages and JSON APIs for branches and products.

## Features

- Global branches directory with locations
- Product catalog with prices and categories
- Server-rendered pages (Jinja2) and JSON API endpoints
- Static assets for basic styles

## Requirements

- Python 3.10+

## Setup

```bash
python -m pip install -r grand_flower_shop/requirements.txt
```

## Run (development)

```bash
python -m uvicorn grand_flower_shop.app.main:app --reload --port 8000
# Or
python -m grand_flower_shop.app.main
```

## Try It

- Home: http://localhost:8000/
- Products page: http://localhost:8000/products (20 flowers!)
- Branches page: http://localhost:8000/branches
- Cart: http://localhost:8000/cart
- Health: http://localhost:8000/health
- Products API: http://localhost:8000/api/products
- Branches API: http://localhost:8000/api/branches
- Cart API: http://localhost:8000/api/cart

## Tests

```bash
python -m pip install pytest
pytest -q
```
