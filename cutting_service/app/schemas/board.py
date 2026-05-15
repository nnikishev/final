from pydantic import BaseModel
from uuid import UUID
from datetime import datetime
from typing import Optional, Dict

class BoardCreate(BaseModel):
    camera_id: str
    start_time: datetime
    total_length_mm: Optional[float] = None

class BoardOut(BaseModel):
    id: UUID
    camera_id: str
    start_time: datetime
    end_time: Optional[datetime]
    total_length_mm: Optional[float]
    defects_summary: Optional[Dict[str, int]]
    created_at: datetime

    class Config:
        from_attributes = True