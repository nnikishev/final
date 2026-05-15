from pydantic import BaseModel
from uuid import UUID
from typing import Optional, Dict

class DefectCreate(BaseModel):
    board_id: UUID
    defect_type: str
    confidence: float
    position_from_start_mm: float
    width_mm: float
    bbox_px: Dict[int, int]
    frame_idx: int

class DefectOut(DefectCreate):
    id: UUID