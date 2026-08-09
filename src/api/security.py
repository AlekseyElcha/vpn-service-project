from fastapi import Security, HTTPException, status, Request
from fastapi.security.api_key import APIKeyHeader

from src.backend_logging import logger
from src.config.settings import settings

# Ожидаем заголовок X-API-Key в запросах от бота
api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)

async def verify_api_key(request: Request, api_key: str = Security(api_key_header)):
    # Открытые страницы, не требующие ключа
    if request.url.path in ["/connect", "/"]:
        return api_key
        
    if api_key != settings.api_security.api_secret_key:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Could not validate API KEY",
        )
    return api_key