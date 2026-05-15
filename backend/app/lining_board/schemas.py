from datetime import datetime, time
from typing import Literal, Union

from pydantic import BaseModel


QualityLiteral = Literal["A", "B", "C", "D"]
DefectSeverityLiteral = Literal["low", "medium", "high", "critical"]


class DefectDTO(BaseModel):
    id: str
    defect_type: str
    severity: DefectSeverityLiteral
    location: str

class CuttingSegmentDTO(BaseModel):
    from_mm: float
    to_mm: float
    grade: Union[int, str]
    length_m: float
    price: float

class CuttingPlanDTO(BaseModel):
    board_id: str
    segments: list[CuttingSegmentDTO]
    total_revenue: float
    algorithm: str

class FrontendBoardDTO(BaseModel):
    board_id: str
    quality: QualityLiteral
    defects: list[DefectDTO]
    timestamp: datetime
    processing_duration: float
    total_length_mm: Union[float, int] | None
    cutting_plan: CuttingPlanDTO | None = None   
    revenue: float | None = None                 


class FrontendBoardsResponseDTO(BaseModel):
    boards: list[FrontendBoardDTO]
    total: int


class TopDefectDTO(BaseModel):
    type: str
    count: int


class BoardsByHourDTO(BaseModel):
    hour: str
    count: int


class QualityDistributionDTO(BaseModel):
    A: int
    B: int
    C: int
    D: int


class DashboardMetricsDTO(BaseModel):
    totalBoards: int
    avgProcessingDuration: float
    qualityDistribution: QualityDistributionDTO
    totalDefects: int
    topDefects: list[TopDefectDTO]
    boardsByHour: list[BoardsByHourDTO]


class LiningBoardCreateDTO(BaseModel):
    start_time: time
    end_time: time
    defect_counts: dict[str, int] | None = None
    total_defects: int | None = 0
    quality: QualityLiteral
    defect_photos: list[str] | None = None


class LiningBoardUpdateDTO(BaseModel):
    start_time: time | None = None
    end_time: time | None = None
    defect_counts: dict[str, int] | None = None
    total_defects: int | None = None
    quality: QualityLiteral | None = None
    defect_photos: list[str] | None = None


class LiningBoardDTO(BaseModel):
    board_number: int
    start_time: time
    end_time: time
    defect_counts: dict[str, int] | None = None
    total_defects: int | None = None
    quality: QualityLiteral
    defect_photos: list[str] | None = None


class StatusResponseDTO(BaseModel):
    status: str


class MLBoardMessageDTO(BaseModel):
    board_number: int
    start_time: float
    end_time: float
    duration: float
    defect_counts: dict[str, int]
    total_defects: int
    quality: str
    defect_photos: list[str]


# Новое сообщение от cutting_service
class CuttingPlanMessageDTO(BaseModel):
    board_id: str
    segments: list[dict]   # будет валидироваться в CuttingPlanDTO
    total_revenue: float