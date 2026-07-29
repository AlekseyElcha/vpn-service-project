import time

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi.responses import JSONResponse

from src.core.promo.validate_promo import check_promo_already_used
from src.exceptions.actions import DBActionException
from src.dtos.schemas import PromoCodeActivationRecordSchema
from src.repos.database.crud.promo import add_promo_activation_record_to_db, activate_promo
from src.core.promo.validate_promo import get_promo_info
from src.exceptions.db import DBCrudException, NotFoundException
from src.payments.balance import update_balance_outside_payment
from src.core.promo.create_promo import create_new_promo
from src.dtos.schemas import PromoCodeSchema
from src.repos.database.get_session import get_db_session


router = APIRouter(prefix="/promo", tags=["Promo"])


@router.post("/create")
async def create_promo_code(
        code: PromoCodeSchema,
        db_session: AsyncSession = Depends(get_db_session)
) -> JSONResponse:
    try:
        await create_new_promo(
            new_promo=code,
            db_session=db_session
            )
    except DBActionException:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Не удалось создать новый промо."
        )
    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content={
            "success": True,
            "msg": "Промокод успешно создан!"
        }
    )


@router.get("/activate")
async def activate_promo_code(
        code: str = Query(...),
        tg_id: int = Query(...),
        db_session: AsyncSession = Depends(get_db_session)
) -> JSONResponse:
    try:
        promo_info = await get_promo_info(
            code=code,
            session=db_session
        )
    except DBCrudException:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Произошла ошибка сервера."
        )
    # except NotFoundException:
    #     return JSONResponse(
    #         status_code=status.HTTP_404_NOT_FOUND,
    #         content={
    #             "success": False,
    #             "msg": "Промокод не найден."
    #         }
    #     )
    #
    # if not promo_info:
    #     return JSONResponse(
    #         status_code=status.HTTP_400_BAD_REQUEST,
    #         content={
    #             "success": False,
    #             "msg": "Промокод не найден."
    #         }
    #     )
    #
    # current_time = int(time.time())
    #
    # if not promo_info.expiry_time or not promo_info.id:
    #     return JSONResponse(
    #         status_code=status.HTTP_400_BAD_REQUEST,
    #         content={
    #             "success": False,
    #             "msg": "Ошибка при получении данных о промокоде."
    #         }
    #     )
    #
    # promo_expiration_time = int(promo_info.expiry_time)
    #
    # promo_already_used = await check_promo_already_used(
    #     promo_id=promo_info.id,
    #     tg_id=tg_id,
    #     db_session=db_session
    # )
    #
    # if current_time > promo_expiration_time or promo_info.activations == 0:
    #     return JSONResponse(
    #         status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
    #         content={
    #             "success": False,
    #             "msg": "Промокод недействителен."
    #         }
    #     )
    #
    # if promo_already_used:
    #     return JSONResponse(
    #         status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
    #         content={
    #             "success": False,
    #             "msg": "Промокод уже был использован."
    #         }
    #     )

    try:
        await activate_promo(
            promo=promo_info,
            record=PromoCodeActivationRecordSchema(
                tg_id=tg_id,
                promo_id=promo_info.id
            ),
            session=db_session
        )
    except NotFoundException:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Не найдено"
        )

    except NotFoundException:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Не найдено"
        )




        NotFoundException
        PromoAlreadyUsedException
        PromoExpiredException
        DBCrudException
    # await update_balance_outside_payment(
    #     user_tg_id=tg_id,
    #     stars_amount=int(promo_info.bonus_amount),
    #     session=db_session
    # )
    #
    # try:
    #     await add_promo_activation_record_to_db(
    #         record=PromoCodeActivationRecordSchema(
    #             tg_id=tg_id,
    #             promo_id=promo_info.id
    #         ),
    #         session=db_session
    #     )
    # except DBCrudException:
    #     raise HTTPException(
    #         status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
    #         detail="Произошла ошибка сервера."
    #     )

    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content={
            "success": True,
            "msg": f"На аккаунт начислено {promo_info.bonus_amount}"
        }
    )
