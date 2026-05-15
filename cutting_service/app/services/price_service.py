from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.price_list import PriceList
from app.schemas.price_list import PriceItem

class PriceService:
    def __init__(self, db_session: AsyncSession):
        self.db = db_session

    async def get_all_prices(self) -> list[PriceItem]:
        result = await self.db.execute(select(PriceList))
        rows = result.scalars().all()
        return [PriceItem(length_m=r.length_m, grade=r.grade, price=r.price) for r in rows]

    async def update_prices(self, items: list[PriceItem]):
        # Очистим таблицу и загрузим новые
        await self.db.execute(PriceList.__table__.delete())
        for item in items:
            self.db.add(PriceList(length_m=item.length_m, grade=item.grade, price=item.price))
        await self.db.commit()