import os
import requests
import pandas as pd
from sqlalchemy import create_engine
from datetime import datetime
import logging
import time
from dotenv import load_dotenv

# --- Configuración de Logging Professional ---
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Cargamos variables de entorno
load_dotenv()


def extract_market_data():
    """
    EXTRAER: Consume la API de CoinGecko con manejo de errores y reintentos.
    """
    url = "https://api.coingecko.com/api/v3/coins/markets"
    params = {
        "vs_currency": "usd",
        "order": "market_cap_desc",
        "per_page": 50,
        "page": 1,
        "sparkline": False
    }
    
    try:
        logger.info("Extracting: Connecting to CoinGecko API...")
        response = requests.get(url, params=params, timeout=20)
        
        # Manejo de Rate Limiting (Error 429)
        if response.status_code == 429:
            logger.warning("Rate Limit reached. Retrying in 30 seconds...")
            time.sleep(30)
            return extract_market_data()
            
        response.raise_for_status()
        data = response.json()
        logger.info(f"Extraction successful: {len(data)} records retrieved.")
        return data

    except requests.exceptions.RequestException as e:
        logger.error(f"Extraction failed: Network or API error -> {e}")
        raise

def transform_data(raw_data):
    """
    TRANSFORMAR: Limpieza, orden y selección de columnas con Pandas.
    """
    try:
        logger.info("Transforming: Processing raw JSON into structured DataFrame...")
        df = pd.DataFrame(raw_data)

        # Selección de columnas críticas (Issue #3)
        cols = [
            'id', 'symbol', 'name', 'current_price', 'market_cap', 
            'market_cap_rank', 'total_volume', 'high_24h', 'low_24h', 
            'price_change_percentage_24h'
        ]
        df = df[cols]

        # Data Quality: Limpieza de valores nulos en el precio
        df = df.dropna(subset=['current_price'])

        # Metadatos de Trazabilidad
        df['extracted_at'] = datetime.now()

        logger.info(f"Transformation complete: Final dataset shape {df.shape}.")
        return df

    except Exception as e:
        logger.error(f"Transformation failed: {e}")
        raise

def load_to_warehouse(df):
    """
    CARGAR: Ingesta en PostgreSQL usando SQLAlchemy.
    """
    db_url = os.getenv("DATABASE_URL")
    if not db_url:
        logger.error("DATABASE_URL missing in .env configuration.")
        return

    try:
        logger.info("Loading: Initiating database ingestion...")
        engine = create_engine(db_url)
        
        # 'append' permite crear un histórico de precios (Serie Temporal)
        df.to_sql('crypto_prices', engine, if_exists='append', index=False)
        logger.info("Load successful: Data persisted in PostgreSQL warehouse.")

    except Exception as e:
        logger.error(f"Load failed: Database connection or insertion error -> {e}")
        raise

if __name__ == '__main__':
    start_time = time.time()
    try:
        logger.info("--- STARTING CRYPTO ETL PIPELINE ---")
        
        # Pipeline Flow
        raw = extract_market_data()
        clean = transform_data(raw)
        load_to_warehouse(clean)
        
        duration = round(time.time() - start_time, 2)
        logger.info(f"--- PIPELINE COMPLETED SUCCESSFULLY IN {duration}s ---")

    except Exception:
        logger.critical("PIPELINE CRASHED: Check logs for details.")
