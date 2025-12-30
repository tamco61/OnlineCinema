from uuid import UUID

from fastapi import HTTPException, status, Depends
from sqlalchemy import and_, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import Favorite
from app.db.session import get_db


class FavoritesService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_user_favorites(
            self, profile_id: UUID, limit: int = 100
    ) -> list[Favorite]:
        result = await self.db.execute(
            select(Favorite)
            .where(Favorite.profile_id == profile_id)
            .order_by(Favorite.created_at.desc())
            .limit(limit)
        )
        return list(result.scalars().all())

    async def add_favorite(
            self, profile_id: UUID, content_id: UUID, content_type: str
    ) -> Favorite:
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

    async def remove_favorite(
            self, profile_id: UUID, content_id: UUID
    ) -> bool:
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

    async def is_favorite(
            self, profile_id: UUID, content_id: UUID
    ) -> bool:
        result = await self.db.execute(
            select(Favorite).where(
                and_(
                    Favorite.profile_id == profile_id,
                    Favorite.content_id == content_id,
                )
            )
        )
        return result.scalar_one_or_none() is not None


async def get_favorites_service(
        db: AsyncSession = Depends(get_db),
) -> FavoritesService:
    return FavoritesService(db)
