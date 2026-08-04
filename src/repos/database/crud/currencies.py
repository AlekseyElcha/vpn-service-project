import asyncio
from typing import Sequence

from sqlalchemy import select, Row
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from src.backend_logging import logger
from src.repos.database.models import LocalCurrenciesModel
from src.exceptions.db import NotFoundException, DBCrudException


async def get_currency_ratio_from_db(
        currency_code: str,
        session: AsyncSession
):
    query = select(LocalCurrenciesModel).where(LocalCurrenciesModel.currency_code == currency_code)
    try:
        data = await session.execute(query)
        result = data.scalar_one_or_none()
        if not result:
            raise NotFoundException
        return result.exchange_rate
    except SQLAlchemyError as e:
        logger.warning(e)
        raise DBCrudException


async def get_many_currency_ratios_from_db(
        currency_names: list[str],
        session: AsyncSession
):
    query = (select(LocalCurrenciesModel.currency_code, LocalCurrenciesModel.exchange_rate)
             .where(LocalCurrenciesModel.currency_code.in_(currency_names))
    )
    try:
        data = await session.execute(query)
        result = [row._asdict() for row in data.all()]
        return result
    except SQLAlchemyError:
        raise DBCrudException
