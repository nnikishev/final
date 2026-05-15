from sqlalchemy import Column, String, Float, Integer, DateTime, ForeignKey, JSON
from sqlalchemy.dialects.postgresql import UUID
from app.models.board import Base
import uuid
from datetime import datetime

class CutPlan(Base):
    __tablename__ = "cut_plans"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    board_id = Column(UUID(as_uuid=True), ForeignKey("boards.id", ondelete="CASCADE"), unique=True)
    segments = Column(JSON)  # список отрезков: [{"from_mm":0, "to_mm":1000, "grade":0, "length_m":1.0, "price":150, "order_id":null}]
    total_revenue = Column(Float)
    algorithm = Column(String, default="greedy")
    created_at = Column(DateTime, default=datetime.utcnow)