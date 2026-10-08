import pandas as pd
import numpy as np

def join_accident_weather(accidents_df: pd.DataFrame, weather_df: pd.DataFrame) -> pd.DataFrame:
    """Joins accident data with weather data on date and rounded coordinates."""
    df1 = accidents_df.copy()
    df2 = weather_df.copy()
    
    if df2.empty:
        # Create empty columns
        for col in ['temperature', 'precipitation', 'rain', 'snowfall', 'wind_speed', 'weather_code', 'weather_description']:
            df1[col] = np.nan
        return df1
        
    # Standardize types and formatting for merge
    df1['join_lat'] = df1['latitude'].round(2)
    df1['join_lon'] = df1['longitude'].round(2)
    df1['join_date'] = pd.to_datetime(df1['date']).dt.strftime('%Y-%m-%d')
    
    df2['join_lat'] = df2['latitude_rounded'].round(2)
    df2['join_lon'] = df2['longitude_rounded'].round(2)
    df2['join_date'] = pd.to_datetime(df2['date']).dt.strftime('%Y-%m-%d')
    
    # Merge
    merged = pd.merge(
        df1, 
        df2[['join_lat', 'join_lon', 'join_date', 'temperature', 'precipitation', 'rain', 'snowfall', 'wind_speed', 'weather_code', 'weather_description']], 
        on=['join_lat', 'join_lon', 'join_date'], 
        how='left'
    )
    
    # Drop join keys
    merged = merged.drop(columns=['join_lat', 'join_lon', 'join_date'])
    
    # Rename API specific columns
    merged = merged.rename(columns={
        'weather_code': 'weather_code_api',
        'weather_description': 'weather_description_api'
    })
    
    return merged

def calculate_match_statistics(merged_df: pd.DataFrame, original_count: int) -> dict:
    """Calculates statistics on the weather join."""
    matched = merged_df['temperature'].notna().sum()
    unmatched = original_count - matched
    match_rate = matched / original_count if original_count > 0 else 0
    
    return {
        "total_records": original_count,
        "matched_count": int(matched),
        "unmatched_count": int(unmatched),
        "match_rate": float(match_rate)
    }
