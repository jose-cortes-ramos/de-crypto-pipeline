import requests
import time
import logging
from typing import List, Dict, Any
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

from src.config import Config
from src.schemas import CryptoMarketData

logger = logging.getLogger(__name__)

class CoinGeckoExtractor:
    """
    Extractor modular para CoinGecko con lógica de reintentos y validación de esquemas.
    Nivel: Senior Data Engineering.
    """
    
    def __init__(self):
        self.base_url = Config.COINGECKO_BASE_URL
        self.api_key = Config.COINGECKO_API_KEY
        self.params = {
            "vs_currency": Config.DEFAULT_CURRENCY,
            "order": Config.ORDER,
            "per_page": Config.PER_PAGE,
            "page": 1,
            "sparkline": False
        }
        # Añadimos la API Key a los headers si está presente
        self.headers = {"x-cg-demo-api-key": self.api_key} if self.api_key else {}

    @retry(
        stop=stop_after_attempt(5),
        wait=wait_exponential(multiplier=1, min=4, max=60),
        retry=retry_if_exception_type(requests.exceptions.RequestException),
        before_sleep=lambda retry_state: logger.warning(
            f"Retrying extraction... Attempt {retry_state.attempt_number}. "
            f"Error: {retry_state.outcome.exception()}"
        )
    )
    def fetch_raw_data(self) -> List[Dict[str, Any]]:
        """
        Consume la API con reintentos automáticos (Exponential Backoff).
        """
        url = f"{self.base_url}/coins/markets"
        
        start_time = time.time()
        response = requests.get(url, params=self.params, headers=self.headers, timeout=20)
        latency = round(time.time() - start_time, 2)
        
        # Observabilidad: Monitoreo de performance
        payload_size = len(response.content) / 1024  # KB
        logger.info(f"API Request: {url} | Latency: {latency}s | Size: {payload_size:.2f}KB")
        
        response.raise_for_status()
        return response.json()

    def extract(self) -> List[Dict[str, Any]]:
        """
        Orquesta la extracción y aplica validación de esquema (Schema-on-Read).
        """
        try:
            logger.info("Starting extraction from CoinGecko...")
            raw_data = self.fetch_raw_data()
            
            # Validación con Pydantic: Garantizamos la integridad del contrato de datos
            validated_data = []
            for item in raw_data:
                try:
                    # Validamos cada registro contra el esquema
                    validated_item = CryptoMarketData(**item)
                    validated_data.append(validated_item.model_dump())
                except Exception as ve:
                    logger.warning(f"Skipping malformed record (ID: {item.get('id')}): {ve}")
                    continue
            
            logger.info(f"Extraction complete: {len(validated_data)} valid records retrieved.")
            return validated_data

        except Exception as e:
            logger.error(f"Critical error during extraction: {e}")
            raise
