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
