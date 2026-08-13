import asyncio
import json
import time
from contextlib import asynccontextmanager
from typing import Final

import aio_pika
import aiohttp
from sqlalchemy import select

from src.backend_logging import logger
from src.billing.db.update import update_db_client_billing, update_user_balance_billing
from src.billing.vpn.update import update_vpn_client_billing
from src.config.settings import settings
from src.exceptions.db import DBCrudException
from src.repos.database.get_session import get_db_session
from src.repos.database.models import ClientModel, UserModel
from src.utils.time_utils import calculate_new_unix_expiry_time

MONTHLY_PRICE_RUB = settings.payment.price_1_month_rub
HOUR_IN_UNIX = 3600

async def run_billing():
    current_unix_time: Final = int(time.time())

    time_from = current_unix_time + (23 * HOUR_IN_UNIX)
    time_to = current_unix_time + (24 * HOUR_IN_UNIX)

    updated_subs_tg_ids = []
    low_balance_tg_id = []
    expired_subs_tg_ids_low_balance = []

    error_messages_for_admins = []


    query_select_expired_with_balance = (
        select(ClientModel, UserModel)
        .join(UserModel, ClientModel.tg_id == UserModel.tg_id)
        .where(
            ClientModel.tg_id == UserModel.tg_id,
            ClientModel.expiry_time <= current_unix_time,
            UserModel.balance >= MONTHLY_PRICE_RUB,
        )
    )

    query_select_low_balance = (
        select(ClientModel, UserModel)
        .join(ClientModel, UserModel.tg_id == ClientModel.tg_id)
        .where(
            ClientModel.expiry_time >= time_from,
            ClientModel.expiry_time <= time_to,
            UserModel.balance <= MONTHLY_PRICE_RUB,
        )
    )

    query_select_expired = (
        select(ClientModel, UserModel)
        .join(ClientModel, UserModel.tg_id == ClientModel.tg_id)
        .where(
            ClientModel.expiry_time < current_unix_time,
            ClientModel.enable == True,
            UserModel.balance <= MONTHLY_PRICE_RUB,
        )
    )

    session_context_db = asynccontextmanager(get_db_session)
# ---------------------------------------------------------------------------------------

    async with session_context_db() as db_session:
        async with aiohttp.ClientSession() as http_session:
            exp_with_balance_exec = await db_session.execute(query_select_expired_with_balance)
            expired_with_balance = exp_with_balance_exec.tuples().all()

            for client, user in expired_with_balance:
                new_user_balance = user.balance - MONTHLY_PRICE_RUB

                base_expiry = calculate_new_unix_expiry_time(
                    first_unix_time=current_unix_time,
                    month_ahead=1
                )
                new_expiration_time_db = base_expiry
                new_expiration_time_vpn = base_expiry * 1000

                try:
                    async with db_session.begin_nested():
                        await update_db_client_billing(
                            tg_id=client.tg_id,
                            enable=True,
                            expiry_time=new_expiration_time_db,
                            db_session=db_session,
                        )
                        await update_user_balance_billing(
                            tg_id=client.tg_id,
                            new_balance=new_user_balance,
                            db_session=db_session,
                        )

                except DBCrudException:
                    continue

                try:
                    await update_vpn_client_billing(
                        email=client.email,
                        expiry_time=new_expiration_time_vpn,
                        enable=True,
                        session=http_session
                    )
                    updated_subs_tg_ids.append(client.tg_id)

                except Exception as e:
                    error_messages_for_admins.append(f"БД обновлена, но VPN для {client.email} упал: {e}")
                    logger.error(f"БД обновлена, но VPN для {client.email} упал: {e}")

            await db_session.commit()

        await db_session.commit()
    logger.info("[BILLING_SCRIPT] Successfully updated users with expired subs!")
# ---------------------------------------------------------------------------------------

    async with session_context_db() as db_session:
        low_balance_query_exec = await db_session.execute(query_select_low_balance)

        for client, user in low_balance_query_exec:
            low_balance_tg_id.append(client.tg_id)

    logger.info("[BILLING_SCRIPT] Successfully checked for users with low balance!")
# ---------------------------------------------------------------------------------------

    async with session_context_db() as db_session:
        async with aiohttp.ClientSession() as http_session:
            expired_subs_query_exec = await db_session.execute(query_select_expired)

            for client, user in expired_subs_query_exec:
                try:
                    async with db_session.begin_nested():
                        await update_db_client_billing(
                            tg_id=client.tg_id,
                            enable=False,
                            expiry_time=client.expiry_time,
                            db_session=db_session
                        )
                except DBCrudException as db_err:
                    logger.error(f"Не удалось отключить клиента {client.tg_id} в БД: {db_err}")
                    continue

                try:
                    await update_vpn_client_billing(
                        email=client.email,
                        expiry_time=client.expiry_time,
                        enable=False,
                        session=http_session
                    )

                    expired_subs_tg_ids_low_balance.append(client.tg_id)

                except Exception as vpn_err:
                    logger.error(
                        f"БД обновлена, но VPN-сервер не отключил {client.email}. "
                        f"Требуется ручная синхронизация!!! Ошибка: {vpn_err}"
                    )
                    error_messages_for_admins.append(f"БД обновлена, но VPN-сервер не отключил {client.email}. "
                        f"Требуется ручная синхронизация! Ошибка: {vpn_err}")


            await db_session.commit()

    logger.info(
        f"[BILLING_SCRIPT] Завершено отключение клиентов с низким балансом. Успешно обработано: {len(expired_subs_tg_ids_low_balance)}")
# ---------------------------------------------------------------------------------------

    rabbitmq_conn = await aio_pika.connect(settings.rmq.rmq_connection_url)
    async with rabbitmq_conn, rabbitmq_conn.channel() as rmq_channel:
        errors = "\n\n".join(error_messages_for_admins)
        admin_tg_ids = settings.bot.admins
        for tg_id in admin_tg_ids:
            payload = {
                "action": "notify",
                "tg_id": tg_id,
                "message": f"<b>Информация по работе биллинга:\n\n</b>"
                           f"{errors if errors else "Ошибок нет, все отлично!"}\n\n"
                           f"-----------------------------------------------------\n\n"
                           f"+ Автопродление: {updated_subs_tg_ids}\n\n"
                           f"+ Предупреждение о низком балансе: {low_balance_tg_id}\n\n"
                           f"+ Отключение: {expired_subs_tg_ids_low_balance}\n\n"
            }
            await rmq_channel.default_exchange.publish(
                aio_pika.Message(
                    body=json.dumps(payload).encode("utf-8"),
                    delivery_mode=aio_pika.DeliveryMode.PERSISTENT
                ),
                routing_key="tasks"
            )
            logger.info(f"[BILLING_SCRIPT] Сообщение для {tg_id} АДМИН отправлено в очередь tasks.")

        for tg_id in updated_subs_tg_ids:
            payload = {
                "action": "notify",
                "tg_id": tg_id,
                "message": "<b>✅ Ваша подписка была автоматически продлена!\n\n"
                           "❤️ Благодарим за использование услуг УруруVPN!</b>"
            }

            await rmq_channel.default_exchange.publish(
                aio_pika.Message(
                    body=json.dumps(payload).encode("utf-8"),
                    delivery_mode=aio_pika.DeliveryMode.PERSISTENT
                ),
                routing_key="tasks"
            )
            logger.info(f"[BILLING_SCRIPT] Сообщение для {tg_id} отправлено в очередь tasks.")

        for tg_id in low_balance_tg_id:
            payload = {
                "action": "notify",
                "tg_id": tg_id,
                "message": "<b>⚠️ Уважаемый клиент!\n\n"
                           "Благодарим Вас за ипользование услуг УруруVPN!\n\n"
                           "К сожалению, в скором времени услуги для Вас могут быть приостановлены.\n\n"
                           "Чтобы этого не произошло, пожалуйста, пополните баланс! ⚠️</b>"
            }

            await rmq_channel.default_exchange.publish(
                aio_pika.Message(
                    body=json.dumps(payload).encode("utf-8"),
                    delivery_mode=aio_pika.DeliveryMode.PERSISTENT
                ),
                routing_key="tasks"
            )
            logger.info(f"[BILLING_SCRIPT] Сообщение для {tg_id} отправлено в очередь tasks.")

        for tg_id in expired_subs_tg_ids_low_balance:
            payload = {
                "action": "notify",
                "tg_id": tg_id,
                "message": "<b>❗❗❗Ваша подписка УруруVPN отключена❗❗❗\n\n"
                           "Чтобы продолжить пользоваться подпиской - пополните баланс в Личном кабинете сервиса!</b>"
            }

            await rmq_channel.default_exchange.publish(
                aio_pika.Message(
                    body=json.dumps(payload).encode("utf-8"),
                    delivery_mode=aio_pika.DeliveryMode.PERSISTENT
                ),
                routing_key="tasks"
            )
            logger.info(f"[BILLING_SCRIPT] Сообщение для {tg_id} отправлено в очередь tasks.")


if __name__ == "__main__":
    asyncio.run(run_billing())