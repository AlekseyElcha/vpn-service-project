from sqlalchemy import update
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from src.exceptions.db import DBCrudException
from src.repos.database.models import UserModel


async def update_balance(
        user_tg_id: int,
        stars_amount: int | float,
        session: AsyncSession
) -> None:
    query = (update(UserModel)
             .where(UserModel.tg_id == user_tg_id)
             .values(balance=UserModel.balance + stars_amount)
    )
    try:
        result = await session.execute(query)
        if result.rowcount == 0:
            raise DBCrudException(f"User with tg_id={user_tg_id} not found for balance update")
        await session.flush()
    except SQLAlchemyError:
        await session.rollback()
        raise DBCrudException


async def update_balance_outside_payment(
        user_tg_id: int,
        stars_amount: int | float,
        session: AsyncSession
) -> None:
    query = (update(UserModel)
             .where(UserModel.tg_id == user_tg_id)
             .values(balance=UserModel.balance + stars_amount)
    )
    try:
        result = await session.execute(query)
        if result.rowcount == 0:
            raise DBCrudException(f"User with tg_id={user_tg_id} not found for balance update")
        await session.commit()
        await session.flush()
    except SQLAlchemyError:
        await session.rollback()
        raise DBCrudException
