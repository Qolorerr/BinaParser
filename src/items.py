from dataclasses import dataclass


@dataclass
class Item:
    id: int
    price: str
    location: str
