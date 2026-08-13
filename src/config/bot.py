from pydantic import BaseModel


class TgBotConfig(BaseModel):
    token: str
    name: str
    proxy: str
    payment_test_mode: int
    admins: list[int]
