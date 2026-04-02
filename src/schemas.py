"""Data validation schemas for the Crypto ETL pipeline."""

from pydantic import BaseModel, Field, field_validator
from typing import Optional
from decimal import Decimal
from datetime import datetime


class CryptoMarketData(BaseModel):
    """
    Schema-on-Read: Valida la integridad de CoinGecko.

    Asegura precision financiera mediante el uso de Decimal.
    """

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

    @field_validator(
        "current_price", "market_cap", "total_volume", mode="before"
    )
    @classmethod
    def cast_to_decimal(cls, v):
        """Asegura la conversion correcta a Decimal."""
        if v is None:
            return None
        return Decimal(str(v))

    class Config:
        """Pydantic configuration for attributes."""

        from_attributes = True


class CryptoPriceOutput(CryptoMarketData):
    """
    Schema-on-Write: Valida el contrato antes de la ingesta.

    Incluye metadatos de trazabilidad.
    """

    extracted_at: datetime
