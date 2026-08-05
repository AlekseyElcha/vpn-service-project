from sqlalchemy import select, update
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from src.config.settings import settings
from src.exceptions.db import DBCrudException
from src.repos.database.models import DailyGameStreakModel, UserModel


async def get_current_streak_count_by_tg_id(
        tg_id: int,
        session: AsyncSession
) -> int | None:
    query = (select(DailyGameStreakModel.streak_count)
             .where(DailyGameStreakModel.tg_id == tg_id))
    try:
        data = await session.execute(query)
        result = data.scalars().first()
        if result:
            return result
        else:
            return None
    except SQLAlchemyError:
        raise DBCrudException


async def get_previous_check_in_time_by_tg_id(
        tg_id: int,
        session: AsyncSession
) -> int | None:
    query = (select(DailyGameStreakModel.last_checked_in)
             .where(DailyGameStreakModel.tg_id == tg_id))
    try:
        data = await session.execute(query)
        result = data.scalars().first()
        if result:
            return result
        else:
            return None
    except SQLAlchemyError:
        raise DBCrudException



async def register_check_in_return_new_streak(
        check_in_time: int,
        tg_id: int,
        session: AsyncSession
) -> int | None:
    query = (
        update(DailyGameStreakModel)
        .where(DailyGameStreakModel.tg_id == tg_id)
        .values(
            streak_count=DailyGameStreakModel.streak_count + 1,
            last_checked_in=check_in_time
        )
        .returning(DailyGameStreakModel.streak_count)
    )
    try:
        result = await session.execute(query)
        new_streak = result.scalar_one_or_none()
        await session.commit()
        if new_streak:
            return new_streak
        else:
            return 1
    except SQLAlchemyError:
        raise DBCrudException


async def reward_user_and_reset_streak(
        tg_id: int,
        check_in_time: int,
        session: AsyncSession
):
    reward = settings.game.reward

    query_reward = (update(UserModel)
             .where(UserModel.tg_id == tg_id)
             .values(balance=UserModel.balance+reward)
    )
    query_reset_streak = (update(DailyGameStreakModel)
                    .where(DailyGameStreakModel.tg_id == tg_id)
                    .values(
                        streak_count=1,
                        last_checked_in=check_in_time
                    )
    )
    try:
        await session.execute(query_reward)
        await session.execute(query_reset_streak)
        await session.commit()
    except SQLAlchemyError:
        await session.rollback()
        raise DBCrudException


async def create_streak_one_for_user(
        tg_id: int,
        time_unix: int,
        session: AsyncSession
):
    new_streak = DailyGameStreakModel(
        tg_id=tg_id,
        last_checked_in=time_unix,
        streak_count=1
    )
    session.add(new_streak)
    try:
        await session.commit()
        await session.refresh(new_streak)
    except SQLAlchemyError:
        await session.rollback()
        raise DBCrudException


async def reset_streak_to_one(
        tg_id: int,
        unix_time: int,
        session: AsyncSession
):
    query = (update(DailyGameStreakModel)
                    .where(DailyGameStreakModel.tg_id == tg_id)
                    .values(
                        streak_count=1,
                        last_checked_in=unix_time
                    )
    )
    try:
        await session.execute(query)
        await session.commit()
    except SQLAlchemyError:
        await session.rollback()
        raise DBCrudException

