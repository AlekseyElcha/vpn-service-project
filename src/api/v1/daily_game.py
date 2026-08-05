import time
from typing import Final

from fastapi import APIRouter, Depends, Query
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession
from starlette import status

from src.exceptions.db import DBCrudException
from src.repos.database.crud.game import get_previous_check_in_time_by_tg_id, \
    register_check_in_return_new_streak, reward_user_and_reset_streak, create_streak_one_for_user, \
    reset_streak_to_one, get_current_streak_count_by_tg_id
from src.repos.database.get_session import get_db_session


router = APIRouter(prefix="/game")

@router.get("/streak")
async def get_current_user_daily_streak(
        tg_id: int = Query(...),
        db_session: AsyncSession = Depends(get_db_session)
):
    current_streak = await get_current_streak_count_by_tg_id(
        tg_id=tg_id,
        session=db_session
    )

    if not current_streak:
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content={
                "success": False,
                "streak": None
            }
        )

    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content={
            "success": True,
            "streak": current_streak
        }
    )


@router.post("/check-in")
async def register_user_check_in(
        tg_id: int = Query(...),
        db_session: AsyncSession = Depends(get_db_session)
):
    ONE_DAY: Final = 86400

    previous_check_in = await get_previous_check_in_time_by_tg_id(
        tg_id=tg_id,
        session=db_session
    )

    current_time = int(time.time())

    if not previous_check_in:
        await create_streak_one_for_user(
            tg_id=tg_id,
            time_unix=current_time,
            session=db_session
        )
        return JSONResponse(
            status_code=status.HTTP_201_CREATED,
            content={
                "success": True,
                "msg": "Первый день засчитан, отличное начало! Награда впереди! Заходите в это меню завтра:)"
            }
        )

    prev_check_in_day = previous_check_in // ONE_DAY
    curr_check_in_day = current_time // ONE_DAY

    diff = curr_check_in_day - prev_check_in_day

    if diff == 0:
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "success": True,
                "msg": "Сегодня Вы уже отметились в этом меню, заходите завтра!"
            }
        )

    elif diff >= 2:
        await reset_streak_to_one(
            tg_id=tg_id,
            unix_time=current_time,
            session=db_session
        )
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "success": True,
                "msg": f"😢 Вы пропустили день, поэтому Ваш стрик сбросился до 1 дня. Может теперь получится?)"
            }
        )

    else:
        streak_count = await register_check_in_return_new_streak(
            tg_id=tg_id,
            check_in_time=current_time,
            session=db_session
        )

        if streak_count == 7:
            try:
                await reward_user_and_reset_streak(
                    tg_id=tg_id,
                    check_in_time=current_time,
                    session=db_session)
            except DBCrudException:
                return JSONResponse(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    content={
                        "success": False,
                        "msg": "Произошла ошибка:( Уже чиним!!!"
                    }
                )
            return JSONResponse(
                status_code=status.HTTP_200_OK,
                content={
                    "success": True,
                    "msg": "🎉 Получена награда за 7 дней!!! Поздравляем!!!"
                }
            )

        return JSONResponse(
                status_code=status.HTTP_200_OK,
                content={
                    "success": True,
                    "msg": f"👍 Отлично! Текущий стрик: {streak_count} из 7 дней! Ждём Вас завтра!"
                }
        )

