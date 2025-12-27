from dataclasses import dataclass
from typing import Optional


@dataclass
class Branch:
    id: int
    name: str
    country: str
    city: str
    address: str
    phone: Optional[str] = None
    timezone: Optional[str] = None
