from pydantic import BaseModel


class CryptoConfig(BaseModel):
    coinmarketcap_api_key: str
    currencies_cmc_ids_for_ratio_update: list[int]
