import ssl
from typing import Dict

import aiohttp

from src.backend_logging import logger
from src.config.settings import settings
from src.exceptions.x_ui_exception_handler import ThreeXUIExceptionHandler

headers = \
    {
        "Authorization": f"Bearer {settings.vpn_panel.auth_token}",
        "Accept": "application/json"
    }

async def update_vpn_client_billing(
    email: str,
    expiry_time: int,
    enable: bool,
    session: aiohttp.ClientSession
):
    route = f"/clients/update/{email}"
    url = f"{settings.vpn_panel.panel_url}{route}"

    ssl_context = ssl.create_default_context()
    ssl_context.check_hostname = False
    ssl_context.verify_mode = ssl.CERT_NONE

    json_payload = {
        "email": email,
        "expiryTime": expiry_time,
        "enable": enable,
    }

    try:
        async with session.post(url, headers=headers, json=json_payload, ssl=ssl_context) as response:
            if response.status in (200, 201):
                data = await response.json()

                ThreeXUIExceptionHandler.handle_response(data)

            return response.status

            text = await response.text()


    except aiohttp.ClientError as e:
        raise e
