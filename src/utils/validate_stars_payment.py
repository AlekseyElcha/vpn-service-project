from src.config.settings import settings


def validate_stars_payment_return_rub_price(
        month_count: int,
) -> int | None:
    month_prices = {
        1: (settings.payment.price_1_month_stars, settings.payment.price_1_month_rub),
        3: (settings.payment.price_3_month_stars, settings.payment.price_3_month_rub),
        6: (settings.payment.price_6_month_stars, settings.payment.price_6_month_rub),
    }

    prices = month_prices.get(month_count)
    if not prices:
        return None

    return prices[1]


