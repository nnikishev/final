# app/routers/lining_board.py
from typing import Any
from uuid import UUID
from fastapi import APIRouter, HTTPException, Depends

from app.lining_board.schemas import (
    DashboardMetricsDTO,
    FrontendBoardsResponseDTO,
    LiningBoardCreateDTO,
    LiningBoardDTO,
    LiningBoardUpdateDTO,
    StatusResponseDTO,
)
from app.lining_board.service import StatisticsServiceDep

router = APIRouter(
    prefix="/lining-board",
    tags=["lining-board"],
    responses={404: {"description": "Not found"}},
)

# старый эндпоинт / – возвращает список досок (простые dict) – оставим для обратной совместимости
@router.get("/")
async def get_list(
    service: StatisticsServiceDep,
    limit: int = 20,
    skip: int = 0,
    sort_field: str = "start_time",
) -> list[dict]:
    boards, _ = await service.board_repo.get_list(limit=limit, offset=skip, sort_field=sort_field)
    return [{"board_number": str(b.id), "start_time": b.start_time.isoformat()} for b in boards]

# основной эндпоинт для фронтенда
@router.get("/frontend/boards", response_model=FrontendBoardsResponseDTO)
async def get_frontend_boards(
    service: StatisticsServiceDep,
    search: str | None = None,
    quality: str | None = None,
    defect_type: str | None = None,
    sort_by: str = "date",
    sort_order: str = "desc",
    page: int = 1,
    limit: int = 20,
) -> dict[str, Any]:
    return await service.get_boards_for_frontend(
        search=search,
        quality=quality,
        defect_type=defect_type,
        sort_by=sort_by,
        sort_order=sort_order,
        page=page,
        limit=limit,
    )

@router.get("/frontend/metrics", response_model=DashboardMetricsDTO)
async def get_frontend_metrics(service: StatisticsServiceDep) -> dict[str, Any]:
    return await service.get_metrics_for_frontend()

@router.get("/{board_number}", response_model=LiningBoardDTO)  # board_number здесь – это UUID строкой
async def get_one(service: StatisticsServiceDep, board_number: str) -> dict[str, Any]:
    try:
        board = await service.get_one_board(UUID(board_number))
        return {
            "board_number": str(board.id),  # поле board_number в DTO – число, но в старой схеме это int? Придётся конвертировать
            "start_time": board.start_time.time(),
            "end_time": board.end_time.time() if board.end_time else None,
            "defect_counts": board.defects_summary,
            "total_defects": sum(board.defects_summary.values()) if board.defects_summary else 0,
            "quality": board.quality or "C",
            "defect_photos": [],  # у нас нет фото в этой таблице, можно вернуть пустой список
        }
    except RuntimeError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
