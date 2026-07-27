from fastapi import APIRouter, status
from fastapi.responses import JSONResponse
from ping3 import ping

from src.backend_logging import logger
from src.config.settings import settings

router = APIRouter(prefix="/check", tags=["API Check"])


@router.get("/ping-api")
async def pong() -> JSONResponse:
    logger.info("GET /ping request")
    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content={
            "success": True
        }
    )


@router.get("/ping-vpn-server")
async def ping_vpn_server() -> JSONResponse:
    logger.info("GET /ping-vpn-server request")

    address = settings.vpn_panel.domain.split("://")[1]
    response = ping(address)

    if response:
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "success": True,
                "ping": int(response * 1000)
            }
        )
    else:
        return JSONResponse(
            status_code = status.HTTP_400_BAD_REQUEST,
            content = {
                "success": False,
                "ping": "timeout"
            }
        )


