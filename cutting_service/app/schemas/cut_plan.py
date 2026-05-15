from pydantic import BaseModel
from uuid import UUID
from typing import List, Optional
from datetime import datetime

class Segment(BaseModel):
    from_mm: float
    to_mm: float
    grade: int          # сорт, присвоенный отрезку
    length_m: float
    price: float
    order_id: Optional[str] = None

class CutPlanOut(BaseModel):
    id: UUID
    board_id: UUID
    segments: List[Segment]
    total_revenue: float
    algorithm: str
    created_at: datetime