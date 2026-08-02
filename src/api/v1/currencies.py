from fastapi import APIRouter, HTTPException, status, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi.responses import JSONResponse

from src.exceptions.db import NotFoundException, DBCrudException
from src.repos.database.crud.currencies import get_currency_ratio_from_db
from src.repos.database.get_session import get_db_session

router = APIRouter(prefix="/currencies", tags=["currencies"])

@router.get("/get")
async def get_local_crypto_currency_ratio(
        currency_code: str,
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
