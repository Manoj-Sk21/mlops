import pytest
import pandas as pd
import numpy as np
from unittest.mock import MagicMock

@pytest.fixture
def sample_accident_df():
    data = {
        'accident_index': [f'ACC{i:04d}' for i in range(20)],
        'location_easting_osgr': np.random.uniform(400000, 600000, 20),
        'location_northing_osgr': np.random.uniform(100000, 600000, 20),
        'longitude': np.random.uniform(-8, 2, 20),
        'latitude': np.random.uniform(49, 61, 20),
        'accident_severity': np.random.choice([1, 2, 3], 20, p=[0.05, 0.15, 0.8]),
        'number_of_vehicles': np.random.randint(1, 5, 20),
        'number_of_casualties': np.random.randint(1, 4, 20),
        'date': pd.date_range('2022-01-01', periods=20).strftime('%d/%m/%Y'),
        'time': [f"{np.random.randint(0,24):02d}:{np.random.randint(0,60):02d}" for _ in range(20)],
        'road_type': np.random.choice([1, 2, 3, 6, 9], 20),
        'speed_limit': np.random.choice([20, 30, 40, 50, 60, 70], 20),
        'weather_conditions': np.random.choice([1, 2, 3, 4, 5, 6, 7, 8, 9], 20)
    }
    # Inject some invalid data
    data['latitude'][0] = 90.0
    data['longitude'][1] = -10.0
    
    return pd.DataFrame(data)

@pytest.fixture
def sample_vehicle_df():
    data = {
        'accident_index': [f'ACC{i//2:04d}' for i in range(30)],
        'vehicle_reference': [i%2 + 1 for i in range(30)],
        'vehicle_type': np.random.choice([1, 2, 9, 11, 19], 30)
    }
    return pd.DataFrame(data)

@pytest.fixture
def sample_casualty_df():
    data = {
        'accident_index': [f'ACC{i//2:04d}' for i in range(25)],
        'casualty_reference': [i%2 + 1 for i in range(25)],
        'casualty_class': np.random.choice([1, 2, 3], 25),
        'casualty_severity': np.random.choice([1, 2, 3], 25)
    }
    return pd.DataFrame(data)

@pytest.fixture
def sample_weather_df():
    data = {
        'date': pd.date_range('2022-01-01', periods=10).strftime('%Y-%m-%d'),
        'wmo_code': np.random.choice([0, 1, 2, 3, 45, 51, 61, 71, 95], 10),
        'temperature_max': np.random.uniform(0, 30, 10),
        'precipitation_sum': np.random.uniform(0, 10, 10)
    }
    return pd.DataFrame(data)

@pytest.fixture
def sample_model_ready_df():
    data = {
        'id': [f'ID{i}' for i in range(50)],
        'latitude': np.random.uniform(50, 55, 50),
        'longitude': np.random.uniform(-3, 1, 50),
        'speed_limit': np.random.choice([30, 40, 50, 70], 50),
        'number_of_vehicles': np.random.randint(1, 4, 50),
        'number_of_casualties': np.random.randint(1, 3, 50),
        'severity': np.random.choice([1, 2, 3], 50),
        'road_type': np.random.choice(['Single carriageway', 'Dual carriageway', 'Roundabout'], 50),
        'weather_condition': np.random.choice(['Fine no high winds', 'Raining no high winds', 'Snowing no high winds'], 50)
    }
    return pd.DataFrame(data)

@pytest.fixture
def mock_db_engine():
    mock = MagicMock()
    mock.begin.return_value.__enter__.return_value = MagicMock()
    mock.connect.return_value.__enter__.return_value = MagicMock()
    return mock

@pytest.fixture
def sample_prediction_input():
    return {
        'latitude': 51.5074,
        'longitude': -0.1278,
        'speed_limit': 30,
        'number_of_vehicles': 2,
        'number_of_casualties': 1,
        'date': '2023-10-15',
        'time': '14:30',
        'road_type': 'Single carriageway',
        'weather_condition': 'Fine no high winds'
    }
