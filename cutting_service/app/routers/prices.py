from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.services.price_service import PriceService
from app.schemas.price_list import PriceListUpdate, PriceItem

router = APIRouter(prefix="/prices", tags=["Prices"])

@router.get("/")
async def get_prices(db: AsyncSession = Depends(get_db)):
    service = PriceService(db)
    items = await service.get_all_prices()
    return {"items": items}

@router.post("/")
async def update_prices(data: PriceListUpdate, db: AsyncSession = Depends(get_db)):
    service = PriceService(db)
    await service.update_prices(data.items)
    return {"status": "updated"}