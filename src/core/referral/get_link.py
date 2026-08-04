from sqlalchemy.ext.asyncio import AsyncSession

from src.config.settings import settings
from src.exceptions.actions import NotFoundExceptionAction, DBActionException
from src.exceptions.db import NotFoundException, DBCrudException
from src.repos.database.crud.referral import get_referral_code_for_user

bot_name = settings.bot.name

async def get_referral_link_for_tg_user(
        tg_id: int,
        db_session: AsyncSession
) -> str:
    try:
        ref_code = await get_referral_code_for_user(
            tg_id=tg_id,
            session=db_session
        )
    except NotFoundException:
        raise NotFoundExceptionAction
    except DBCrudException:
        raise DBActionException

    ref_link = f"https://t.me/{bot_name}?start={ref_code}"

    return ref_link
