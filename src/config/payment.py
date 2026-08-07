from pydantic import BaseModel


class PaymentConfig(BaseModel):
    daily_price: int
    price_1_month_rub: int
    price_3_month_rub: int
    price_6_month_rub: int

    price_1_month_stars: int
    price_3_month_stars: int
    price_6_month_stars: int