from fastapi import APIRouter, Query, status, HTTPException, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi.responses import JSONResponse

from src.core.referral.user import get_referrer_tg_id_by_code
from src.exceptions.referrals import UserAlreadyExistsException
from src.core.referral.activate import activate_referral
from src.dtos.schemas import ReferralActivationSchema
from src.exceptions.actions import DBActionException, NotFoundExceptionAction
from src.core.referral.get_link import get_referral_link_for_tg_user
from src.repos.database.get_session import get_db_session

router = APIRouter(prefix="/referral", tags=["Referral"])


@router.get("/link")
async def get_tg_bot_referral_link(
        tg_id: int = Query(...),
        db_session: AsyncSession = Depends(get_db_session)
) -> JSONResponse:
    try:
        ref_link = await get_referral_link_for_tg_user(
            tg_id=tg_id,
            db_session=db_session
        )
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "success": True,
                "referral_link": ref_link
            }
        )
    except DBActionException:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Произошла ошибка."
        )
    except NotFoundExceptionAction:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Не удалось создать ссылку."
        )


@router.post("/activate")
async def activate_referral_subscription(
        referral_code: str  = Query(...),
        referred_tg_id: int = Query(...),
        db_session: AsyncSession = Depends(get_db_session)
):
    referrer_tg_id = await get_referrer_tg_id_by_code(
        ref_code=referral_code,
        session=db_session
    )

    if referrer_tg_id is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Не удалось активировать рефералку."
        )

    referral_info = ReferralActivationSchema(
        referral_code=referral_code,
        referrer_tg_id=referrer_tg_id,
        referred_tg_id=referred_tg_id
    )

    try:
        await activate_referral(
            referral=referral_info,
            db_session=db_session
        )
    except UserAlreadyExistsException:
        return {
            "success": False,
            "msg": "Вы уже зарегистрированы в нашем сервисе, применить реферальную ссылку не получится."
        }

    except DBActionException:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Произошла ошибка!"
        )
    success_message = (f"Успех! Вы воспользовались ссылкой пользователя {referral_info.referrer_tg_id}!\n\n"
                       f"На Ваш начислен бонусный баланс на 7 дней подписки! Добро пожаловать в УруруVPN!")
    return {
        "success": True,
        "msg": success_message
    }
