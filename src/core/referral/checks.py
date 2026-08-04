from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from src.exceptions.db import DBCrudException
from src.repos.database.models import UserModel


async def get_user_referrer(
        tg_id: int,
        session: AsyncSession
) -> int | None:
    query = select(UserModel.referrer_id).where(UserModel.tg_id == tg_id)
    try:
        data = await session.execute(query)
        referrer_id = data.scalar_one_or_none()
        await session.flush()
        if referrer_id:
            return int(referrer_id)
        else:
            return None
    except SQLAlchemyError:
        raise DBCrudException
