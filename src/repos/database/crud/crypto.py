from sqlalchemy import update, select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from src.exceptions.db import DBCrudException
from src.repos.database.models import LocalCurrenciesModel


async def update_crypto_ratio(
        crypto_code: str,
        new_ratio: int | float,
        session: AsyncSession,
) -> None:
    query = (update(LocalCurrenciesModel)
             .where(LocalCurrenciesModel.currency_code == crypto_code)
             .values(exchange_rate=new_ratio)
    )
    try:
        await session.execute(query)
        await session.commit()
    except SQLAlchemyError:
        await session.rollback()
        raise DBCrudException


async def create_new_crypto_ratio(
        crypto_code: str,
        currency_cmd_id: int,
        ratio: int | float,
        session: AsyncSession,
) -> None:
    new_ratio = LocalCurrenciesModel(
        currency_code=crypto_code,
        currency_cmd_id=currency_cmd_id,
        exchange_rate=ratio
    )
    session.add(new_ratio)
    try:
        await session.commit()
        await session.refresh(new_ratio)
    except SQLAlchemyError:
        await session.rollback()
        raise DBCrudException



async def crypto_ratio_exists_in_db(
        crypto_code: str,
        session: AsyncSession
) -> bool:
    query = select(LocalCurrenciesModel).where(LocalCurrenciesModel.currency_code == crypto_code)
    try:
        data = await session.execute(query)
        result = data.scalar_one_or_none()
        if result:
            return True
        return False
    except SQLAlchemyError:
        raise DBCrudException
