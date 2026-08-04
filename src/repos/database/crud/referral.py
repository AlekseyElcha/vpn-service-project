from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from src.dtos.schemas import ReferralActivationSchema
from src.exceptions.db import DBCrudException
from src.exceptions.db import NotFoundException
from src.repos.database.models import UserModel, ReferralModel


async def get_referral_code_for_user(
        tg_id: int,
        session: AsyncSession
):
    query = select(UserModel.ref_code).where(UserModel.tg_id == tg_id)
    try:
        data = await session.execute(query)
        result = data.scalar_one_or_none()
        await session.flush()
        if result:
            return result
        else:
            raise NotFoundException
    except SQLAlchemyError:
        raise DBCrudException


async def add_referral_record_to_db(
        referral: ReferralActivationSchema,
        session: AsyncSession
):
    new_referral = ReferralModel(**referral.model_dump(exclude={"referral_code"}))
    session.add(new_referral)
    # try:
    #     await session.commit()
    #     await session.refresh(new_referral)
    # except SQLAlchemyError:
    #     await session.rollback()
    #     raise DBCrudException
