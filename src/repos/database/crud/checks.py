from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from src.exceptions.db import DBCrudException
from src.repos.database.models import PromoActivationRecordModel, ClientModel


async def check_promo_already_used_by_tg_id_and_promo_id(
        tg_id: int,
        promo_id: str,
        session: AsyncSession
) -> bool:
    query = (select(PromoActivationRecordModel)
             .where(PromoActivationRecordModel.promo_id == promo_id)
             .where(PromoActivationRecordModel.tg_id == tg_id)
             )
    try:
        data = await session.execute(query)
        result = data.scalars().all()
        if result:
            return True
        else:
            return False
    except SQLAlchemyError:
        raise DBCrudException


async def check_user_already_has_subscription(
        tg_id: int,
        session: AsyncSession
) -> bool:
    query = select(ClientModel).where(ClientModel.tg_id == tg_id)
    try:
        data = await session.execute(query)
        result = data.scalars().all()
        if result:
            return True
        return False
    except SQLAlchemyError:
        raise DBCrudException
