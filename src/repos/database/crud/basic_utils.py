import uuid
from typing import List

from sqlalchemy import select, ScalarResult
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from src.repos.database.models import ClientModel
from src.exceptions.db import DBCrudException
from src.repos.database.models import UserModel


async def user_existence_by_tg_id(
        tg_id: int,
        session: AsyncSession
) -> bool:
    query = select(UserModel).where(UserModel.tg_id == tg_id)
    try:
        result = await session.execute(query)
        return True if result.scalar_one_or_none() is not None else False
    except SQLAlchemyError as e:
        raise DBCrudException from e


async def get_user_balance_by_tg_id(
        tg_id: int,
        session: AsyncSession
) -> int:
    query = select(UserModel.balance).where(UserModel.tg_id == tg_id)
    try:
        data = await session.execute(query)
        res = data.scalar_one_or_none()
        if res:
            return res
        else:
            return 0
    except SQLAlchemyError as e:
        raise DBCrudException from e


async def get_user_clients(
        tg_id: int,
        session: AsyncSession
) -> List[uuid.UUID] | None:
    query = select(ClientModel.id).where(ClientModel.tg_id == tg_id)
    try:
        data = await session.execute(query)
        res = data.scalars()
        if not res:
            return None
        return list(res)
    except:
        raise DBCrudException


async def get_all_users_tg_ids_from_db(
        session: AsyncSession
):
    query = select(UserModel.tg_id)
    try:
        data = await session.execute(query)
        result = data.scalars().all()
        return list(result)
    except SQLAlchemyError as e:
        await session.rollback()
        raise DBCrudException
