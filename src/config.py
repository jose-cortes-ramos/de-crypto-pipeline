"""Configuration module for the Crypto ETL pipeline."""

import os
from dotenv import load_dotenv

# Cargar variables de entorno desde .env
load_dotenv()


class Config:
    """
    Configuración centralizada para el pipeline de datos.

    Elimina el hardcoding y permite gestionar entornos fácilmente.
    """

    # CoinGecko API Config
    COINGECKO_BASE_URL = os.getenv(
        "COINGECKO_BASE_URL", "https://api.coingecko.com/api/v3"
    )
    COINGECKO_API_KEY = os.getenv("COINGECKO_API_KEY")

    # Parámetros por defecto para la extracción
    DEFAULT_CURRENCY = "usd"
    PER_PAGE = 50
    ORDER = "market_cap_desc"

    # Database Config
    DATABASE_URL = os.getenv("DATABASE_URL")
    DB_POOL_SIZE = int(os.getenv("DB_POOL_SIZE", "5"))
    DB_MAX_OVERFLOW = int(os.getenv("DB_MAX_OVERFLOW", "10"))
    DB_POOL_TIMEOUT = int(os.getenv("DB_POOL_TIMEOUT", "30"))

    # GCP Config (Issue #6)
    GCP_BUCKET_NAME = os.getenv("GCP_BUCKET_NAME")
    GCP_CREDENTIALS_PATH = os.getenv("GCP_CREDENTIALS_PATH")

    # Analytics Config (Issue #7)
    ANALYTICS_ASSETS = [
        "bitcoin",
        "ethereum",
        "solana",
        "binancecoin",
        "ripple",
    ]
    HISTORICAL_DAYS = 365

    # ETL Monitoring & Logging
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
    LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    # Formato JSON para observabilidad avanzada (Senior Feature)
    LOG_JSON_FIELDS = "levelname,name,message,asctime,filename,lineno"

    @classmethod
    def validate(cls):
        """Valida que existan variables críticas para evitar fallos."""
        if not cls.DATABASE_URL:
            # Fallamos rápido si la configuración está mal
            raise ValueError("CRITICAL CONFIG ERROR: DATABASE_URL is not set.")

        if not cls.COINGECKO_BASE_URL:
            raise ValueError(
                "CRITICAL CONFIG ERROR: COINGECKO_BASE_URL is missing."
            )
