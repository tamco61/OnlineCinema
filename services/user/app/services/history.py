from uuid import UUID
from datetime import datetime

from sqlalchemy import and_, desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import UserProfile, WatchHistory
from app.schemas.history import WatchHistoryUpdate
from app.db.session import get_db
from fastapi import Depends

class HistoryService:

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_user_history(
        self, profile_id: UUID, limit: int = 50
    ) -> list[WatchHistory]:
        result = await self.db.execute(
            select(WatchHistory)
            .where(WatchHistory.profile_id == profile_id)
            .order_by(desc(WatchHistory.last_watched_at))
            .limit(limit)
        )
        return list(result.scalars().all())

    async def update_progress(
        self, profile_id: UUID, data: WatchHistoryUpdate
    ) -> WatchHistory:
        result = await self.db.execute(
            select(WatchHistory).where(
                and_(
                    WatchHistory.profile_id == profile_id,
                    WatchHistory.content_id == data.content_id,
                )
            )
        )
        history = result.scalar_one_or_none()

        if history:
            history.progress_seconds = data.progress_seconds
            history.duration_seconds = data.duration_seconds
            history.completed = data.completed
            history.last_watched_at = datetime.utcnow()
        else:
            history = WatchHistory(
                profile_id=profile_id,
                content_id=data.content_id,
                content_type=data.content_type,
                progress_seconds=data.progress_seconds,
                duration_seconds=data.duration_seconds,
                completed=data.completed,
                last_watched_at=datetime.utcnow(),
            )
            self.db.add(history)

        await self.db.commit()
        await self.db.refresh(history)
        return history

    async def get_content_progress(
        self, profile_id: UUID, content_id: UUID
    ) -> WatchHistory | None:
        result = await self.db.execute(
            select(WatchHistory).where(
                and_(
                    WatchHistory.profile_id == profile_id,
                    WatchHistory.content_id == content_id,
                )
            )
        )
        return result.scalar_one_or_none()


async def get_history_service(db: AsyncSession=Depends(get_db)) -> HistoryService:
    return HistoryService(db)