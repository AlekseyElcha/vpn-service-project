from typing import Any, Dict

import httpx
from telegram_stars_rates import get_stars_rate

from src.config.settings import settings


async def fetch_crypto_currency_price_via_coinmarketcap(crypto_id: int) -> Dict[str, Any] | None:
    async with httpx.AsyncClient() as client:
        try:
            url = f"https://pro-api.coinmarketcap.com/v2/cryptocurrency/quotes/latest"

            headers = {
                "Accept": "application/json",
                "X-CMC_PRO_API_KEY": settings.crypto.coinmarketcap_api_key
            }

            response = await client.get(url, params={"id": crypto_id}, headers=headers, timeout=30.0)

            if response.status_code == 200:
                response = response.json()
                data = response["data"][str(crypto_id)]

                name = data["name"]
                symbol = data["symbol"]

                usd_quote = data["quote"]["USD"]
                price = usd_quote["price"]

                return {
                    "name": name,
                    "symbol": symbol,
                    "price": price
                }
            else:
                return None
        except Exception as e:
            return None


async def fetch_tg_stars_to_usd() -> int | None:
    result = get_stars_rate()
    print(result)
    if result:
        price_usd = result["usdt_per_star"]
        if price_usd == -1:
            return None
        return price_usd
    return None

