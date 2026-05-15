from pydantic import BaseModel
from typing import List, Tuple

class PriceItem(BaseModel):
    length_m: float
    grade: int
    price: float

class PriceListUpdate(BaseModel):
    items: List[PriceItem]