from collections.abc import AsyncGenerator
from typing import Optional

from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import declarative_base

from services.catalog.app.core.config import settings  # noqa

engine: Optional[AsyncEngine] = None
async_session_maker: Optional[async_sessionmaker[AsyncSession]] = None
Base = declarative_base()


def get_engine() -> AsyncEngine:
    global engine

    if engine is None:
        engine = create_async_engine(
            settings.database_url,
            echo=settings.is_development,
            pool_size=10,
            max_overflow=20,
            pool_pre_ping=True,
            pool_recycle=3600
        )

    return engine


def get_session_maker() -> async_sessionmaker[AsyncSession]:
    global async_session_maker

    if async_session_maker is None:
        async_session_maker = async_sessionmaker(
            bind=get_engine(),
            class_=AsyncSession,
            expire_on_commit=False,
            autocommit=False,
            autoflush=False,
        )

    return async_session_maker


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    session_maker = get_session_maker()

    async with session_maker() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def init_db() -> None:
    engine = get_engine()

    async with engine.begin() as conn:
        from app.db import models  # noqa

        await conn.run_sync(Base.metadata.create_all)


async def close_db() -> None:
    global engine

    if engine is not None:
        await engine.dispose()
        engine = None
