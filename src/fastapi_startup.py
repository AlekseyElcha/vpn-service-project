from dotenv import load_dotenv

from src.repos.database.models import Base
from src.repos.database.session_factory import engine

load_dotenv()
async def start():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    await engine.dispose()
