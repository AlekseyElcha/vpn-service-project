import time

from sqlalchemy import select, update, exists
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from src.exceptions.promo import PromoAlreadyUsedException, PromoExpiredException
from src.repos.database.models import PromoCodeModel, PromoActivationRecordModel, UserModel
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
    # try:
    data = await session.execute(query)
    result = data.scalar_one_or_none()
    print(result)
    if result:
        return result
    else:
        raise NotFoundException
    # except SQLAlchemyError:
    #     raise DBCrudException


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



async def activate_promo(
        promo: PromoCodeModel,
        record: PromoCodeActivationRecordSchema,
        session: AsyncSession
):
    query_select = (
        select(PromoCodeModel)
        .where(PromoCodeModel.code == promo.code)
        .with_for_update()
    )

    activation_record = PromoActivationRecordModel(**record.model_dump())

    query_update_balance = (
        update(UserModel)
        .where(UserModel.tg_id == record.tg_id)
        .values(balance=UserModel.balance + promo.bonus_amount)
    )

    query_check_promo_already_used = select(
        exists().where(
            PromoActivationRecordModel.tg_id == record.tg_id,
            PromoActivationRecordModel.promo_id == promo.id
        )
    )

    query_update_activations_left_counter = (
        update(PromoCodeModel)
        .where(PromoCodeModel.code == promo.code)
        .values(activations_count = PromoCodeModel.activations_count + 1)
    )

    try:
        result = await session.execute(query_select)
        promo_info = result.scalar_one_or_none()

        if not promo_info:
            raise NotFoundException

        already_used = await session.scalar(query_check_promo_already_used)
        if already_used:
            raise PromoAlreadyUsedException

        current_time = int(time.time())

        if promo_info.expiry_time and promo_info.expiry_time <= current_time:
            raise PromoExpiredException

        await session.execute(query_update_balance)
        await session.execute(query_update_activations_left_counter)
        session.add(activation_record)
        await session.commit()
    except SQLAlchemyError:
        await session.rollback()
        raise DBCrudException

