from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.cut_plan import CutPlan
from app.schemas.cut_plan import CutPlanOut
from app.core.database import get_db

router = APIRouter(prefix="/cut_plans", tags=["Cut Plans"])

@router.get("/board/{board_id}", response_model=CutPlanOut)
async def get_cut_plan_by_board(board_id: str, db: AsyncSession = Depends(get_db)):
    from uuid import UUID
    result = await db.execute(select(CutPlan).where(CutPlan.board_id == UUID(board_id)))
    plan = result.scalar_one_or_none()
    if not plan:
        raise HTTPException(status_code=404, detail="Cut plan not found for this board")
    return plan