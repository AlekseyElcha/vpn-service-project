from contextlib import asynccontextmanager

import aiohttp
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi import Depends

from src.backend_logging import logger
from src.fastapi_startup import start
from src.api.v1.inbounds import router as inbounds_router
from src.api.v1.clients import router as clients_router
from src.api.v1.users import router as users_router
from src.api.v1.server import router as server_router
from src.api.v1.pay import router as payment_router
from src.api.v1.checks import router as checks_router
from src.api.v1.promo import router as promo_router
from src.api.v1.referral import router as referral_router
from src.api.v1.currencies import router as currency_router
from src.api.v1.daily_game import router as daily_game_router
from src.api.security import verify_api_key

@asynccontextmanager
async def lifespan(_: FastAPI):
    app.state.http_session = aiohttp.ClientSession()
    await start()
    logger.info("Application started successfully")
    yield
    await app.state.http_session.close()
    logger.info("Application stopped successfully")


tags_metadata = [
    {"name": "Inbounds", "description": "Управление доступом к протоколам VPN."},
    {"name": "Clients", "description": "Работа с VPN-клиентами."},
    {"name": "Users", "description": "Работа с администраторами."},
    {"name": "Payment", "description": "Прием оплаты через Telegram Stars"},
    {"name": "Server", "description": "Получение метрик VPN-сервера"},
    {"name": "Server Checks", "description": "Пингование инфраструктуры"},
    {"name": "Promo", "description": "Промокоды для бонусного баланса"},
    {"name": "Referral", "description": "Реферальная система"},
]


app = FastAPI(
    lifespan=lifespan,
    openapi_tags=tags_metadata
)

# Добавляем глобальную зависимость на проверку ключа
app.router.dependencies.append(Depends(verify_api_key))

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:443",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router=inbounds_router)
app.include_router(router=clients_router)
app.include_router(router=payment_router)
app.include_router(router=users_router)
app.include_router(router=server_router)
app.include_router(router=checks_router)
app.include_router(router=promo_router)
app.include_router(router=referral_router)
app.include_router(router=currency_router)
app.include_router(router=daily_game_router)

@app.get("/")
async def root():
    return {
        "msg": "working"
    }
