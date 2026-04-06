"""Main orchestrator for the Crypto ETL pipeline."""

import time
import logging
from pythonjsonlogger import jsonlogger
from datetime import datetime
import pandas as pd
from sqlalchemy import create_engine, Table, MetaData
from sqlalchemy.dialects.postgresql import insert

from src.config import Config
from src.extractors import CoinGeckoExtractor
from src.schemas import CryptoPriceOutput
from src.utils import check_api_health, check_db_health, GCSUploader

# --- Configuracion de Logging Estructurado (JSON) - Senior Practice ---
log_handler = logging.StreamHandler()
json_format = " ".join(
    [f"%({field})s" for field in Config.LOG_JSON_FIELDS.split(",")]
)
formatter = jsonlogger.JsonFormatter(json_format)
log_handler.setFormatter(formatter)

logging.basicConfig(level=Config.LOG_LEVEL, handlers=[log_handler])
logger = logging.getLogger(__name__)


def transform_data(validated_data: list):
    """
    TRANSFORMAR: Limpieza y validacion de calidad con Pandas.

    Implementa precision financiera (Decimal) y Schema Enforcement.
    """
    try:
        logger.info("Transforming: Processing data with Decimal precision...")

        # Ingestion de datos validados
        df = pd.DataFrame(validated_data)

        if df.empty:
            logger.warning("Transformation: Empty input received.")
            return df

        # Definicion de columnas criticas
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

        # Data Quality Check: Filtrado de precios inconsistentes
        initial_count = len(df)
        df = df[df["current_price"] > 0]

        filtered_count = initial_count - len(df)
        if filtered_count > 0:
            logger.warning(
                f"Data Quality: Filtered {filtered_count} invalid records."
            )

        # Metadatos de Trazabilidad
        df["extracted_at"] = datetime.now()

        # --- Output Schema Enforcement ---
        logger.info(
            "Validating output schema enforcement (Schema-on-Write)..."
        )
        records = df.to_dict(orient="records")

        for record in records:
            CryptoPriceOutput(**record)

        logger.info(f"Transformation complete: {len(df)} records validated.")
        return df

    except Exception as e:
        logger.error(f"Transformation failed or schema mismatch: {e}")
        raise


def load_to_warehouse(df: pd.DataFrame):
    """
    CARGAR: Ingesta en PostgreSQL con UPSERT (Idempotencia).

    Gestiona pool de conexiones y verifica integridad post-ingesta.
    """
    db_url = Config.DATABASE_URL
    if not db_url or df.empty:
        logger.warning("Loading: No data to load or DATABASE_URL missing.")
        return

    try:
        logger.info(f"Loading: Initiating Upsert for {len(df)} records...")

        # 1. Gestion de Pool de Conexiones
        engine = create_engine(
            db_url,
            pool_size=Config.DB_POOL_SIZE,
            max_overflow=Config.DB_MAX_OVERFLOW,
            pool_timeout=Config.DB_POOL_TIMEOUT,
        )

        # 2. Reflexion de tabla para insercion dinamica
        metadata = MetaData()
        table = Table("crypto_prices", metadata, autoload_with=engine)

        # 3. Preparacion de Upsert (INSERT ... ON CONFLICT DO UPDATE)
        records = df.to_dict(orient="records")

        with engine.begin() as conn:  # Transaccion atomica
            for record in records:
                stmt = insert(table).values(record)

                # Definimos columnas a actualizar (excluyendo PKs)
                update_cols = {
                    c.name: stmt.excluded[c.name]
                    for c in table.columns
                    if c.name not in ["id", "extracted_at"]
                }

                upsert_stmt = stmt.on_conflict_do_update(
                    index_elements=["id", "extracted_at"], set_=update_cols
                )
                conn.execute(upsert_stmt)

        # 4. Auditoria de Carga (Data Audit - Issue #4 Phase 2)
        with engine.connect() as conn:
            from sqlalchemy import select, func

            # Verificamos registros cargados en esta ejecucion
            latest_extraction = df["extracted_at"].max()
            audit_query = (
                select(func.count())
                .select_from(table)
                .where(table.c.extracted_at == latest_extraction)
            )

            db_count = conn.execute(audit_query).scalar()
            df_count = len(df)

            if db_count == df_count:
                logger.info(f"Audit Successful: {db_count} records verified.")
            else:
                logger.error(f"Audit Failure: DF {df_count} != DB {db_count}.")
                raise ValueError("Data Integrity Breach: Load count mismatch.")

        logger.info("Load successful: Data persisted idempotently.")

    except Exception as e:
        logger.error(f"Load failed: Database error -> {e}")
        raise


def run_pipeline():
    """Orquestador principal del ETL Pipeline."""
    start_time = time.time()
    try:
        logger.info("--- STARTING CRYPTO ETL PIPELINE ---")

        # 1. Validación de Configuración
        Config.validate()

        # 2. Infrastructure Healthchecks
        if not check_api_health():
            raise RuntimeError("Pipeline Aborted: API is unreachable.")

        engine = create_engine(Config.DATABASE_URL)
        if not check_db_health(engine):
            raise RuntimeError("Pipeline Aborted: Database is unreachable.")

        # 3. Extracción (Modular & Robusta)
        extractor = CoinGeckoExtractor()
        raw_validated_data = extractor.extract()

        # 4. Data Lake Ingestion (New Sink: GCP)
        if Config.GCP_BUCKET_NAME and Config.GCP_CREDENTIALS_PATH:
            uploader = GCSUploader(
                Config.GCP_BUCKET_NAME, Config.GCP_CREDENTIALS_PATH
            )
            blob_name = (
                f"crypto_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            )
            uploader.upload_data(raw_validated_data, blob_name)

        # 5. Transformación (Pandas)
        clean_df = transform_data(raw_validated_data)

        # 6. Carga (SQLAlchemy)
        load_to_warehouse(clean_df)

        duration = round(time.time() - start_time, 2)
        logger.info(f"--- PIPELINE COMPLETED SUCCESSFULLY IN {duration}s ---")

    except Exception as e:
        logger.critical(f"PIPELINE CRASHED: {e}")
        raise


if __name__ == "__main__":
    run_pipeline()
