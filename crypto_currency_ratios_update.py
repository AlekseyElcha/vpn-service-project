import asyncio
import json

import aio_pika
import httpx

from src.backend_logging import logger
from src.config.settings import settings

CURRENCIES_IDS_COIN_MC = settings.crypto.currencies_cmc_ids_for_ratio_update

async def run_update_v1(currency_cmc_id: int) -> None:
    async with (httpx.AsyncClient() as client):
        try:
            url = f"http://localhost:8000/currencies/renew"
            response = await client.put(url, params={"currency_cmc_id": currency_cmc_id}, timeout=45.0)

            if response.status_code == 200:
                response = response.json()
                if response.get("success") == True:
                    logger.info("[CURRENCY UPDATE] Successfully updated crypto currency %r", currency_cmc_id)
                else:
                    logger.error("[CURRENCY UPDATE] No success: True in JSON response!")
            else:
                logger.error("[CURRENCY UPDATE] Received non-200 response from server!")
        except Exception as e:
            logger.error("[CURRENCY UPDATE] Exception occured while updating crypto currency %r, %s",
                         currency_cmc_id, e
            )


async def run_update_v2(
        currencies: list = CURRENCIES_IDS_COIN_MC
):
    updated_info = {}

    async with (httpx.AsyncClient() as client):
        for currency_id in currencies:
            try:
                url = f"http://localhost:8000/currencies/renew"
                response = await client.put(url, params={"currency_cmc_id": currency_id}, timeout=45.0)

                if response.status_code == 200:
                    response = response.json()
                    if response.get("success") == True:
                        new_ratio = response.get("currency_ratio")
                        currency_code = response.get("currency_code")
                        updated_info[currency_code] = new_ratio
                    else:
                        updated_info[currency_code] = -1
                else:
                    logger.error("[CURRENCY UPDATE] Received non-200 response from server!")
            except Exception as e:
                logger.error("[CURRENCY UPDATE] Exception occured while updating crypto currency %r, %s",
                             currency_id, e
                )

    rabbitmq_conn = await aio_pika.connect(settings.rmq.rmq_connection_url)

    async with rabbitmq_conn, rabbitmq_conn.channel() as rmq_channel:
        payload = {
            "action": "set_crypto_ratios",
            "data": updated_info
        }

        await rmq_channel.default_exchange.publish(
            aio_pika.Message(
                body=json.dumps(payload).encode("utf-8"),
                delivery_mode=aio_pika.DeliveryMode.PERSISTENT
            ),
            routing_key="tasks"
        )


async def main():
    tasks = [run_update_v2()]
    await asyncio.gather(*tasks)


if __name__ == "__main__":
    asyncio.run(main())
