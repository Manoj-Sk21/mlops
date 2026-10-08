import time
import requests
import sqlite3
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from .ingestion_utils import logger, log_ingestion, retry_with_backoff

OPEN_METEO_URL = "https://archive-api.open-meteo.com/v1/archive"

WEATHER_CODE_MAPPING = {
    0: "Clear sky",
    1: "Mainly clear",
    2: "Partly cloudy",
    3: "Overcast",
    45: "Fog",
    48: "Depositing rime fog",
    51: "Light drizzle",
    53: "Moderate drizzle",
    55: "Dense drizzle",
    56: "Light freezing drizzle",
    57: "Dense freezing drizzle",
    61: "Slight rain",
    63: "Moderate rain",
    65: "Heavy rain",
    66: "Light freezing rain",
    67: "Heavy freezing rain",
    71: "Slight snow fall",
    73: "Moderate snow fall",
    75: "Heavy snow fall",
    77: "Snow grains",
    80: "Slight rain showers",
    81: "Moderate rain showers",
    82: "Violent rain showers",
    85: "Slight snow showers",
    86: "Heavy snow showers",
    95: "Thunderstorm",
    96: "Thunderstorm with slight hail",
    99: "Thunderstorm with heavy hail"
}

def get_weather_description(code: int) -> str:
    """Map WMO weather codes to descriptions."""
    return WEATHER_CODE_MAPPING.get(code, "Unknown")

def _init_cache_db(cache_db_path: str):
    """Initializes the SQLite cache database for weather data."""
    conn = sqlite3.connect(cache_db_path)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS weather_cache (
            lat REAL,
            lon REAL,
            date TEXT,
            temperature REAL,
            precipitation REAL,
            rain REAL,
            snowfall REAL,
            wind_speed REAL,
            weather_code INTEGER,
            PRIMARY KEY (lat, lon, date)
        )
    ''')
    conn.commit()
    conn.close()

@retry_with_backoff(max_retries=3, base_delay=2)
def _fetch_from_api(lat: float, lon: float, start_date: str, end_date: str) -> dict:
    params = {
        "latitude": lat,
        "longitude": lon,
        "start_date": start_date,
        "end_date": end_date,
        "daily": "weathercode,temperature_2m_max,temperature_2m_min,precipitation_sum,rain_sum,snowfall_sum,windspeed_10m_max",
        "timezone": "auto"
    }
    response = requests.get(OPEN_METEO_URL, params=params)
    response.raise_for_status()
    return response.json()

def fetch_weather_for_locations(locations_df: pd.DataFrame, cache_db_path: str, engine, run_id: str, demo_mode: bool = False) -> pd.DataFrame:
    """Fetches weather data for unique locations/dates using Open-Meteo API and a local SQLite cache."""
    start_time = time.time()
    error_msg = ""
    status = "SUCCESS"
    
    if demo_mode:
        logger.info("Demo mode enabled. Generating synthetic weather data.")
        # Generate some synthetic weather mapping directly to the input locations
        df = locations_df.copy()
        df['temperature'] = np.random.uniform(-5.0, 30.0, len(df))
        df['precipitation'] = np.random.uniform(0.0, 20.0, len(df))
        df['rain'] = df['precipitation'] * 0.8
        df['snowfall'] = df['precipitation'] * 0.2
        df['wind_speed'] = np.random.uniform(0.0, 100.0, len(df))
        df['weather_code'] = np.random.choice(list(WEATHER_CODE_MAPPING.keys()), len(df))
        df['weather_description'] = df['weather_code'].apply(get_weather_description)
        
        duration = time.time() - start_time
        log_ingestion(engine, "open_meteo_weather", "API_JSON", status, len(df), "weather_synthetic", "synthetic", error_msg, duration, run_id)
        return df
    
    _init_cache_db(cache_db_path)
    
    # Pre-process locations to round coords
    locations = locations_df[['latitude', 'longitude', 'date']].dropna().copy()
    locations['lat_rounded'] = locations['latitude'].round(2)
    locations['lon_rounded'] = locations['longitude'].round(2)
    
    # Get unique combo to fetch
    unique_requests = locations[['lat_rounded', 'lon_rounded', 'date']].drop_duplicates()
    
    results = []
    conn = sqlite3.connect(cache_db_path)
    
    try:
        # We can fetch date ranges per location to minimize API calls, but for simplicity we fetch per unique loc/date
        # Or better, group by lat/lon and get min/max date
        grouped = unique_requests.groupby(['lat_rounded', 'lon_rounded'])
        
        for (lat, lon), group in grouped:
            min_date = group['date'].min()
            max_date = group['date'].max()
            
            # Check cache first (simplification: assume if min and max exist, we might have it all. Better to fetch if any missing)
            # Fetch from API
            try:
                data = _fetch_from_api(lat, lon, min_date, max_date)
                if 'daily' in data:
                    daily = data['daily']
                    for i, d in enumerate(daily['time']):
                        temp = (daily['temperature_2m_max'][i] + daily['temperature_2m_min'][i]) / 2 if daily['temperature_2m_max'][i] is not None else None
                        res_dict = {
                            "lat": lat,
                            "lon": lon,
                            "date": d,
                            "temperature": temp,
                            "precipitation": daily['precipitation_sum'][i],
                            "rain": daily['rain_sum'][i],
                            "snowfall": daily['snowfall_sum'][i],
                            "wind_speed": daily['windspeed_10m_max'][i],
                            "weather_code": daily['weathercode'][i]
                        }
                        results.append(res_dict)
                        # Insert to cache
                        conn.execute('''
                            INSERT OR IGNORE INTO weather_cache 
                            (lat, lon, date, temperature, precipitation, rain, snowfall, wind_speed, weather_code)
                            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                        ''', (lat, lon, d, temp, daily['precipitation_sum'][i], daily['rain_sum'][i], daily['snowfall_sum'][i], daily['windspeed_10m_max'][i], daily['weathercode'][i]))
                conn.commit()
                time.sleep(0.1) # Be nice to the API
            except Exception as e:
                logger.error(f"Error fetching weather for ({lat}, {lon}): {e}")
                
    except Exception as e:
        status = "FAILED"
        error_msg = str(e)
        logger.error(f"Weather ingestion failed: {e}")
    finally:
        conn.close()
        
    weather_df = pd.DataFrame(results)
    if not weather_df.empty:
        weather_df['weather_description'] = weather_df['weather_code'].apply(get_weather_description)
        # Rename for merging later
        weather_df = weather_df.rename(columns={"lat": "latitude_rounded", "lon": "longitude_rounded"})
    
    duration = time.time() - start_time
    log_ingestion(engine, "open_meteo_weather", "API_JSON", status, len(weather_df), "weather_cache.sqlite", OPEN_METEO_URL, error_msg, duration, run_id)
    
    return weather_df
