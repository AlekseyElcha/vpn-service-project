import time
from typing import Dict, Any

from sqlalchemy.ext.asyncio import AsyncSession

from src.repos.database.models import PromoCodeModel
from src.exceptions.actions import DBActionException
from src.repos.database.crud.checks import check_promo_already_used_by_tg_id_and_promo_id
from src.exceptions.db import DBCrudException, NotFoundException
from src.repos.database.crud.promo import get_promo_code_info_from_db


async def get_promo_info(
        code: str,
        session: AsyncSession
) -> PromoCodeModel | None:
    try:
        promo_info = await get_promo_code_info_from_db(
            code=code,
            session=session
        )
        return promo_info
    except DBCrudException:
        return None
    except NotFoundException:
        raise NotFoundException


async def check_promo_already_used(
        promo_id: str,
        tg_id: int,
        db_session: AsyncSession
) -> bool:
    try:
        promo_used = await check_promo_already_used_by_tg_id_and_promo_id(
            tg_id=tg_id,
            promo_id=promo_id,
            session=db_session
        )
        return promo_used
    except DBCrudException:
        raise DBActionException
