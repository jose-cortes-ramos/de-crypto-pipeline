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
    COINGECKO_BASE_URL = os.getenv("COINGECKO_BASE_URL", "https://api.coingecko.com/api/v3")
    COINGECKO_API_KEY = os.getenv("COINGECKO_API_KEY")
    
    # Parámetros por defecto para la extracción
    DEFAULT_CURRENCY = "usd"
    PER_PAGE = 50
    ORDER = "market_cap_desc"

    # Database Config
    DATABASE_URL = os.getenv("DATABASE_URL")

    # ETL Monitoring & Logging
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
    LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

    @classmethod
    def validate(cls):
        """Valida que las variables críticas existan para evitar fallos en runtime."""
        if not cls.DATABASE_URL:
            # En un entorno senior, fallamos rápido si la configuración está mal
            raise ValueError("CRITICAL CONFIG ERROR: DATABASE_URL is not set.")
        
        if not cls.COINGECKO_BASE_URL:
            raise ValueError("CRITICAL CONFIG ERROR: COINGECKO_BASE_URL is missing.")
