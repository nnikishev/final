from typing import Optional, List, Dict, Any
from uuid import UUID
from sqlalchemy import select, func, and_, desc, asc
from sqlalchemy.ext.asyncio import AsyncSession
from app.lining_board.model import Board, Defect, CutPlan

class BoardRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_id(self, board_id: UUID) -> Optional[Board]:
        result = await self.session.execute(select(Board).where(Board.id == board_id))
        return result.scalar_one_or_none()

    async def get_list(
        self,
        limit: int = 20,
        offset: int = 0,
        sort_field: str = "start_time",
        sort_order: str = "desc",
        search: Optional[str] = None,
        quality: Optional[str] = None,
        defect_type: Optional[str] = None,
    ) -> tuple[List[Board], int]:
        query = select(Board)
        count_query = select(func.count()).select_from(Board)

        # фильтры
        if search:
            # поиск по id (как строке) – упрощённо
            query = query.where(Board.id.cast(String).ilike(f"%{search}%"))
            count_query = count_query.where(Board.id.cast(String).ilike(f"%{search}%"))
        if quality:
            query = query.where(Board.quality == quality)
            count_query = count_query.where(Board.quality == quality)
        if defect_type:
            # требуется подзапрос: доски, у которых есть хотя бы один дефект указанного типа
            subq = select(Defect.board_id).where(Defect.defect_type == defect_type).distinct()
            query = query.where(Board.id.in_(subq))
            count_query = count_query.where(Board.id.in_(subq))

        # сортировка
        sort_column = getattr(Board, sort_field, Board.start_time)
        if sort_order == "desc":
            query = query.order_by(desc(sort_column))
        else:
            query = query.order_by(asc(sort_column))

        query = query.offset(offset).limit(limit)
        result = await self.session.execute(query)
        boards = result.scalars().all()

        total_result = await self.session.execute(count_query)
        total = total_result.scalar()

        return boards, total

    async def get_defects_for_board(self, board_id: UUID) -> List[Defect]:
        result = await self.session.execute(select(Defect).where(Defect.board_id == board_id))
        return result.scalars().all()

    async def get_cut_plan_for_board(self, board_id: UUID) -> Optional[CutPlan]:
        result = await self.session.execute(select(CutPlan).where(CutPlan.board_id == board_id))
        return result.scalar_one_or_none()

    async def get_metrics(self) -> Dict[str, Any]:
        # общее количество досок
        total_boards_result = await self.session.execute(select(func.count()).select_from(Board))
        total_boards = total_boards_result.scalar() or 0

        # средняя длительность обработки (секунды) – считаем по разнице start_time и end_time
        # если end_time нет, не учитываем
        avg_duration_result = await self.session.execute(
            select(func.avg(func.extract('epoch', Board.end_time - Board.start_time)))
            .where(Board.end_time.isnot(None))
        )
        avg_duration = avg_duration_result.scalar() or 0.0

        # распределение по качеству
        quality_dist = await self.session.execute(
            select(Board.quality, func.count()).group_by(Board.quality)
        )
        quality_distribution = {row[0]: row[1] for row in quality_dist.all()}
        # гарантируем наличие всех классов
        for q in ["A", "B", "C", "D"]:
            quality_distribution.setdefault(q, 0)

        # общее количество дефектов
        total_defects_result = await self.session.execute(select(func.count()).select_from(Defect))
        total_defects = total_defects_result.scalar() or 0

        # топ-5 типов дефектов
        top_defects_result = await self.session.execute(
            select(Defect.defect_type, func.count())
            .group_by(Defect.defect_type)
            .order_by(func.count().desc())
            .limit(5)
        )
        top_defects = [{"type": row[0], "count": row[1]} for row in top_defects_result.all()]

        # количество досок по часам (за последние 24 часа)
        from datetime import datetime, timedelta
        day_ago = datetime.utcnow() - timedelta(days=1)
        boards_by_hour_result = await self.session.execute(
            select(
                func.date_trunc('hour', Board.start_time).label('hour'),
                func.count()
            )
            .where(Board.start_time >= day_ago)
            .group_by('hour')
            .order_by('hour')
        )
        boards_by_hour = [{"hour": row[0].isoformat(), "count": row[1]} for row in boards_by_hour_result.all()]

        return {
            "totalBoards": total_boards,
            "avgProcessingDuration": avg_duration,
            "qualityDistribution": quality_distribution,
            "totalDefects": total_defects,
            "topDefects": top_defects,
            "boardsByHour": boards_by_hour,
        }