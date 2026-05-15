from sqlalchemy import Column, Float, Integer, UniqueConstraint
from app.models.board import Base

class PriceList(Base):
    __tablename__ = "price_list"

    id = Column(Integer, primary_key=True, autoincrement=True)
    length_m = Column(Float, nullable=False)   # длина в метрах
    grade = Column(Integer, nullable=False)    # сорт 0..3
    price = Column(Float, nullable=False)      # цена за штуку (руб)

    __table_args__ = (UniqueConstraint('length_m', 'grade', name='unique_length_grade'),)