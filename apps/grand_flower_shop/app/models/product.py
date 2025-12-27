from dataclasses import dataclass
from typing import Optional


@dataclass
class Product:
    id: int
    name: str
    description: str
    price: float
    currency: str = "USD"
    category: Optional[str] = None
    image_url: Optional[str] = None
