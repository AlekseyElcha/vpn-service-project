import ssl
from typing import Dict, Any

import aiohttp
from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.exceptions.db import DBCrudException
from src.repos.database.models import ClientModel
from src.exceptions.x_ui_exception_handler import ThreeXUIExceptionHandler
from src.config.settings import settings

headers = \
    {
        "Authorization": f"Bearer {settings.vpn_panel.auth_token}",
        "Accept": "application/json"
    }

base_url = settings.vpn_panel.panel_url


async def get_client_info(
        email: str,
        session: aiohttp.ClientSession
) -> Dict[str, Any]:
    route = f"/clients/get/{email}"
    url = f"{base_url}{route}"

    ssl_context = ssl.create_default_context()
    ssl_context.check_hostname = False
    ssl_context.verify_mode = ssl.CERT_NONE

    try:
        async with session.get(url, headers=headers, ssl=ssl_context) as response:
            if response.status == 200:
                data = await response.json()

                ThreeXUIExceptionHandler.handle_response(data)

                return data

            text = await response.text()
            raise HTTPException(status_code=response.status, detail=f"Ошибка API: {text}")

    except aiohttp.ClientError as e:
        raise HTTPException(status_code=500, detail=f"Ошибка внешнего сервиса: {str(e)}")


async def get_subscriptions_by_tg_id(
        tg_id: int,
        session: AsyncSession
):
    query = select(ClientModel).where(ClientModel.tg_id == tg_id)

    try:
        data = await session.execute(query)
        results = data.scalars().all()

        return results
    except:
        raise DBCrudException
