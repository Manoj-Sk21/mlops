import pandas as pd
import numpy as np
from datetime import datetime

SEVERITY_DICT = {1: 'Fatal', 2: 'Serious', 3: 'Slight'}
ROAD_TYPE_DICT = {1: 'Roundabout', 2: 'One way street', 3: 'Dual carriageway', 6: 'Single carriageway', 7: 'Slip road', 9: 'Unknown', 12: 'One way/slip', -1: 'Missing'}
WEATHER_DICT = {1: 'Fine no high winds', 2: 'Raining no high winds', 3: 'Snowing no high winds', 4: 'Fine + high winds', 5: 'Raining + high winds', 6: 'Snowing + high winds', 7: 'Fog or mist', 8: 'Other', 9: 'Unknown', -1: 'Missing'}
ROAD_SURFACE_DICT = {1: 'Dry', 2: 'Wet or damp', 3: 'Snow', 4: 'Frost or ice', 5: 'Flood over 3cm', 6: 'Oil or diesel', 7: 'Mud', -1: 'Missing'}
LIGHT_DICT = {1: 'Daylight', 4: 'Darkness-lights lit', 5: 'Darkness-lights unlit', 6: 'Darkness-no lighting', 7: 'Darkness-lighting unknown', -1: 'Missing'}

def get_season(month: int) -> str:
    if month in [12, 1, 2]: return 'Winter'
    if month in [3, 4, 5]: return 'Spring'
    if month in [6, 7, 8]: return 'Summer'
    return 'Autumn'

def is_rush_hour(hour: int) -> bool:
    return (7 <= hour <= 9) or (16 <= hour <= 18)

def clean_accidents(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df.columns = [c.lower().strip() for c in df.columns]
    
    # Dates & Times
    df['date'] = pd.to_datetime(df['date'], format='%d/%m/%Y', errors='coerce')
    df['accident_year'] = df['date'].dt.year
    df['accident_month'] = df['date'].dt.month
    df['accident_day'] = df['date'].dt.day
    df['season'] = df['accident_month'].apply(get_season)
    df['is_weekend'] = df['date'].dt.dayofweek >= 5
    
    df['time'] = pd.to_datetime(df['time'], format='%H:%M', errors='coerce').dt.time
    df['hour'] = pd.to_datetime(df['time'], format='%H:%M', errors='coerce').dt.hour
    df['is_rush_hour'] = df['hour'].apply(lambda x: is_rush_hour(x) if pd.notnull(x) else False)
    
    # Mappings
    df['severity_label'] = df['accident_severity'].map(SEVERITY_DICT).fillna('Unknown')
    df['road_type_label'] = df['road_type'].map(ROAD_TYPE_DICT).fillna('Unknown')
    df['weather_label'] = df['weather_conditions'].map(WEATHER_DICT).fillna('Unknown')
    df['road_surface_label'] = df['road_surface_conditions'].map(ROAD_SURFACE_DICT).fillna('Unknown')
    df['light_label'] = df['light_conditions'].map(LIGHT_DICT).fillna('Unknown')
    
    df['urban_or_rural_area'] = df['urban_or_rural_area'].map({1: 'Urban', 2: 'Rural', 3: 'Unallocated'}).fillna('Unknown')
    
    # Numeric types
    df['latitude'] = pd.to_numeric(df['latitude'], errors='coerce')
    df['longitude'] = pd.to_numeric(df['longitude'], errors='coerce')
    df['latitude'] = df['latitude'].replace(-1, np.nan)
    df['longitude'] = df['longitude'].replace(-1, np.nan)
    
    df['speed_limit'] = pd.to_numeric(df['speed_limit'], errors='coerce')
    df['speed_limit'] = df['speed_limit'].replace(-1, np.nan)
    
    df['number_of_vehicles'] = pd.to_numeric(df['number_of_vehicles'], errors='coerce').fillna(1).astype(int)
    df['number_of_casualties'] = pd.to_numeric(df['number_of_casualties'], errors='coerce').fillna(1).astype(int)
    
    # Deduplicate & strip
    df = df.drop_duplicates(subset=['accident_index'])
    for col in df.select_dtypes(include=['object']).columns:
        df[col] = df[col].astype(str).str.strip()
        
    df['cleaned_at'] = datetime.now()
    return df

def clean_vehicles(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df.columns = [c.lower().strip() for c in df.columns]
    
    # Deduplicate
    df = df.drop_duplicates(subset=['accident_index', 'vehicle_reference'])
    
    df['sex_of_driver_label'] = df['sex_of_driver'].map({1: 'Male', 2: 'Female', 3: 'Not known', -1: 'Missing'}).fillna('Unknown')
    df['age_of_driver'] = pd.to_numeric(df['age_of_driver'], errors='coerce').replace(-1, np.nan)
    df['engine_capacity_cc'] = pd.to_numeric(df['engine_capacity_cc'], errors='coerce').replace(-1, np.nan)
    df['age_of_vehicle'] = pd.to_numeric(df['age_of_vehicle'], errors='coerce').replace(-1, np.nan)
    
    df['cleaned_at'] = datetime.now()
    return df

def clean_casualties(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df.columns = [c.lower().strip() for c in df.columns]
    
    # Deduplicate
    df = df.drop_duplicates(subset=['accident_index', 'vehicle_reference', 'casualty_reference'])
    
    df['casualty_class_label'] = df['casualty_class'].map({1: 'Driver/rider', 2: 'Passenger', 3: 'Pedestrian'}).fillna('Unknown')
    df['sex_of_casualty_label'] = df['sex_of_casualty'].map({1: 'Male', 2: 'Female', 9: 'Not known', -1: 'Missing'}).fillna('Unknown')
    df['age_of_casualty'] = pd.to_numeric(df['age_of_casualty'], errors='coerce').replace(-1, np.nan)
    
    df['cleaned_at'] = datetime.now()
    return df
