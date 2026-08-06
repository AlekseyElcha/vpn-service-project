from pydantic import BaseModel

class APISecurityConfig(BaseModel):
    api_secret_key: str
