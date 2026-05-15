from sqlalchemy import Column, String, Float, Integer, DateTime, ForeignKey, JSON
from sqlalchemy.dialects.postgresql import UUID
from app.models.board import Base
import uuid
from datetime import datetime

class Defect(Base):
    __tablename__ = "defects"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    board_id = Column(UUID(as_uuid=True), ForeignKey("boards.id", ondelete="CASCADE"))
    defect_type = Column(String, nullable=False)
    confidence = Column(Float)
    position_from_start_mm = Column(Float)
    width_mm = Column(Float)
    bbox_px = Column(JSON)  # {x1,y1,x2,y2}
    frame_idx = Column(Integer)
    timestamp = Column(DateTime, default=datetime.utcnow)