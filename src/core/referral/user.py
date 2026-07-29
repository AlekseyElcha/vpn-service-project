from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from src.exceptions.db import DBCrudException
from src.repos.database.models import UserModel


async def get_referrer_tg_id_by_code(
        ref_code: str,
        session: AsyncSession
) -> int | None:
    query = select(UserModel.tg_id).where(UserModel.ref_code == ref_code)
    try:
        data = await session.execute(query)
        result = data.scalar_one_or_none()
        await session.flush()
        if result:
            return result
        else:
            return None
    except SQLAlchemyError:
        raise DBCrudException
