from sqlalchemy import update
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from src.exceptions.db import DBCrudException
from src.repos.database.models import ClientModel, UserModel


async def update_db_client_billing(
        tg_id: int,
        enable: bool,
        expiry_time: int,
        db_session: AsyncSession,
):
    query = (
        update(ClientModel)
        .where(ClientModel.tg_id==tg_id)
        .values(
            enable=enable,
            expiry_time=expiry_time
        )
    )
    try:
        await db_session.execute(query)
    except SQLAlchemyError:
        raise DBCrudException



async def update_user_balance_billing(
        tg_id: int,
        new_balance: int | float,
        db_session: AsyncSession,
):
    query = (
        update(UserModel)
        .where(UserModel.tg_id == tg_id)
        .values(
            balance=new_balance
        )
    )
    try:
        await db_session.execute(query)
    except SQLAlchemyError:
        raise DBCrudException
