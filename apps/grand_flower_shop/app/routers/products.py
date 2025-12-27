from pathlib import Path
from fastapi import APIRouter

from ..services.file_service import load_json

router = APIRouter()
DATA_DIR = Path(__file__).resolve().parent.parent / "data"

@router.get("/products")
def list_products():
    return load_json(DATA_DIR / "products.json")
