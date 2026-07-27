from contextlib import asynccontextmanager
from datetime import datetime

from fastapi import APIRouter, Body

from src.backend_logging import logger
from src.core.clients.toggle_client import enable_clients_by_user_tg_id
from src.dtos.schemas import NewUserSchema, PaymentRecordSchema
from src.exceptions.db import DBCrudException
from src.payments.balance import update_balance
from src.repos.database.crud.basic_utils import user_existence_by_tg_id, get_user_clients, get_user_balance_by_tg_id
from src.repos.database.crud.creation import add_new_user_to_db_without_commit
from src.repos.database.crud.payments import add_payment_record_to_db
from src.repos.database.get_session import get_db_session


router = APIRouter(prefix="/payment", tags=["Payment"])


@router.post("/pay")
async def process_successful_payment(user_id: int = Body(embed=True),
                              payment_amount: int | float = Body(embed=True),
                              item_id: str = Body(embed=True)
):
    logger.info("POST /pay request -> user id=%s, payment_amount=%s, item_id=%s", user_id, payment_amount, item_id)

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

            if (old_balance <= 0) and (old_balance + payment_amount) > 0:
                enable_needed = True
            else:
                enable_needed = False

            time_now = int(datetime.now().timestamp())
            await add_payment_record_to_db(
                new_record=PaymentRecordSchema(
                    tg_id=int(user_id),
                    item_id=item_id,
                    time=time_now,
                    amount=payment_amount,
                ),
                session=db_session,
            )
            logger.debug("Added payment record to db: tg_id=%s, item_id=%s, time=%s, amount=%s",
                         int(user_id), item_id, time_now, payment_amount)

            await update_balance(
                user_tg_id=int(user_id),
                stars_amount=payment_amount,
                session=db_session,
            )
            logger.debug("Updated user balance: tg_id=%s", int(user_id))

            user_clients = await get_user_clients(
                tg_id=int(user_id),
                session=db_session
            )
            logger.debug("Fetched user clients: tg_id=%s, user_clients=%s", int(user_id), user_clients)

            if enable_needed and user_clients:
                await enable_clients_by_user_tg_id(
                    client_ids=user_clients,
                    session=db_session
                )
                logger.debug("Clients required enable, enabled successfully, tg_id=%s, client_ids=%s",
                             int(user_id), user_clients)

            await db_session.commit()
            logger.info("POST /pay request -> 200 OK")
            return {
                "success": True
            }

        except DBCrudException as e:
            await db_session.rollback()

            logger.error("Error processing payment: %s", e)
            return {
                "success": False
            }
