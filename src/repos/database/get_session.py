from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession

from src.repos.database.session_factory import async_session_maker


async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    async with async_session_maker() as session:
        yield session
