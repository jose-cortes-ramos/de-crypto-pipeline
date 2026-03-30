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
    extracted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (id, extracted_at)
);

-- Senior Detail: Índices optimizados para Series Temporales (Time-Series)
-- 1. Índice para búsquedas rápidas por símbolo (BTC, ETH, etc.)
CREATE INDEX IF NOT EXISTS idx_crypto_symbol ON crypto_prices(symbol);

-- 2. Índice para filtros de tiempo (Series temporales: "precios de la última hora")
CREATE INDEX IF NOT EXISTS idx_crypto_extracted_at ON crypto_prices(extracted_at);

-- 3. Índice compuesto para consultas de tendencia por activo (Historial de BTC ordenado por tiempo)
CREATE INDEX IF NOT EXISTS idx_crypto_symbol_time ON crypto_prices(symbol, extracted_at DESC);
