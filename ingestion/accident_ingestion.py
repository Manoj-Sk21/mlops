import os
import time
import requests
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from .ingestion_utils import logger, log_ingestion, retry_with_backoff

ACCIDENTS_URL = "https://data.dft.gov.uk/road-accidents-safety-data/dft-road-casualty-statistics-accident-last-5-years.csv"
VEHICLES_URL = "https://data.dft.gov.uk/road-accidents-safety-data/dft-road-casualty-statistics-vehicle-last-5-years.csv"
CASUALTIES_URL = "https://data.dft.gov.uk/road-accidents-safety-data/dft-road-casualty-statistics-casualty-last-5-years.csv"

@retry_with_backoff(max_retries=3, base_delay=2)
def _download_csv(url: str) -> pd.DataFrame:
    """Helper to download CSV from URL into a pandas DataFrame."""
    logger.info(f"Downloading data from {url}")
    return pd.read_csv(url, low_memory=False)

def download_accident_data(data_dir: str, engine, run_id: str, demo_mode: bool = False) -> pd.DataFrame:
    """Downloads accident data or generates demo data if demo_mode is True."""
    start_time = time.time()
    error_msg = ""
    status = "SUCCESS"
    df = pd.DataFrame()
    filename = "accidents_latest.csv"
    
    try:
        if demo_mode:
            logger.info("Demo mode enabled. Generating synthetic accidents data.")
            df = generate_demo_accidents(n=1000)
            filename = "demo_accidents.csv"
        else:
            df = _download_csv(ACCIDENTS_URL)
            filename = f"accidents_{datetime.now().year}.csv"
            
        file_path = os.path.join(data_dir, filename)
        df.to_csv(file_path, index=False)
        logger.info(f"Saved accident data to {file_path} ({len(df)} rows)")
        
    except Exception as e:
        status = "FAILED"
        error_msg = str(e)
        logger.error(f"Failed to download accident data: {e}")
        raise
    finally:
        duration = time.time() - start_time
        log_ingestion(engine, "uk_road_safety_accidents", "API_CSV", status, len(df), filename, ACCIDENTS_URL if not demo_mode else "synthetic", error_msg, duration, run_id)
        
    return df

def download_vehicle_data(data_dir: str, engine, run_id: str, demo_mode: bool = False) -> pd.DataFrame:
    """Downloads vehicle data or generates demo data if demo_mode is True."""
    start_time = time.time()
    error_msg = ""
    status = "SUCCESS"
    df = pd.DataFrame()
    filename = "vehicles_latest.csv"
    
    try:
        if demo_mode:
            logger.info("Demo mode enabled. Generating synthetic vehicle data.")
            # Retrieve accident indices from demo_accidents if exists, otherwise generate some
            accident_file = os.path.join(data_dir, "demo_accidents.csv")
            if os.path.exists(accident_file):
                acc_df = pd.read_csv(accident_file)
                indices = acc_df['accident_index'].tolist()
            else:
                indices = [f"DEMO_{i}" for i in range(1000)]
            df = generate_demo_vehicles(indices, n_per_accident=2)
            filename = "demo_vehicles.csv"
        else:
            df = _download_csv(VEHICLES_URL)
            filename = f"vehicles_{datetime.now().year}.csv"
            
        file_path = os.path.join(data_dir, filename)
        df.to_csv(file_path, index=False)
        logger.info(f"Saved vehicle data to {file_path} ({len(df)} rows)")
        
    except Exception as e:
        status = "FAILED"
        error_msg = str(e)
        logger.error(f"Failed to download vehicle data: {e}")
        raise
    finally:
        duration = time.time() - start_time
        log_ingestion(engine, "uk_road_safety_vehicles", "API_CSV", status, len(df), filename, VEHICLES_URL if not demo_mode else "synthetic", error_msg, duration, run_id)
        
    return df

def download_casualty_data(data_dir: str, engine, run_id: str, demo_mode: bool = False) -> pd.DataFrame:
    """Downloads casualty data or generates demo data if demo_mode is True."""
    start_time = time.time()
    error_msg = ""
    status = "SUCCESS"
    df = pd.DataFrame()
    filename = "casualties_latest.csv"
    
    try:
        if demo_mode:
            logger.info("Demo mode enabled. Generating synthetic casualty data.")
            accident_file = os.path.join(data_dir, "demo_accidents.csv")
            if os.path.exists(accident_file):
                acc_df = pd.read_csv(accident_file)
                indices = acc_df['accident_index'].tolist()
            else:
                indices = [f"DEMO_{i}" for i in range(1000)]
            df = generate_demo_casualties(indices, n_per_accident=1.5)
            filename = "demo_casualties.csv"
        else:
            df = _download_csv(CASUALTIES_URL)
            filename = f"casualties_{datetime.now().year}.csv"
            
        file_path = os.path.join(data_dir, filename)
        df.to_csv(file_path, index=False)
        logger.info(f"Saved casualty data to {file_path} ({len(df)} rows)")
        
    except Exception as e:
        status = "FAILED"
        error_msg = str(e)
        logger.error(f"Failed to download casualty data: {e}")
        raise
    finally:
        duration = time.time() - start_time
        log_ingestion(engine, "uk_road_safety_casualties", "API_CSV", status, len(df), filename, CASUALTIES_URL if not demo_mode else "synthetic", error_msg, duration, run_id)
        
    return df


def generate_demo_accidents(n: int = 1000) -> pd.DataFrame:
    """Creates realistic synthetic accident data."""
    np.random.seed(42)
    indices = [f"DEMO_{str(i).zfill(6)}" for i in range(n)]
    dates = [datetime(2023, 1, 1) + timedelta(days=np.random.randint(0, 365)) for _ in range(n)]
    
    severity_choices = [1, 2, 3]
    severity_probs = [0.03, 0.15, 0.82]
    
    return pd.DataFrame({
        "accident_index": indices,
        "accident_year": [d.year for d in dates],
        "accident_severity": np.random.choice(severity_choices, n, p=severity_probs),
        "number_of_vehicles": np.random.randint(1, 5, n),
        "number_of_casualties": np.random.randint(1, 4, n),
        "date": [d.strftime("%d/%m/%Y") for d in dates],
        "day_of_week": [d.isoweekday() for d in dates],
        "time": [f"{str(np.random.randint(0, 24)).zfill(2)}:{str(np.random.randint(0, 60)).zfill(2)}" for _ in range(n)],
        "latitude": np.random.uniform(50.0, 58.0, n),
        "longitude": np.random.uniform(-5.0, 1.5, n),
        "local_authority_district": np.random.randint(1, 400, n),
        "local_authority_highway": ["E" + str(np.random.randint(10000000, 99999999)) for _ in range(n)],
        "first_road_class": np.random.choice([1, 2, 3, 4, 5, 6], n),
        "first_road_number": np.random.randint(1, 9999, n),
        "road_type": np.random.choice([1, 2, 3, 6, 7, 9, 12, -1], n),
        "speed_limit": np.random.choice([20, 30, 40, 50, 60, 70], n),
        "junction_detail": np.random.choice([0, 1, 2, 3, 5, 6, 7, 8, 9, 99, -1], n),
        "junction_control": np.random.choice([0, 1, 2, 3, 4, -1], n),
        "light_conditions": np.random.choice([1, 4, 5, 6, 7, -1], n),
        "weather_conditions": np.random.choice([1, 2, 3, 4, 5, 6, 7, 8, 9, -1], n),
        "road_surface_conditions": np.random.choice([1, 2, 3, 4, 5, 6, 7, -1], n),
        "special_conditions_at_site": np.random.choice([0, 1, 2, 3, 4, 5, 6, 7, 9, -1], n),
        "carriageway_hazards": np.random.choice([0, 1, 2, 3, 6, 7, 9, -1], n),
        "urban_or_rural_area": np.random.choice([1, 2, 3], n),
        "did_police_officer_attend_scene_of_accident": np.random.choice([1, 2, 3, -1], n),
        "lsoa_of_accident_location": ["E" + str(np.random.randint(10000000, 99999999)) for _ in range(n)],
        "police_force": np.random.randint(1, 99, n)
    })

def generate_demo_vehicles(accident_indices: list, n_per_accident: float = 2.0) -> pd.DataFrame:
    """Generates synthetic vehicle data linked to accident indices."""
    np.random.seed(42)
    n = int(len(accident_indices) * n_per_accident)
    acc_indices = np.random.choice(accident_indices, n)
    
    return pd.DataFrame({
        "accident_index": acc_indices,
        "accident_year": [2023] * n,
        "vehicle_reference": [np.random.randint(1, 4) for _ in range(n)],
        "vehicle_type": np.random.choice([9, 11, 2, 3, 4, 5, 19], n),
        "towing_and_articulation": np.random.choice([0, 1, 2, 3, 4, 5, 9, -1], n),
        "vehicle_manoeuvre": np.random.choice(range(1, 19), n),
        "vehicle_location_restricted_lane": np.random.choice([0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, -1], n),
        "junction_location": np.random.choice(range(1, 9), n),
        "skidding_and_overturning": np.random.choice([0, 1, 2, 3, 4, 5, 9, -1], n),
        "hit_object_in_carriageway": np.random.choice(range(0, 13), n),
        "vehicle_leaving_carriageway": np.random.choice(range(0, 9), n),
        "hit_object_off_carriageway": np.random.choice(range(0, 12), n),
        "first_point_of_impact": np.random.choice([0, 1, 2, 3, 4, 9, -1], n),
        "vehicle_left_hand_drive": np.random.choice([1, 2, 9, -1], n),
        "journey_purpose_of_driver": np.random.choice([1, 2, 3, 4, 5, 6, 15, -1], n),
        "sex_of_driver": np.random.choice([1, 2, 3, -1], n),
        "age_of_driver": np.random.randint(17, 90, n),
        "age_band_of_driver": np.random.choice(range(1, 12), n),
        "engine_capacity_cc": np.random.choice([1000, 1200, 1400, 1600, 2000, -1], n),
        "propulsion_code": np.random.choice(range(1, 13), n),
        "age_of_vehicle": np.random.randint(1, 20, n),
        "driver_imd_decile": np.random.choice(range(1, 11), n),
        "driver_home_area_type": np.random.choice([1, 2, 3, -1], n)
    })

def generate_demo_casualties(accident_indices: list, n_per_accident: float = 1.5) -> pd.DataFrame:
    """Generates synthetic casualty data linked to accident indices."""
    np.random.seed(42)
    n = int(len(accident_indices) * n_per_accident)
    acc_indices = np.random.choice(accident_indices, n)
    
    return pd.DataFrame({
        "accident_index": acc_indices,
        "accident_year": [2023] * n,
        "vehicle_reference": [np.random.randint(1, 4) for _ in range(n)],
        "casualty_reference": [np.random.randint(1, 5) for _ in range(n)],
        "casualty_class": np.random.choice([1, 2, 3], n),
        "sex_of_casualty": np.random.choice([1, 2, 9, -1], n),
        "age_of_casualty": np.random.randint(0, 100, n),
        "age_band_of_casualty": np.random.choice(range(1, 12), n),
        "casualty_severity": np.random.choice([1, 2, 3], n, p=[0.02, 0.1, 0.88]),
        "pedestrian_location": np.random.choice(range(0, 11), n),
        "pedestrian_movement": np.random.choice(range(0, 10), n),
        "car_passenger": np.random.choice([0, 1, 2, 9, -1], n),
        "bus_or_coach_passenger": np.random.choice([0, 1, 2, 3, 4, 9, -1], n),
        "pedestrian_road_maintenance_worker": np.random.choice([0, 1, 2, -1], n),
        "casualty_type": np.random.choice([0, 1, 2, 3, 4, 5, 8, 9, 10, 11, 16, 17], n),
        "casualty_home_area_type": np.random.choice([1, 2, 3, -1], n),
        "casualty_imd_decile": np.random.choice(range(1, 11), n)
    })
