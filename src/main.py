"""Main orchestrator for the Crypto ETL pipeline."""

import time
import logging
from pythonjsonlogger import json
from datetime import datetime
import pandas as pd
from sqlalchemy import create_engine, Table, MetaData
from sqlalchemy.dialects.postgresql import insert

from src.config import Config
from src.extractors import CoinGeckoExtractor
from src.schemas import CryptoPriceOutput, CryptoHistoricalRow
from src.utils import GCSUploader

# --- Configuracion de Logging Estructurado (JSON) ---
log_handler = logging.StreamHandler()
json_format = " ".join(
    [f"%({field})s" for field in Config.LOG_JSON_FIELDS.split(",")]
)
formatter = json.JsonFormatter(json_format)
log_handler.setFormatter(formatter)

logging.basicConfig(level=Config.LOG_LEVEL, handlers=[log_handler])
logger = logging.getLogger(__name__)


def transform_real_time_data(validated_data: list) -> pd.DataFrame:
    """TRANSFORMAR: Limpieza y validacion de calidad para snapshots."""
    try:
        logger.info("Transforming: Processing real-time market data...")
        df = pd.DataFrame(validated_data)
        if df.empty:
            return df

        cols = [
            "id",
            "symbol",
            "name",
            "current_price",
            "market_cap",
            "market_cap_rank",
            "total_volume",
            "high_24h",
            "low_24h",
            "price_change_percentage_24h",
        ]
        df = df[cols]
        df = df[df["current_price"] > 0]
        df["extracted_at"] = datetime.now()

        for record in df.to_dict(orient="records"):
            CryptoPriceOutput(**record)

        return df
    except Exception as e:
        logger.error(f"Real-time transformation failed: {e}")
        raise


def transform_historical_data(
    raw_historical: dict, coin_id: str
) -> pd.DataFrame:
    """TRANSFORMAR: Aplanado de datos historicos."""
    try:
        logger.info(f"Transforming: Flattening history for {coin_id}...")
        df_p = pd.DataFrame(raw_historical["prices"], columns=["ts", "price"])
        df_c = pd.DataFrame(
            raw_historical["market_caps"], columns=["ts", "market_cap"]
        )
        df_v = pd.DataFrame(
            raw_historical["total_volumes"], columns=["ts", "total_volume"]
        )

        df = df_p.merge(df_c, on="ts").merge(df_v, on="ts")
        df["coin_id"] = coin_id
        df["timestamp"] = pd.to_datetime(df["ts"], unit="ms")
        df = df.drop(columns=["ts"])

        for record in df.to_dict(orient="records"):
            CryptoHistoricalRow(**record)

        return df
    except Exception as e:
        logger.error(f"Historical transformation failed for {coin_id}: {e}")
        raise


def load_to_warehouse(df: pd.DataFrame, table_name: str, pk_cols: list):
    """Carga generica con estrategia de UPSERT."""
    if not Config.DATABASE_URL or df.empty:
        return

    try:
        logger.info(
            f"Loading: UPSERT into {table_name} ({len(df)} records)..."
        )
        engine = create_engine(Config.DATABASE_URL)
        metadata = MetaData()
        table = Table(table_name, metadata, autoload_with=engine)

        with engine.begin() as conn:
            for record in df.to_dict(orient="records"):
                stmt = insert(table).values(record)
                update_cols = {
                    c.name: stmt.excluded[c.name]
                    for c in table.columns
                    if c.name not in pk_cols
                }
                conn.execute(
                    stmt.on_conflict_do_update(
                        index_elements=pk_cols, set_=update_cols
                    )
                )
        logger.info(f"Load successful for {table_name}.")
    except Exception as e:
        logger.error(f"Load failed for {table_name}: {e}")
        raise


def run_pipeline():
    """Orquestador Hibrido: Real-Time + Historical."""
    start_time = time.time()
    try:
        logger.info("--- STARTING HYBRID CRYPTO PIPELINE ---")
        Config.validate()
        extractor = CoinGeckoExtractor()

        # 1. FASE TIEMPO REAL (50 Monedas)
        logger.info("PHASE 1: Real-Time Snapshots")
        raw_rt = extractor.extract()

        # Cloud Persistence (Data Lake - Snapshot)
        if Config.GCP_BUCKET_NAME and Config.GCP_CREDENTIALS_PATH:
            uploader = GCSUploader(
                Config.GCP_BUCKET_NAME, Config.GCP_CREDENTIALS_PATH
            )
            ts_now = datetime.now().strftime("%Y%m%d_%H%M%S")
            blob_name = f"snapshots/crypto_market_{ts_now}.json"
            uploader.upload_data(raw_rt, blob_name)

        clean_rt = transform_real_time_data(raw_rt)
        load_to_warehouse(clean_rt, "crypto_prices", ["id", "extracted_at"])

        # 2. FASE HISTORICA (Top 5 Monedas)
        logger.info("PHASE 2: Historical Backfill")
        for asset in Config.ANALYTICS_ASSETS:
            raw_h = extractor.extract_historical(
                asset, days=Config.HISTORICAL_DAYS
            )

            if Config.GCP_BUCKET_NAME and Config.GCP_CREDENTIALS_PATH:
                uploader = GCSUploader(
                    Config.GCP_BUCKET_NAME, Config.GCP_CREDENTIALS_PATH
                )
                ts_now = datetime.now().strftime("%Y%m%d")
                blob_name = f"historical/{asset}_{ts_now}.json"
                uploader.upload_data(raw_h, blob_name)

            clean_h = transform_historical_data(raw_h, asset)
            load_to_warehouse(
                clean_h, "crypto_historical_daily", ["coin_id", "timestamp"]
            )

            logger.info(f"Cooling down 30s after {asset}...")
            time.sleep(30)

        duration = round(time.time() - start_time, 2)
        logger.info(f"--- PIPELINE COMPLETED IN {duration}s ---")

    except Exception as e:
        logger.critical(f"PIPELINE CRASHED: {e}")
        raise


if __name__ == "__main__":
    run_pipeline()
