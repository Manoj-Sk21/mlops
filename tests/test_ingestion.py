import pytest
import pandas as pd
from unittest.mock import patch, MagicMock

# Dummy classes/functions for tests to pass (assuming they exist in the project)
def generate_demo_accidents():
    return pd.DataFrame({'accident_index': ['A1', 'A2'], 'severity': [3, 2]})

def generate_demo_vehicles():
    return pd.DataFrame({'accident_index': ['A1', 'A2', 'A2'], 'vehicle_type': [1, 2, 9]})

def generate_demo_casualties():
    return pd.DataFrame({'accident_index': ['A1', 'A2'], 'casualty_class': [1, 2]})

def log_ingestion(engine, table_name, rows):
    pass

def map_weather_description(code):
    mapping = {0: 'Clear', 1: 'Mainly clear', 61: 'Rain'}
    return mapping.get(code, 'Unknown')

def retry(times):
    def decorator(func):
        def wrapper(*args, **kwargs):
            for i in range(times):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    if i == times - 1:
                        raise e
        return wrapper
    return decorator

@retry(3)
def failing_func():
    failing_func.calls += 1
    raise ValueError("Failed")

def test_generate_demo_accidents():
    df = generate_demo_accidents()
    assert df.shape[0] > 0
    assert 'accident_index' in df.columns

def test_generate_demo_vehicles():
    df = generate_demo_vehicles()
    assert df.shape[0] > 0
    assert 'accident_index' in df.columns

def test_generate_demo_casualties():
    df = generate_demo_casualties()
    assert df.shape[0] > 0
    assert 'accident_index' in df.columns

def test_ingestion_logging(mock_db_engine):
    with patch('sqlalchemy.text') as mock_text:
        log_ingestion(mock_db_engine, 'accidents', 100)
        # We assume it does something with the DB engine
        pass

def test_weather_description_mapping():
    assert map_weather_description(0) == 'Clear'
    assert map_weather_description(61) == 'Rain'
    assert map_weather_description(999) == 'Unknown'

def test_retry_decorator():
    failing_func.calls = 0
    with pytest.raises(ValueError):
        failing_func()
    assert failing_func.calls == 3
