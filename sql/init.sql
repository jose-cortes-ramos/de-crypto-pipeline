-- 1. Tabla de Precios en Tiempo Real (Snapshot Actual)
-- Utilizada para monitoreo inmediato y alertas.
CREATE TABLE IF NOT EXISTS crypto_prices (
    id VARCHAR(50) NOT NULL,
    symbol VARCHAR(10) NOT NULL,
    name VARCHAR(100) NOT NULL,
    current_price DECIMAL(18, 8) NOT NULL,
    market_cap BIGINT,
    market_cap_rank INT,
    total_volume BIGINT,
    high_24h DECIMAL(18, 8),
    low_24h DECIMAL(18, 8),
    price_change_percentage_24h DECIMAL(10, 5),
    extracted_at TIMESTAMP NOT NULL, -- Controlado desde Python para consistencia Data Lake/DW
    PRIMARY KEY (id, extracted_at)
);

-- 2. Tabla de Hechos Históricos (Issue #7)
-- Optimizada para analítica de tendencias y series temporales de largo plazo.
CREATE TABLE IF NOT EXISTS crypto_historical_daily (
    coin_id VARCHAR(50) NOT NULL,
    timestamp TIMESTAMP NOT NULL,
    price DECIMAL(18, 8) NOT NULL,
    market_cap DECIMAL(24, 2), -- Soporta valores en el rango de los trillones
    total_volume DECIMAL(24, 2),
    PRIMARY KEY (coin_id, timestamp)
);

-- 3. Índices de Rendimiento para Analítica (BI Optimization)
-- Aceleran filtros por fecha y búsquedas de tendencias por activo.
CREATE INDEX IF NOT EXISTS idx_hist_timestamp ON crypto_historical_daily(timestamp);
CREATE INDEX IF NOT EXISTS idx_hist_coin_time ON crypto_historical_daily(coin_id, timestamp DESC);

-- Índices de la tabla de snapshots
CREATE INDEX IF NOT EXISTS idx_crypto_extracted_at ON crypto_prices(extracted_at);
CREATE INDEX IF NOT EXISTS idx_crypto_symbol_time ON crypto_prices(symbol, extracted_at DESC);
