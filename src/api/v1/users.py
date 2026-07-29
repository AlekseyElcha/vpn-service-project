from fastapi import APIRouter, Depends, Query, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.responses import JSONResponse

from src.core.utils import create_referral_code
from src.backend_logging import logger
from src.dtos.schemas import NewUserSchema
from src.repos.database.crud.creation import add_new_user_to_db
from src.core.clients.client_info import get_subscriptions_by_tg_id
from src.exceptions.db import DBCrudException
from src.repos.database.crud.basic_utils import get_user_balance_by_tg_id, user_existence_by_tg_id
from src.repos.database.get_session import get_db_session

router = APIRouter(prefix="/users", tags=["Users"])


@router.get("/balance")
async def get_user_balance(
        tg_id: int = Query(...),
        db_session: AsyncSession = Depends(get_db_session)
) -> JSONResponse:
    logger.info("GET /balance request, tg_id: {}".format(tg_id))

    try:
        user_balance = await get_user_balance_by_tg_id(
            tg_id=tg_id,
            session=db_session
        )
        logger.debug("Fetched user balance: tg_id=%s, balance=%s", tg_id, user_balance)
        logger.info("GET /balance request, tg_id: {} -> 200 OK".format(tg_id))

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "msg": "success",
                "balance": user_balance
            }
        )

    except DBCrudException as e:
        logger.debug("Error getting user balance: {}".format(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Произошла ошибка сервера."
        )



@router.get("/subs")
async def get_user_subscriptions(
        tg_id: int = Query(...),
        db_session: AsyncSession = Depends(get_db_session)
):
    logger.info("GET /subs request, tg_id: {}".format(tg_id))

    try:
        results = await get_subscriptions_by_tg_id(
            tg_id=tg_id,
            session=db_session
        )
        logger.debug("Fetched user subscriptions: tg_id=%s, results=%s", tg_id, results)

        logger.info("GET /subs request, tg_id: {} -> 200 OK".format(tg_id))
        return results
    except DBCrudException as e:
        logger.error("Error getting user subs by tg_id=%s, error: e", tg_id, e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Внутренняя ошибка сервера."
        )


@router.post("/add")
async def create_new_user(
        new_user: NewUserSchema,
        db_session: AsyncSession = Depends(get_db_session)
) -> JSONResponse:
    logger.info("POST /add request, new_user: {}".format(new_user))
    if new_user.ref_code is None or new_user.ref_code == "":
        new_user.ref_code = create_referral_code()
    try:
        user_exists = await user_existence_by_tg_id(
                tg_id=int(new_user.tg_id),
                session=db_session
            )
        if user_exists:
            logger.debug("POST /add request, new_user: {} -> 201 OK".format(new_user))
            return JSONResponse(
                status_code=status.HTTP_200_OK,
                content={
                    "success": True,
                    "msg": "user already exists"
                }
            )
    except DBCrudException as e:
        logger.error("Error checking user existence: tg_id=%s, error: %s", new_user.tg_id, e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Произошла ошибка сервера."
        )

    try:
        await add_new_user_to_db(
            new_user=new_user,
            session=db_session
        )
        logger.debug("POST /add request, new_user: {} -> 200 OK".format(new_user))
        return JSONResponse(
            status_code=status.HTTP_201_CREATED,
            content={
                "success": True,
                "msg": "user created"
            }
        )

    except DBCrudException as e:
        logger.error("Error adding new user to db, new_user: %s, error: %s".format(new_user), e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Не удалось создать пользователя"
        )

