import time
import logging
from datetime import datetime
import pandas as pd
from sqlalchemy import create_engine

from src.config import Config
from src.extractors import CoinGeckoExtractor

# --- Configuración de Logging Professional (Centralizada) ---
logging.basicConfig(
    level=Config.LOG_LEVEL,
    format=Config.LOG_FORMAT
)
logger = logging.getLogger(__name__)

def transform_data(validated_data: list):
    """
    TRANSFORMAR: Limpieza, orden y selección de columnas con Pandas.
    Recibe datos ya validados por el esquema de Pydantic.
    """
    try:
        logger.info("Transforming: Processing validated data into structured DataFrame...")
        df = pd.DataFrame(validated_data)

        # Selección de columnas críticas (Issue #3)
        cols = [
            'id', 'symbol', 'name', 'current_price', 'market_cap', 
            'market_cap_rank', 'total_volume', 'high_24h', 'low_24h', 
            'price_change_percentage_24h'
        ]
        df = df[cols]

        # Data Quality: Limpieza de valores nulos en el precio (Doble validación)
        df = df.dropna(subset=['current_price'])

        # Metadatos de Trazabilidad
        df['extracted_at'] = datetime.now()

        logger.info(f"Transformation complete: Final dataset shape {df.shape}.")
        return df

    except Exception as e:
        logger.error(f"Transformation failed: {e}")
        raise

def load_to_warehouse(df: pd.DataFrame):
    """
    CARGAR: Ingesta en PostgreSQL usando SQLAlchemy.
    """
    db_url = Config.DATABASE_URL
    if not db_url:
        logger.error("DATABASE_URL missing in configuration.")
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

def run_pipeline():
    """
    Orquestador principal del ETL Pipeline.
    """
    start_time = time.time()
    try:
        logger.info("--- STARTING CRYPTO ETL PIPELINE (MODULAR ARCHITECTURE) ---")
        
        # 1. Validación de Configuración
        Config.validate()

        # 2. Extracción (Modular & Robusta)
        extractor = CoinGeckoExtractor()
        raw_validated_data = extractor.extract()
        
        # 3. Transformación (Pandas)
        clean_df = transform_data(raw_validated_data)
        
        # 4. Carga (SQLAlchemy)
        load_to_warehouse(clean_df)
        
        duration = round(time.time() - start_time, 2)
        logger.info(f"--- PIPELINE COMPLETED SUCCESSFULLY IN {duration}s ---")

    except Exception as e:
        logger.critical(f"PIPELINE CRASHED: {e}")
        raise

if __name__ == '__main__':
    run_pipeline()
