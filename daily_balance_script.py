import asyncio
import json
from contextlib import asynccontextmanager
from time import sleep

import aio_pika
import aiohttp
from sqlalchemy import update, select, func

from src.config.settings import settings
from src.backend_logging import logger
from src.repos.database.get_session import get_db_session
from src.dtos.schemas import ClientUpdateSchema
from src.core.clients.update_client import update_vpn_client
from src.repos.database.models import ClientModel, UserModel



async def run_daily_billing(daily_cost: int = settings.payment.daily_price):
    session_context = asynccontextmanager(get_db_session)

    async with session_context() as session:
        logger.info("[BILLING_SCRIPT] Старт биллинга...")
        active_cnt_subquery = (
            select(func.count(ClientModel.id))
            .where(
                ClientModel.tg_id == UserModel.tg_id,
                ClientModel.enable == True
            )
            .scalar_subquery()
        )

        balance_minimized = await session.execute(
            update(UserModel)
            .where(active_cnt_subquery > 0)
            .values(balance=UserModel.balance - (daily_cost * active_cnt_subquery))
        )
        logger.info(f"[BILLING_SCRIPT] Изменено строк в UserModel: {balance_minimized.rowcount}")

        zero_balance_users = await session.scalars(
            select(UserModel.tg_id)
            .where(UserModel.balance <= 0)
            .where(ClientModel.tg_id == UserModel.tg_id)
            .where(ClientModel.enable == True)
        )

        client_count_subq = (
            select(func.count(ClientModel.id))
            .where(ClientModel.tg_id == UserModel.tg_id)
            .scalar_subquery()
        )

        result = await session.execute(
            select(
                UserModel.tg_id,
                client_count_subq.label("clients_count")
            )
            .where(UserModel.balance > 0)
            .where(UserModel.balance <= daily_cost * client_count_subq)
        )

        low_balance_users_list = [row.tg_id for row in result.all()]


        zero_balance_users_list = zero_balance_users.all()


        if zero_balance_users_list:
            turned_off = await session.execute(
                update(ClientModel)
                .where(
                    ClientModel.tg_id.in_(zero_balance_users_list),
                    ClientModel.enable == True
                )
                .values(enable=False)
                .returning(ClientModel.email)
            )

            disabled_emails = turned_off.scalars().all()
            logger.info(f"[BILLING_SCRIPT] Отключено клиентов в БД: {len(disabled_emails)}")

            if disabled_emails:
                async with aiohttp.ClientSession() as http_session:
                    for email in disabled_emails:
                        logger.info(f"[BILLING_SCRIPT] Отправка запроса на отключение VPN для: {email}")
                        try:
                            await update_vpn_client(
                                session=http_session,
                                email=email,
                                updated_client=ClientUpdateSchema(enable=False)
                            )
                        except Exception as e:
                            logger.info(f"[BILLING_SCRIPT] Ошибка при отключении {email}: {e}")


        rabbitmq_conn = await aio_pika.connect(settings.rmq.rmq_connection_url)

        async with rabbitmq_conn, rabbitmq_conn.channel() as rmq_channel:
            for tg_id in zero_balance_users_list:
                sleep(5)
                payload = {
                    "action": "notify",
                    "tg_id": tg_id,
                    "message": "<b>⚠ На Вашем балансе недостаточное количество средств. Услуги приостановлены.\n\n"
                               "Чтобы продолжить пользоваться услугами УруруVPN - пополните баланс!</b>"
                }

                await rmq_channel.default_exchange.publish(
                    aio_pika.Message(
                        body=json.dumps(payload).encode("utf-8"),
                        delivery_mode=aio_pika.DeliveryMode.PERSISTENT
                    ),
                    routing_key="tasks"
                )
                logger.info(f"[BILLING_SCRIPT] Сообщение для {tg_id} отправлено напрямую в notification_tasks.")

            for tg_id in low_balance_users_list:
                sleep(5)
                payload = {
                    "action": "notify",
                    "tg_id": tg_id,
                    "message": "Благодарим за пользование услугами УруруVPN! К сожалению, услуги для Вас могут быть "
                               "в скором времени приостановлены.\n\n"
                               "<b>Рекомендуем Вам пополнить баланс, чтобы отключения не произошло!</b>"
                }

                await rmq_channel.default_exchange.publish(
                    aio_pika.Message(
                        body=json.dumps(payload).encode("utf-8"),
                        delivery_mode=aio_pika.DeliveryMode.PERSISTENT
                    ),
                    routing_key="notification_tasks"
                )
                logger.info(f"[BILLING_SCRIPT] Сообщение для {tg_id} отправлено напрямую в notification_tasks.")

        await session.commit()
        logger.info("[BILLING_SCRIPT] Транзакция успешно зафиксирована.")


if __name__ == "__main__":
    asyncio.run(run_daily_billing())
