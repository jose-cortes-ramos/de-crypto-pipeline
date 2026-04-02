import pytest
import pandas as pd
from decimal import Decimal
from datetime import datetime
from src.main import transform_data

def test_transform_data_decimal_precision():
    """
    Test para asegurar que la transformacion mantiene la precision de Decimal.
    """
    # Datos de entrada simulados (Ya validados por Pydantic)
    validated_data = [
        {
            'id': 'bitcoin', 'symbol': 'btc', 'name': 'Bitcoin', 
            'current_price': Decimal('65000.12345678'), 'market_cap': Decimal('1200000000'),
            'market_cap_rank': 1, 'total_volume': Decimal('30000000000'),
            'high_24h': Decimal('66000'), 'low_24h': Decimal('64000'),
            'price_change_percentage_24h': Decimal('1.5')
        }
    ]
    
    df = transform_data(validated_data)
    
    # Verificacion de tipo y precision
    assert isinstance(df['current_price'][0], Decimal)
    assert df['current_price'][0] == Decimal('65000.12345678')
    assert 'extracted_at' in df.columns

def test_transform_data_quality_filter():
    """
    Test para asegurar que los filtros de calidad eliminan precios invalidos.
    """
    validated_data = [
        # Registro Valido
        {
            'id': 'bitcoin', 'symbol': 'btc', 'name': 'Bitcoin', 
            'current_price': Decimal('60000'), 'market_cap': Decimal('1000'),
            'market_cap_rank': 1, 'total_volume': Decimal('5000'),
            'high_24h': Decimal('61000'), 'low_24h': Decimal('59000'),
            'price_change_percentage_24h': Decimal('0.5')
        },
        # Registro Invalido (Precio 0)
        {
            'id': 'scam-coin', 'symbol': 'scam', 'name': 'Scam Coin', 
            'current_price': Decimal('0'), 'market_cap': Decimal('0'),
            'market_cap_rank': 999, 'total_volume': Decimal('0'),
            'high_24h': Decimal('0'), 'low_24h': Decimal('0'),
            'price_change_percentage_24h': Decimal('0')
        }
    ]
    
    df = transform_data(validated_data)
    
    # Deberia haber filtrado el registro con precio 0
    assert len(df) == 1
    assert df['id'][0] == 'bitcoin'

def test_transform_data_empty_input():
    """
    Test para asegurar que el pipeline maneja entradas vacias sin fallar.
    """
    df = transform_data([])
    assert isinstance(df, pd.DataFrame)
    assert len(df) == 0

def test_transform_data_optional_fields_none():
    """
    Test para asegurar que los campos opcionales (None) se manejan correctamente.
    Nivel: Senior Resilience.
    """
    validated_data = [
        {
            'id': 'new-coin', 'symbol': 'new', 'name': 'New Coin', 
            'current_price': Decimal('0.5'), 'market_cap': Decimal('100'),
            'market_cap_rank': 500, 'total_volume': Decimal('200'),
            'high_24h': None,  # Campo opcional nulo
            'low_24h': None,   # Campo opcional nulo
            'price_change_percentage_24h': None
        }
    ]
    
    df = transform_data(validated_data)
    
    assert len(df) == 1
    assert pd.isna(df['high_24h'][0])
    assert df['id'][0] == 'new-coin'

def test_transform_data_extreme_precision():
    """
    Test para asegurar precision en micro-cap coins (0.00000001).
    Nivel: Senior Precision.
    """
    micro_price = Decimal('0.00000001234567')
    validated_data = [
        {
            'id': 'micro-coin', 'symbol': 'micro', 'name': 'Micro Coin', 
            'current_price': micro_price, 'market_cap': Decimal('10'),
            'market_cap_rank': 5000, 'total_volume': Decimal('5'),
            'high_24h': micro_price, 'low_24h': micro_price,
            'price_change_percentage_24h': Decimal('0.1')
        }
    ]
    
    df = transform_data(validated_data)
    
    assert df['current_price'][0] == micro_price
    assert isinstance(df['current_price'][0], Decimal)

def test_transform_data_schema_mismatch_failure():
    """
    Test para validar que la transformacion falla (Fail-Fast) si el esquema es invalido.
    Nivel: Senior Data Contract Enforcement.
    """
    # Dato malformado que paso el extractor (simulado)
    malformed_data = [
        {
            'id': 'error-coin',
            'current_price': 'NOT_A_DECIMAL' # Esto deberia causar error de Pydantic en transform_data
        }
    ]
    
    with pytest.raises(Exception):
        transform_data(malformed_data)
