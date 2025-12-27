from dataclasses import dataclass, field
from typing import List


@dataclass
class CartItem:
    product_id: int
    product_name: str
    price: float
    quantity: int


@dataclass
class Cart:
    items: List[CartItem] = field(default_factory=list)

    def add_item(self, product_id: int, product_name: str, price: float, quantity: int = 1):
        for item in self.items:
            if item.product_id == product_id:
                item.quantity += quantity
                return
        self.items.append(CartItem(product_id, product_name, price, quantity))

    def remove_item(self, product_id: int):
        self.items = [item for item in self.items if item.product_id != product_id]

    def update_quantity(self, product_id: int, quantity: int):
        for item in self.items:
            if item.product_id == product_id:
                if quantity <= 0:
                    self.remove_item(product_id)
                else:
                    item.quantity = quantity
                return

    def get_total(self) -> float:
        return sum(item.price * item.quantity for item in self.items)

    def clear(self):
        self.items = []
