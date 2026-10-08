import pytest
import pandas as pd
import numpy as np

# Dummy cleaning functions
def clean_accidents_columns(df):
    df.columns = [c.lower().replace(' ', '_') for c in df.columns]
    return df

def clean_accidents_dates(df):
    df['parsed_date'] = pd.to_datetime(df['date'], format='%d/%m/%Y', errors='coerce')
    return df

def clean_accidents_severity_mapping(df):
    mapping = {1: 'Fatal', 2: 'Serious', 3: 'Slight'}
    df['severity_label'] = df['accident_severity'].map(mapping)
    return df

def clean_accidents_coordinates(df):
    df.loc[~df['latitude'].between(49, 61), 'latitude'] = np.nan
    df.loc[~df['longitude'].between(-8, 2), 'longitude'] = np.nan
    return df

def clean_accidents_duplicates(df):
    return df.drop_duplicates(subset=['accident_index'])

def clean_vehicles(df):
    return df.dropna(subset=['vehicle_type'])

def clean_casualties(df):
    return df.dropna(subset=['casualty_class'])

def get_season(month):
    if month in [12, 1, 2]: return 'Winter'
    elif month in [3, 4, 5]: return 'Spring'
    elif month in [6, 7, 8]: return 'Summer'
    else: return 'Autumn'

def is_rush_hour(hour):
    return (7 <= hour <= 9) or (16 <= hour <= 18)

def test_clean_accidents_columns(sample_accident_df):
    df = sample_accident_df.copy()
    df = df.rename(columns={'accident_index': 'Accident Index'})
    cleaned = clean_accidents_columns(df)
    assert 'accident_index' in cleaned.columns

def test_clean_accidents_dates(sample_accident_df):
    cleaned = clean_accidents_dates(sample_accident_df)
    assert pd.api.types.is_datetime64_any_dtype(cleaned['parsed_date'])

def test_clean_accidents_severity_mapping(sample_accident_df):
    cleaned = clean_accidents_severity_mapping(sample_accident_df)
    assert 'Fatal' in cleaned['severity_label'].values or 'Serious' in cleaned['severity_label'].values or 'Slight' in cleaned['severity_label'].values

def test_clean_accidents_coordinates(sample_accident_df):
    cleaned = clean_accidents_coordinates(sample_accident_df)
    assert cleaned['latitude'].isna().sum() > 0 # At least one invalid lat was injected
    assert cleaned['longitude'].isna().sum() > 0 # At least one invalid lon was injected
    assert cleaned['latitude'].max() <= 61

def test_clean_accidents_duplicates():
    df = pd.DataFrame({'accident_index': ['A1', 'A1', 'A2']})
    cleaned = clean_accidents_duplicates(df)
    assert len(cleaned) == 2

def test_clean_vehicles(sample_vehicle_df):
    df = sample_vehicle_df.copy()
    df.loc[0, 'vehicle_type'] = np.nan
    cleaned = clean_vehicles(df)
    assert len(cleaned) == len(df) - 1

def test_clean_casualties(sample_casualty_df):
    df = sample_casualty_df.copy()
    df.loc[0, 'casualty_class'] = np.nan
    cleaned = clean_casualties(df)
    assert len(cleaned) == len(df) - 1

def test_get_season():
    assert get_season(1) == 'Winter'
    assert get_season(4) == 'Spring'
    assert get_season(7) == 'Summer'
    assert get_season(10) == 'Autumn'

def test_is_rush_hour():
    assert is_rush_hour(8) == True
    assert is_rush_hour(17) == True
    assert is_rush_hour(12) == False
    assert is_rush_hour(3) == False
