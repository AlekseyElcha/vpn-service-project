from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from src.repos.database.models import PromoCodeModel, PromoActivationRecordModel
from src.dtos.schemas import PromoCodeSchema, PromoCodeActivationRecordSchema
from src.exceptions.db import DBCrudException, NotFoundException


async def add_new_promo_code_to_db(
        code: PromoCodeSchema,
        session: AsyncSession
) -> None:
    new_code_orm = PromoCodeModel(**code.model_dump())
    session.add(new_code_orm)
    try:
        await session.commit()
        await session.refresh(new_code_orm)
    except SQLAlchemyError:
        await session.rollback()
        raise DBCrudException


async def get_promo_code_info_from_db(
        code: str,
        session: AsyncSession
):
    query = select(PromoCodeModel).where(PromoCodeModel.code == code)
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


async def add_promo_activation_record_to_db(
        record: PromoCodeActivationRecordSchema,
        session: AsyncSession
):
    new_record = PromoActivationRecordModel(**record.model_dump())
    session.add(new_record)
    try:
        await session.commit()
        await session.refresh(new_record)
    except SQLAlchemyError:
        raise DBCrudException


