from collections.abc import AsyncIterator
from functools import lru_cache

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

from .config import get_settings


class Base(DeclarativeBase):
    """Metadata for tables this service owns (none yet). Alembic migrates exactly
    these; Django's tables are read through their API, never mapped here."""


@lru_cache
def get_sessionmaker() -> async_sessionmaker[AsyncSession]:
    engine = create_async_engine(get_settings().async_database_url, pool_pre_ping=True)
    return async_sessionmaker(engine, expire_on_commit=False)


async def get_db() -> AsyncIterator[AsyncSession]:
    async with get_sessionmaker()() as session:
        yield session


async def dispose_engine() -> None:
    if get_sessionmaker.cache_info().currsize:
        await get_sessionmaker().kw["bind"].dispose()
