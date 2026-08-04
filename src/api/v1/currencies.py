import json
from typing import List, Sequence

import aio_pika
from fastapi import APIRouter, HTTPException, status, Depends, Query, Body
from sqlalchemy import Row
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi.responses import JSONResponse

from src.backend_logging import logger
from src.config.settings import settings
from src.core.external.crypto_currency import fetch_crypto_currency_price_via_coinmarketcap, fetch_tg_stars_to_usd
from src.exceptions.db import NotFoundException, DBCrudException
from src.repos.database.crud.crypto import update_crypto_ratio, crypto_ratio_exists_in_db, create_new_crypto_ratio
from src.repos.database.crud.currencies import get_currency_ratio_from_db, get_many_currency_ratios_from_db
from src.repos.database.get_session import get_db_session
from src.utils.round_ratios import round_ratio

router = APIRouter(prefix="/currencies", tags=["currencies"])

@router.get("/get")
async def get_local_crypto_currency_ratio(
        currency_code: str = Query(...),
        db_session: AsyncSession = Depends(get_db_session)
) -> JSONResponse:
    currency_code = currency_code.upper()

    try:
        currency_ratio = await get_currency_ratio_from_db(
            currency_code=currency_code,
            session=db_session
        )
    except NotFoundException:
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content={
                "success": False,
                "currency_ratio": "not info",
            }
        )

    except DBCrudException:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Произошла ошибка.",
        )

    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content={
            "success": True,
            "currency_ratio": currency_ratio,
        }
    )


@router.get("/many")
async def get_local_crypto_currency_ratio(
        currency_names: List[str] = Query(...),
        db_session: AsyncSession = Depends(get_db_session)
):
    currency_names = [",".join(currency_names) for _ in currency_names]
    try:
        results = await get_many_currency_ratios_from_db(
            currency_names=currency_names,
            session=db_session
        )
    except DBCrudException:
        return None
    return results


@router.put("/renew")
async def update_local_crypto_currency_ratio(
        currency_cmc_id: int = Query(...),
        db_session: AsyncSession = Depends(get_db_session)
) -> JSONResponse:
    crypto_info = await fetch_crypto_currency_price_via_coinmarketcap(crypto_id=currency_cmc_id)
    if crypto_info is None:
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={
                "success": False,
                "currency_ratio": "not info",
            }
        )
    crypto_symbol = crypto_info["symbol"]
    crypto_price = crypto_info["price"]

    if crypto_symbol == "GRAM":
        crypto_symbol = "TON"

    stars_price_in_usd = await fetch_tg_stars_to_usd()
    if stars_price_in_usd is None:
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={
                "success": False,
                "currency_code": crypto_symbol,
                "msg": "no info",
            }
        )

    ratio = crypto_price / stars_price_in_usd

    rounded_ratio = round_ratio(ratio)

    try:
        currency_exists_in_db = await crypto_ratio_exists_in_db(
            crypto_code=crypto_symbol,
            session=db_session
        )
    except DBCrudException:
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "success": False,
                "currency_code": crypto_symbol,
                "msg": "db error",
            }
        )

    if not currency_exists_in_db:
        try:
            await create_new_crypto_ratio(
                crypto_code=crypto_symbol,
                currency_cmd_id=currency_cmc_id,
                ratio=rounded_ratio,
                session=db_session
            )
        except DBCrudException:
            return JSONResponse(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                content={
                    "success": False,
                    "currency_code": crypto_symbol,
                    "msg": "db error 1",
                }
            )
    else:
        try:
            await update_crypto_ratio(
                crypto_code=crypto_symbol,
                new_ratio=rounded_ratio,
                session=db_session
            )
        except DBCrudException:
            return JSONResponse(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                content={
                    "success": False,
                    "currency_code": crypto_symbol,
                    "msg": "db error",
                }
            )

    rabbitmq_conn = await aio_pika.connect(settings.rmq.rmq_connection_url)

    async with rabbitmq_conn, rabbitmq_conn.channel() as rmq_channel:
            payload = {
                "action": "set_crypto_ratios",
                "currency_data": []
            }

            await rmq_channel.default_exchange.publish(
                aio_pika.Message(
                    body=json.dumps(payload).encode("utf-8"),
                    delivery_mode=aio_pika.DeliveryMode.PERSISTENT
                ),
                routing_key="tasks"
            )

    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content={
            "success": True,
            "currency_code": crypto_symbol,
            "currency_ratio": rounded_ratio,
        }
    )

