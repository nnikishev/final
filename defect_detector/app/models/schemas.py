from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime
from uuid import UUID, uuid4

class DefectType(str):
    alive_knot = "alive_knot"
    dead_knot = "dead_knot"
    missed_knot = "missed_knot"
    resin_pocket = "resin_pocket"
    broken_board = "broken_board"

class BBox(BaseModel):
    x1: int
    y1: int
    x2: int
    y2: int

class DefectInFrame(BaseModel):
    type: str
    confidence: float
    bbox_px: BBox
    frame_idx: int

class DefectEvent(BaseModel):
    """Событие дефекта, отправляемое в очередь."""
    type: str = "defect"
    board_id: UUID
    defect_type: str
    confidence: float
    position_mm: Dict[str, float]  # {"from_start_mm": ..., "width_mm": ...}
    bbox_px: BBox
    frame_idx: int
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    image_source: str

class BoardStartEvent(BaseModel):
    type: str = "board_start"
    board_id: UUID
    camera_id: str
    start_frame: int
    start_time_sec: float
    timestamp: datetime = Field(default_factory=datetime.utcnow)

class BoardEndEvent(BaseModel):
    type: str = "board_end"
    board_id: UUID
    total_length_mm: float
    defects_summary: Dict[str, int]   # тип дефекта -> количество
    quality_preliminary: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class StartCameraRequest(BaseModel):
    camera_id: str
    rtsp_url: str

class CameraStatusResponse(BaseModel):
    is_running: bool
    camera_id: Optional[str] = None
    boards_processed: int = 0
    total_defects_detected: int = 0
    processing_fps: float = 0.0

class TestImageResponse(BaseModel):
    defects: List[DefectInFrame]
    annotated_image_url: Optional[str] = None

class TestVideoTaskResponse(BaseModel):
    task_id: str
    status: str   # "pending", "processing", "completed", "failed"