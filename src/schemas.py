from pydantic import BaseModel, Field, field_validator, ConfigDict
from typing import Optional
from decimal import Decimal
from datetime import datetime

class CryptoMarketData(BaseModel):
    """
    Schema-on-Read: Valida la integridad de los datos recibidos de CoinGecko.
    Asegura precision financiera mediante el uso de Decimal (Issue #3).
    """
    model_config = ConfigDict(from_attributes=True)
    
    id: str
    symbol: str
    name: str
    current_price: Decimal = Field(..., gt=0) 
    market_cap: Decimal
    market_cap_rank: int
    total_volume: Decimal
    high_24h: Optional[Decimal] = None
    low_24h: Optional[Decimal] = None
    price_change_percentage_24h: Optional[Decimal] = None

    @field_validator('current_price', 'market_cap', 'total_volume', mode='before')
    @classmethod
    def cast_to_decimal(cls, v):
        """Asegura que los valores numericos se conviertan a Decimal correctamente."""
        if v is None:
            return None
        return Decimal(str(v))

class CryptoPriceOutput(CryptoMarketData):
    """
    Schema-on-Write: Valida el contrato final antes de la ingesta en DB.
    Incluye metadatos de trazabilidad.
    """
    extracted_at: datetime
