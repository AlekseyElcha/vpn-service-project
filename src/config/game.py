from pydantic import BaseModel


class DailyGameConfig(BaseModel):
    days_required: int
    reward: int
