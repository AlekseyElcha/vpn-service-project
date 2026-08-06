from fastapi import Security, HTTPException, status
from fastapi.security.api_key import APIKeyHeader
from src.config.settings import settings

# Ожидаем заголовок X-API-Key в запросах от бота
api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)

async def verify_api_key(api_key: str = Security(api_key_header)):
    if api_key != settings.api_secret_key:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Could not validate API KEY",
        )
    return api_key