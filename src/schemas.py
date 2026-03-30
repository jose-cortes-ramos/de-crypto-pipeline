from pydantic import BaseModel, Field
from typing import Optional

class CryptoMarketData(BaseModel):
    """
    Schema-on-Read: Valida la integridad de los datos recibidos de CoinGecko.
    Asegura que la respuesta cruda coincida con el esquema JSON esperado (Requisito 3).
    """
    id: str
    symbol: str
    name: str
    current_price: float = Field(..., gt=0) # El precio debe ser mayor a 0
    market_cap: float
    market_cap_rank: int
    total_volume: float
    high_24h: Optional[float] = None
    low_24h: Optional[float] = None
    price_change_percentage_24h: Optional[float] = None

    class Config:
        # Permite la creación desde diccionarios de la API
        from_attributes = True
