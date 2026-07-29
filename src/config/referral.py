from pydantic import BaseModel


class ReferralProgramConfig(BaseModel):
    code_length: int
    referred_bonus: int
    referrer_bonus: int
