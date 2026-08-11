from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker

from src.config.settings import settings

engine = create_async_engine(
    url=settings.db.pg_async_url,
    pool_size=settings.db.pool_size,
    max_overflow=settings.db.max_overflow,
    pool_pre_ping=True
)

async_session_maker = async_sessionmaker(
    bind=engine,
    expire_on_commit=False,
)