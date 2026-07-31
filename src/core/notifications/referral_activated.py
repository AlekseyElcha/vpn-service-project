import json

import aio_pika

from src.backend_logging import logger
from src.config.settings import settings
from src.exceptions.notifications import QueuePublishException


async def notify_tg_user_referral_activated(tg_id: int):
    try:
        rabbitmq_conn = await aio_pika.connect(settings.rmq.rmq_connection_url)
        payload = {
            "action": "notify",
            "tg_id": tg_id,
            "message": f"Поздравляем! Вашей реферальной ссылкой успешно воспользовались!\n"
                       f"На Ваш баланс начислен бонус {1}!\n"
                       f"Спасибо Вам!"
        }

        async with rabbitmq_conn, rabbitmq_conn.channel() as rmq_channel:
            await rmq_channel.default_exchange.publish(
                aio_pika.Message(
                    body=json.dumps(payload).encode("utf-8"),
                    delivery_mode=aio_pika.DeliveryMode.PERSISTENT
                ),
                routing_key="notification_tasks"
            )
            logger.info("Published referral activated notification message to queue notification_tasks, payload=%s", payload)
    except aio_pika.exceptions.AMQPError as e:
        raise QueuePublishException