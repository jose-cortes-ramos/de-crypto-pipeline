import logging
import requests
from sqlalchemy import text
from sqlalchemy.engine import Engine
from src.config import Config

logger = logging.getLogger(__name__)

def check_api_health() -> bool:
    """
    Verifica la conectividad con la API de CoinGecko antes de iniciar.
    Nivel: Senior Resilience.
    """
    try:
        url = f"{Config.COINGECKO_BASE_URL}/ping"
        logger.info(f"Healthcheck: Checking API connectivity to {url}...")
        
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        
        logger.info("Healthcheck: API is reachable and healthy.")
        return True
    except Exception as e:
        logger.error(f"Healthcheck Failure: API is unreachable. Error -> {e}")
        return False

def check_db_health(engine: Engine) -> bool:
    """
    Verifica la conectividad con PostgreSQL mediante una consulta simple.
    Nivel: Senior Resilience.
    """
    try:
        logger.info("Healthcheck: Checking Database connectivity...")
        with engine.connect() as conn:
            # Ejecutamos una consulta trivial para validar la conexion
            conn.execute(text("SELECT 1"))
        
        logger.info("Healthcheck: Database is reachable and healthy.")
        return True
    except Exception as e:
        logger.error(f"Healthcheck Failure: Database connection failed. Error -> {e}")
        return False
