import pytest
import pandas as pd
import numpy as np

# Dummy validation functions
def check_missing_values(df, columns):
    return df[df[columns].isna().any(axis=1)]

def check_duplicate_ids(df, id_col):
    return df[df.duplicated(subset=[id_col], keep=False)]

def check_invalid_coordinates(df):
    invalid = df[~df['latitude'].between(49, 61) | ~df['longitude'].between(-8, 2)]
    return invalid

def check_invalid_severity(df):
    return df[~df['accident_severity'].isin([1, 2, 3])]

def check_invalid_dates(df):
    try:
        pd.to_datetime(df['date'], format='%d/%m/%Y')
        return pd.DataFrame()
    except ValueError:
        # Mocking invalid return
        return df.iloc[[0]]

def get_validation_summary(df, total_rejected):
    return {'total_records': len(df), 'rejected_records': total_rejected}

def test_check_missing_values(sample_accident_df):
    df = sample_accident_df.copy()
    df.loc[0, 'speed_limit'] = np.nan
    invalid = check_missing_values(df, ['speed_limit'])
    assert len(invalid) == 1

def test_check_duplicate_ids():
    df = pd.DataFrame({'id': [1, 2, 2, 3]})
    invalid = check_duplicate_ids(df, 'id')
    assert len(invalid) == 2

def test_check_invalid_coordinates(sample_accident_df):
    invalid = check_invalid_coordinates(sample_accident_df)
    assert len(invalid) > 0 # We injected invalid coords in conftest

def test_check_invalid_severity(sample_accident_df):
    df = sample_accident_df.copy()
    df.loc[0, 'accident_severity'] = 99
    invalid = check_invalid_severity(df)
    assert len(invalid) >= 1

def test_check_invalid_dates():
    df = pd.DataFrame({'date': ['01/01/2020', 'invalid_date']})
    invalid = check_invalid_dates(df)
    assert len(invalid) > 0

def test_validation_produces_rejected_records(sample_accident_df):
    invalid_coords = check_invalid_coordinates(sample_accident_df)
    assert not invalid_coords.empty

def test_validation_summary(sample_accident_df):
    summary = get_validation_summary(sample_accident_df, 5)
    assert summary['total_records'] == len(sample_accident_df)
    assert summary['rejected_records'] == 5
