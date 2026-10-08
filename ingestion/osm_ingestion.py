import time
import requests
import sqlite3
import pandas as pd
from .ingestion_utils import logger, log_ingestion, retry_with_backoff

OVERPASS_URL = "https://overpass-api.de/api/interpreter"

def _init_osm_cache(cache_db_path: str):
    conn = sqlite3.connect(cache_db_path)
    conn.execute('''
        CREATE TABLE IF NOT EXISTS osm_cache (
            lat REAL,
            lon REAL,
            road_name TEXT,
            road_type_osm TEXT,
            nearest_road_distance REAL,
            PRIMARY KEY (lat, lon)
        )
    ''')
    conn.commit()
    conn.close()

@retry_with_backoff(max_retries=2, base_delay=3)
def _query_overpass(lat: float, lon: float, radius: int = 50) -> dict:
    query = f"""
    [out:json];
    way(around:{radius},{lat},{lon})["highway"];
    out center;
    """
    response = requests.post(OVERPASS_URL, data={'data': query})
    response.raise_for_status()
    return response.json()

def fetch_road_info(latitude: float, longitude: float, cache_db_path: str) -> dict:
    """Fetches road info from Overpass API with local caching."""
    _init_osm_cache(cache_db_path)
    
    lat_r = round(latitude, 4)
    lon_r = round(longitude, 4)
    
    with sqlite3.connect(cache_db_path) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT road_name, road_type_osm, nearest_road_distance FROM osm_cache WHERE lat=? AND lon=?", (lat_r, lon_r))
        row = cursor.fetchone()
        if row:
            return {"road_name": row[0], "road_type_osm": row[1], "nearest_road_distance": row[2]}
            
    # If not in cache, query API
    try:
        data = _query_overpass(lat_r, lon_r)
        if 'elements' in data and len(data['elements']) > 0:
            element = data['elements'][0]
            tags = element.get('tags', {})
            road_name = tags.get('name', 'Unknown')
            road_type = tags.get('highway', 'Unknown')
            
            with sqlite3.connect(cache_db_path) as conn:
                conn.execute("INSERT OR REPLACE INTO osm_cache VALUES (?, ?, ?, ?, ?)",
                             (lat_r, lon_r, road_name, road_type, 0.0))
                             
            return {"road_name": road_name, "road_type_osm": road_type, "nearest_road_distance": 0.0}
    except Exception as e:
        logger.warning(f"Overpass API failed for {lat_r}, {lon_r}: {e}")
        
    return {"road_name": None, "road_type_osm": None, "nearest_road_distance": None}

def batch_fetch_road_info(locations_df: pd.DataFrame, cache_db_path: str, engine, run_id: str, demo_mode: bool = False) -> pd.DataFrame:
    """Batch fetch OSM info with rate limiting."""
    start_time = time.time()
    error_msg = ""
    status = "SUCCESS"
    
    if demo_mode:
        logger.info("Demo mode enabled for OSM ingestion. Returning empty enrichment.")
        df = locations_df.copy()
        df['road_name'] = 'Demo Road'
        df['road_type_osm'] = 'residential'
        df['nearest_road_distance'] = 10.0
        log_ingestion(engine, "osm_road_info", "API_JSON", status, len(df), "osm_cache.sqlite", "synthetic", error_msg, time.time() - start_time, run_id)
        return df
        
    results = []
    
    unique_locs = locations_df[['latitude', 'longitude']].drop_duplicates().dropna()
    
    try:
        for _, row in unique_locs.iterrows():
            info = fetch_road_info(row['latitude'], row['longitude'], cache_db_path)
            info['latitude'] = row['latitude']
            info['longitude'] = row['longitude']
            results.append(info)
            time.sleep(1.0) # Rate limit: 1 req/sec
    except Exception as e:
        status = "FAILED"
        error_msg = str(e)
        logger.error(f"Batch OSM fetch failed: {e}")
        
    res_df = pd.DataFrame(results)
    log_ingestion(engine, "osm_road_info", "API_JSON", status, len(res_df), "osm_cache.sqlite", OVERPASS_URL, error_msg, time.time() - start_time, run_id)
    return res_df
