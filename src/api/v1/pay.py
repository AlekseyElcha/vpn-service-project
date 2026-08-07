from contextlib import asynccontextmanager
from datetime import datetime
from typing import Dict, Any

from fastapi import APIRouter, Body

from src.backend_logging import logger
from src.core.clients.toggle_client import enable_and_prolong_client_by_user_tg_id
from src.core.referral.checks import get_user_referrer
from src.dtos.schemas import NewUserSchema, PaymentRecordSchema
from src.exceptions.db import DBCrudException
from src.payments.balance import update_balance
from src.repos.database.crud.basic_utils import user_existence_by_tg_id, get_user_balance_by_tg_id, \
    get_user_client_by_tg_id
from src.repos.database.crud.creation import add_new_user_to_db_without_commit
from src.repos.database.crud.payments import add_payment_record_to_db
from src.repos.database.get_session import get_db_session
from src.utils.validate_stars_payment import validate_stars_payment_return_rub_price

router = APIRouter(prefix="/payment", tags=["Payment"])


@router.post("/pay")
async def process_successful_payment(user_id: int = Body(embed=True),
                              payment_amount: int | float = Body(embed=True),
                              item_id: str = Body(embed=True),
                              payment_type: str = Body(embed=True),
) -> Dict[str, Any]:
    logger.info("POST /pay request -> user id=%s, payment_amount=%s, item_id=%s", user_id, payment_amount, item_id)

    try:
        month_count = int(item_id.split()[0])
    except ValueError:
        month_count = 1
        logger.warning("Got unexpected item_id=%s", item_id)


    if payment_type == "Stars":
        payment_amount = validate_stars_payment_return_rub_price(
            month_count=month_count
        )

    async with asynccontextmanager(get_db_session)() as db_session:
        try:
            user_exists = await user_existence_by_tg_id(
                tg_id=int(user_id),
                session=db_session
            )
            logger.debug("Checked user existence by tg_id=%s, result: %s", int(user_id), user_exists)

            if not user_exists:
                await add_new_user_to_db_without_commit(
                    new_user=NewUserSchema(
                        tg_id=int(user_id),
                        balance=0
                    ),
                    session=db_session
                )
                logger.debug("Created db user tg=%s", int(user_id))
            else:
                old_balance = await get_user_balance_by_tg_id(
                    tg_id=int(user_id),
                    session=db_session
                )
                logger.debug("Fetched old user balance: user %s, balance %s", int(user_id), old_balance)

            time_now = int(datetime.now().timestamp())
            await add_payment_record_to_db(
                new_record=PaymentRecordSchema(
                    tg_id=int(user_id),
                    item_id=item_id,
                    time=time_now,
                    amount=payment_amount,
                    payment_type=payment_type,
                ),
                session=db_session,
            )
            logger.debug("Added payment record to db: tg_id=%s, item_id=%s, time=%s, amount=%s",
                         int(user_id), item_id, time_now, payment_amount)

            await update_balance(
                user_tg_id=int(user_id),
                amount=payment_amount,
                session=db_session,
            )

            logger.debug("Updated user balance: tg_id=%s", int(user_id))

            # user_clients = await get_user_clients(
            #     tg_id=int(user_id),
            #     session=db_session
            # )
            try:
                user_client = await get_user_client_by_tg_id(
                    tg_id=int(user_id),
                    session=db_session
                )

                if user_client.enable == False:
                    enable_needed = True
                else:
                    enable_needed = False

            except DBCrudException as e:
                logger.error("Error getting user sub: %s", e)
                return {
                    "success": False,
                    "msg": "Ошибка при получении данных о текущей подписке"
                }

            logger.debug("Fetched user clients: tg_id=%s, user_clients=%s", int(user_id), user_client)

            if enable_needed and user_client:
                await enable_and_prolong_client_by_user_tg_id(
                    client=user_client,
                    session=db_session
                )
                logger.debug("Client required enable, enabled successfully, tg_id=%s, client_id=%s",
                             int(user_id), user_client.id)

            user_referrer_id = await get_user_referrer(
                tg_id=int(user_id),
                session=db_session
            )

            if user_referrer_id:
                await update_balance(
                    user_tg_id=user_referrer_id,
                    amount=20, # TODO: вынести в конфиг
                    session=db_session
                )

            await db_session.commit()

            logger.info("POST /pay request -> 200 OK")
            return {
                "success": True
            }

        except DBCrudException:
            await db_session.rollback()

            logger.error("Error processing payment")
            return {
                "success": False
            }
