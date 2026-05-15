import uuid
from datetime import datetime
from sqlalchemy import Integer, Column, String, Float, DateTime, JSON, ForeignKey, UUID as SQLUUID
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()

class Board(Base):
    __tablename__ = "boards"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    camera_id = Column(String, nullable=False)
    start_time = Column(DateTime, nullable=False)
    end_time = Column(DateTime, nullable=True)
    total_length_mm = Column(Float, nullable=True)
    defects_summary = Column(JSON, nullable=True)  # {"alive_knot":2, ...}
    quality = Column(String, nullable=True)  # A, B, C, D – добавляем, чтобы фронт мог показывать
    created_at = Column(DateTime, default=datetime.utcnow)

    # связи (опционально, для удобства в репозиториях)
    defects = relationship("Defect", back_populates="board", cascade="all, delete-orphan")
    cut_plan = relationship("CutPlan", back_populates="board", uselist=False, cascade="all, delete-orphan")


class Defect(Base):
    __tablename__ = "defects"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    board_id = Column(UUID(as_uuid=True), ForeignKey("boards.id", ondelete="CASCADE"))
    defect_type = Column(String, nullable=False)
    confidence = Column(Float)
    position_from_start_mm = Column(Float)
    width_mm = Column(Float)
    bbox_px = Column(JSON)  # {"x1":..., "y1":..., "x2":..., "y2":...}
    frame_idx = Column(Integer)
    timestamp = Column(DateTime, default=datetime.utcnow)

    board = relationship("Board", back_populates="defects")


class CutPlan(Base):
    __tablename__ = "cut_plans"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    board_id = Column(UUID(as_uuid=True), ForeignKey("boards.id", ondelete="CASCADE"), unique=True)
    segments = Column(JSON)  # список отрезков
    total_revenue = Column(Float)
    algorithm = Column(String, default="greedy")
    created_at = Column(DateTime, default=datetime.utcnow)

    board = relationship("Board", back_populates="cut_plan")