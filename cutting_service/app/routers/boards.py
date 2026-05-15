from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.board import Board
from app.schemas.board import BoardOut
from app.core.database import get_db

router = APIRouter(prefix="/boards", tags=["Boards"])

@router.get("/", response_model=list[BoardOut])
async def list_boards(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Board).order_by(Board.created_at.desc()))
    boards = result.scalars().all()
    return boards

@router.get("/{board_id}", response_model=BoardOut)
async def get_board(board_id: str, db: AsyncSession = Depends(get_db)):
    from uuid import UUID
    board = await db.get(Board, UUID(board_id))
    if not board:
        raise HTTPException(status_code=404, detail="Board not found")
    return board