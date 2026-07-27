from sqlalchemy.ext.asyncio import AsyncSession

from src.exceptions.actions import DBActionException
from src.dtos.schemas import PromoCodeSchema
from src.exceptions.db import DBCrudException
from src.repos.database.crud.promo import add_new_promo_code_to_db


async def create_new_promo(
        new_promo: PromoCodeSchema,
        db_session: AsyncSession
):
    try:
        await add_new_promo_code_to_db(
            code=new_promo,
            session=db_session
        )
    except DBCrudException:
        raise DBActionException
