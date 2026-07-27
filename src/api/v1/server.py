import aiohttp
from fastapi import APIRouter, Depends

from src.backend_logging import logger
from src.config.settings import settings
from src.core.server.get_status import get_xray_status, get_server_status
from src.repos.http_connector.get_http_session import get_http_session


router = APIRouter(prefix="/server", tags=["Server"])


@router.get("/status")
async def get_server_status_for_users(
        http_session: aiohttp.ClientSession = Depends(get_http_session)
):
    logger.info("GET /status request")

    result = {}

    server_info = await get_server_status(
        session=http_session
    )
    logger.debug("Fetched server info: {}".format(server_info))

    if not server_info:
        result["server_running"] = "no info"
    elif server_info.get("success"):
        result["server_running"] = True
    else:
        result["server_running"] = False

    xray_info = await get_xray_status(
        session=http_session
    )
    if not xray_info:
        result["xray_running"] = "no info"
    elif xray_info.get("success"):
        obj_block = xray_info.get("obj")
        if obj_block.get("enabled"):
            result["xray_running"] = True
        else:
            result["xray_running"] = False
    else:
        result["xray_running"] = "no info"

    result["comment"] = settings.vpn_panel.server_status_comment

    logger.info("GET /status request -> 200 OK")
    return result

