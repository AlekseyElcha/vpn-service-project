import time
import uuid

from typing import Annotated, Dict, Any

from fastapi import APIRouter, Query, Depends, HTTPException, status, Body

import aiohttp

from sqlalchemy.ext.asyncio import AsyncSession
from fastapi.responses import JSONResponse

from src.main import logger
from src.core.utils import build_vpn_subscription_link_from_params
from src.core.clients.client_info import get_client_info
from src.repos.database.crud.checks import check_user_already_has_subscription
from src.repos.database.crud.update import update_db_client, update_trial_availability
from src.core.clients.update_client import update_vpn_client
from src.exceptions.db import DBCrudException
from src.repos.database.crud.removal import delete_client_from_db
from src.exceptions.http import HttpRequestException
from src.core.clients.delete_client import delete_vpn_client
from src.core.clients.new_client import create_new_vpn_client
from src.repos.http_connector.get_http_session import get_http_session
from src.repos.database.get_session import get_db_session
from src.repos.database.crud.creation import add_new_client_to_db
from src.dtos.schemas import NewClientSchema, ClientUpdateSchema
from src.config.settings import settings
from src.utils.response_parser import extract_basic_client_info
from src.utils.time_utils import  calculate_new_unix_expiry_time_days, calculate_new_unix_expiry_time_month

router = APIRouter(prefix="/clients", tags=["Clients"])

token = settings.vpn_panel.auth_token
base_url = settings.vpn_panel.panel_url

headers = \
    {
        "Authorization": f"Bearer {token}",
        "Accept": "application/json"
    }


@router.get("/info")
async def get_basic_client_info(
        http_session: Annotated[aiohttp.ClientSession, Depends(get_http_session)],
        email: str = Query(...),
) -> Dict[str, Any]:
    logger.info(f"GET /info request -> email: {email}")
    info = await get_client_info(
        email=email,
        session=http_session
    )
    basic_info = extract_basic_client_info(
        data=info
    )

    logger.info("GET /info request -> 200 OK")
    return basic_info


@router.get("/link")
async def get_subscription_link(
        http_session: Annotated[aiohttp.ClientSession, Depends(get_http_session)],
        email: str = Query(...)
):
    logger.info("GET /link request -> email: {}".format(email))
    client_info = await get_client_info(
        email=email,
        session=http_session
    )
    logger.debug("Fetched client_info: {}".format(client_info))

    basic_info = extract_basic_client_info(data=client_info)
    logger.debug("Extracted basic client info: {}".format(basic_info))

    sub_id = basic_info.get("subId", "")

    if sub_id and isinstance(sub_id, str):
        sub_link = build_vpn_subscription_link_from_params(
            domain=settings.vpn_panel.domain,
            port=settings.vpn_panel.subscription_port,
            prefix=settings.vpn_panel.subscription_prefix,
            sub_id=sub_id
        )
        logger.debug("Created subscription link: {}".format(sub_link))

        logger.info("GET /link request ->200 OK")
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "msg": "success",
                "link": sub_link
            }
        )
    else:
        logger.error("Error building subscription link: no sub_id info")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Произошла ошибка при создании ссылки."
        )



@router.post("/add")
async def create_new_client(
        new_client: NewClientSchema,
        db_session: AsyncSession = Depends(get_db_session),
        http_session: aiohttp.ClientSession = Depends(get_http_session)
) -> JSONResponse:
    user_tg_id = new_client.client.tg_id

    try:
        user_has_sub = await check_user_already_has_subscription(
            tg_id=user_tg_id,
            session=db_session
        )
    except DBCrudException:
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "success": False,
                "msg": "Произошла ошибка!"
            }
        )

    if user_has_sub:
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={
                "success": False,
                "msg": "У Вас уже есть подписка!"
            }
        )


    logger.info("POST /add request -> new_client: {}".format(new_client))

    email_extra = str(uuid.uuid4())[:5]

    client_email = new_client.client.email + email_extra
    new_client.client.email = client_email

    creation_unix_time = int(time.time())
    
    if new_client.is_trial:
        sub_expiration_time = calculate_new_unix_expiry_time_days(
            first_unix_time=creation_unix_time,
            days_ahead=3
        )
    else:
        sub_expiration_time = calculate_new_unix_expiry_time_month(
            first_unix_time=creation_unix_time,
            month_ahead=1
        )

    new_client.client.expiry_time = sub_expiration_time * 1000 # 3x-ui ожидает время в мс

    # обработка через спец.класс
    await create_new_vpn_client(
        new_client=new_client,
        session=http_session
    )

    new_client.client.expiry_time = sub_expiration_time # БД ожидает время с секундах
    logger.debug("Created new vpn client successfully, email: {}".format(client_email))

    try:
        await add_new_client_to_db(
            new_client=new_client,
            session=db_session
        )
        await update_trial_availability(
            user_tg_id=user_tg_id,
            valid_for_trial=False,
            trial_used=True,
            session=db_session
        ) # при покупке / получении бесплатной подписки возможность получения тестового периода слетает
        logger.debug("Created new db client successfully")

    except Exception as e:
        logger.error("Error while creating new db client: {}".format(e))
        try:
            await delete_vpn_client(
                email=new_client.client.email,
                keep_traffic=0,
                session=http_session
            )
            logger.debug("Deleted vpn client successfully, email: {}".format(new_client.client.email))
        except HttpRequestException:
            logger.error("Error while deleting vpn client: {}".format(e))
            return JSONResponse(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                content={
                    "success": False,
                    "msg": "Произошла ошибка!"
                }
            )
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "success": False,
                "msg": "Произошла ошибка!"
            }
        )

    logger.info("POST /add request -> 200 OK")
    return JSONResponse(
        status_code=status.HTTP_201_CREATED,
        content={
            "success": True,
            "msg": "Подписка успешно создана!"
        }
    )


@router.post("/delete/{email}")
async def delete_client(
        email: str,
        keep_traffic: int = Query(...),
        db_session: AsyncSession = Depends(get_db_session),
        http_session: aiohttp.ClientSession = Depends(get_http_session)
) -> JSONResponse:
    logger.info("POST /delete request -> email: {}".format(email))

    # обработка через спец. класс
    await delete_vpn_client(
            email=email,
            keep_traffic=keep_traffic,
            session=http_session
        )
    logger.debug("Deleted vpn client successfully, email: {}".format(email))
    try:
        await delete_client_from_db(
            email=email,
            session=db_session
        )
        logger.debug("Deleted db client successfully, email: {}".format(email))
    except DBCrudException:
        logger.error("Error while deleting db client: {}".format(email))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Произошла внутренняя ошибка сервера."
        )
    logger.info("POST /delete request -> 200 OK")
    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content={
            "msg": "success"
        }
    )


@router.post("/update")
async def update_client(
        update_data: ClientUpdateSchema,
        db_session: AsyncSession = Depends(get_db_session),
        http_session: aiohttp.ClientSession = Depends(get_http_session)
) -> JSONResponse:
    logger.info("POST /update request -> update_data: {}".format(update_data))

    client_dict = update_data.model_dump(by_alias=True)
    logger.debug("Client dict for update: {}".format(client_dict))
    await update_vpn_client(
        email=update_data.email,
        updated_client=client_dict,
        session=http_session
    )
    logger.debug("Updated vpn client successfully, email: {}".format(update_data.email))
    try:
        await update_db_client(
            updated_client=update_data,
            session=db_session
        )
        logger.debug("Updated db client successfully, email: {}".format(update_data.email))
    except DBCrudException:
        logger.error("Error while updating db client: {}".format(update_data.email))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Произошла внутренняя ошибка сервера."
        )

    logger.info("POST /update request -> 200 OK")
    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content={
            "msg": "success"
        }
    )
