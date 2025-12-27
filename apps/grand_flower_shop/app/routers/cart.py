from fastapi import APIRouter
from pydantic import BaseModel

from ..services.cart_service import get_cart
from ..services.file_service import load_json
from pathlib import Path

router = APIRouter()
DATA_DIR = Path(__file__).resolve().parent.parent / "data"


class AddToCartRequest(BaseModel):
    product_id: int
    quantity: int = 1


class UpdateCartItemRequest(BaseModel):
    quantity: int


@router.get("/cart")
def get_cart_items():
    cart = get_cart()
    return {
        "items": [
            {
                "product_id": item.product_id,
                "product_name": item.product_name,
                "price": item.price,
                "quantity": item.quantity,
                "subtotal": item.price * item.quantity,
            }
            for item in cart.items
        ],
        "total": cart.get_total(),
    }


@router.post("/cart/add")
def add_to_cart(request: AddToCartRequest):
    products = load_json(DATA_DIR / "products.json")
    product = next((p for p in products if p["id"] == request.product_id), None)
    if not product:
        return {"error": "Product not found"}, 404

    cart = get_cart()
    cart.add_item(request.product_id, product["name"], product["price"], request.quantity)
    return {
        "message": "Product added to cart",
        "items_count": sum(item.quantity for item in cart.items),
    }


@router.put("/cart/update/{product_id}")
def update_cart_item(product_id: int, request: UpdateCartItemRequest):
    cart = get_cart()
    cart.update_quantity(product_id, request.quantity)
    return {"message": "Cart updated", "total": cart.get_total()}


@router.delete("/cart/remove/{product_id}")
def remove_from_cart(product_id: int):
    cart = get_cart()
    cart.remove_item(product_id)
    return {"message": "Item removed", "total": cart.get_total()}


@router.post("/cart/clear")
def clear_cart():
    cart = get_cart()
    cart.clear()
    return {"message": "Cart cleared"}
