import time
from uuid import UUID

from fastapi import HTTPException, status, Depends
from sqlalchemy import and_, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from services.user.app.db.models import Favorite
from services.user.app.db.session import get_db

from shared.utils.telemetry.metrics import counter, histogram
from shared.utils.telemetry.tracer import trace_span


class FavoritesService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_user_favorites(
            self, profile_id: UUID, limit: int = 100
    ) -> list[Favorite]:
        async with trace_span("favorites_get_user_favorites"):
            start = time.time()
            counter("clickhouse_queries_total").add(1)

            try:
                result = await self.db.execute(
                    select(Favorite)
                    .where(Favorite.profile_id == profile_id)
                    .order_by(Favorite.created_at.desc())
                    .limit(limit)
                )
                return list(result.scalars().all())
            except Exception as e:
                counter("clickhouse_query_errors_total").add(1)
                raise
            finally:
                histogram("clickhouse_query_duration_seconds").record(time.time() - start)

    async def add_favorite(
            self, profile_id: UUID, content_id: UUID, content_type: str
    ) -> Favorite:
        async with trace_span("favorites_add_favorite"):
            start = time.time()
            counter("clickhouse_queries_total").add(1)

            try:
                existing = await self.is_favorite(profile_id, content_id)
                if existing:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="Already in favorites",
                    )

                favorite = Favorite(
                    profile_id=profile_id,
                    content_id=content_id,
                    content_type=content_type,
                )

                self.db.add(favorite)
                try:
                    await self.db.commit()
                    await self.db.refresh(favorite)
                except IntegrityError:
                    await self.db.rollback()
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="Already in favorites",
                    )

                return favorite
            except Exception as e:
                counter("clickhouse_query_errors_total").add(1)
                raise
            finally:
                histogram("clickhouse_query_duration_seconds").record(time.time() - start)

    async def remove_favorite(
            self, profile_id: UUID, content_id: UUID
    ) -> bool:
        async with trace_span("favorites_remove_favorite"):
            start = time.time()
            counter("clickhouse_queries_total").add(1)

            try:
                result = await self.db.execute(
                    select(Favorite).where(
                        and_(
                            Favorite.profile_id == profile_id,
                            Favorite.content_id == content_id,
                        )
                    )
                )
                favorite = result.scalar_one_or_none()

                if not favorite:
                    raise HTTPException(
                        status_code=status.HTTP_404_NOT_FOUND,
                        detail="Favorite not found",
                    )

                await self.db.delete(favorite)
                await self.db.commit()
                return True
            except Exception as e:
                counter("clickhouse_query_errors_total").add(1)
                await self.db.rollback()
                raise
            finally:
                histogram("clickhouse_query_duration_seconds").record(time.time() - start)

    async def is_favorite(
            self, profile_id: UUID, content_id: UUID
    ) -> bool:
        async with trace_span("favorites_is_favorite"):
            start = time.time()
            counter("clickhouse_queries_total").add(1)

            try:
                result = await self.db.execute(
                    select(Favorite).where(
                        and_(
                            Favorite.profile_id == profile_id,
                            Favorite.content_id == content_id,
                        )
                    )
                )
                return result.scalar_one_or_none() is not None
            except Exception as e:
                counter("clickhouse_query_errors_total").add(1)
                raise
            finally:
                histogram("clickhouse_query_duration_seconds").record(time.time() - start)


async def get_favorites_service(
        db: AsyncSession = Depends(get_db),
) -> FavoritesService:
    return FavoritesService(db)
