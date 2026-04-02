"""Extraction module for retrieving data from CoinGecko API."""

import logging
import time
import requests
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
)
from src.config import Config
from src.schemas import CryptoMarketData

logger = logging.getLogger(__name__)


class CoinGeckoExtractor:
    """
    Extractor modular para CoinGecko con reintentos y validación.

    Nivel: Senior Data Engineering.
    """

    def __init__(self):
        """Inicializa el extractor con la configuración base."""
        self.base_url = Config.COINGECKO_BASE_URL
        self.api_key = Config.COINGECKO_API_KEY

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=10),
        retry=retry_if_exception_type(requests.exceptions.RequestException),
    )
    def _make_request(self, endpoint: str, params: dict = None) -> dict:
        """Realiza una petición HTTP con lógica de reintentos."""
        url = f"{self.base_url}/{endpoint}"
        headers = {"accept": "application/json"}
        if self.api_key:
            headers["x-cg-demo-api-key"] = self.api_key

        start_time = time.time()
        response = requests.get(
            url, headers=headers, params=params, timeout=10
        )
        latency = round(time.time() - start_time, 2)

        response.raise_for_status()
        payload_size = len(response.content) / 1024

        logger.info(
            f"API Request: {endpoint} | "
            f"Latency: {latency}s | Size: {payload_size:.2f}KB"
        )
        return response.json()

    def extract(self) -> list:
        """Extrae y valida datos de mercados de criptomonedas."""
        try:
            logger.info("Starting extraction from CoinGecko...")
            params = {
                "vs_currency": Config.DEFAULT_CURRENCY,
                "order": Config.ORDER,
                "per_page": Config.PER_PAGE,
                "page": 1,
            }

            raw_data = self._make_request("coins/markets", params=params)
            validated_data = []

            # Validación con Pydantic: Garantizamos la integridad
            for item in raw_data:
                try:
                    market_data = CryptoMarketData(**item)
                    validated_data.append(market_data.model_dump())
                except Exception as ve:
                    logger.warning(
                        f"Skipping malformed record (ID: {item.get('id')}): "
                        f"{ve}"
                    )

            logger.info(f"Extraction complete: {len(validated_data)} records.")
            return validated_data

        except Exception as e:
            logger.error(f"Extraction critical failure: {e}")
            raise
