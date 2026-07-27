import time
from typing import Dict, Any

from sqlalchemy.ext.asyncio import AsyncSession

from src.exceptions.db import DBCrudException, NotFoundException
from src.repos.database.crud.promo import get_promo_code_info_from_db


async def get_promo_info(
        code: str,
        session: AsyncSession
) -> Dict[str, Any] | None:
    try:
        promo_info = await get_promo_code_info_from_db(
            code=code,
            session=session
        )
        current_time = time.time()
        result = {}
        if promo_info.expiry_time and promo_info.expiry_time > current_time:
            result["bonus_amount"] = promo_info.bonus_amount
            result["id"] = promo_info.id
            return result
        else:
            return None
    except DBCrudException:
        return None
    except NotFoundException:
        raise NotFoundException