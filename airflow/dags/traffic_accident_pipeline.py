from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.operators.empty import EmptyOperator
from datetime import datetime, timedelta
import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from ingestion.ingestion_utils import get_db_engine, get_data_dirs, generate_run_id
from ingestion.accident_ingestion import download_accident_data, download_vehicle_data, download_casualty_data
from ingestion.weather_ingestion import fetch_weather_for_locations
from transformation.validation import DataQualityValidator
from transformation.cleaning import clean_accidents, clean_vehicles, clean_casualties
from transformation.weather_join import join_accident_weather
from transformation.geospatial import add_postgis_geometry, load_to_postgis
from transformation.aggregations import build_all, build_model_ready
import pandas as pd

default_args = {
    'owner': 'data-engineer',
    'retries': 2,
    'retry_delay': timedelta(minutes=5),
    'start_date': datetime(2024, 1, 1)
}

def _download_accident_data(**kwargs):
    run_id = generate_run_id()
    kwargs['ti'].xcom_push(key='run_id', value=run_id)
    engine = get_db_engine()
    dirs = get_data_dirs()
    demo_mode = os.getenv('DEMO_MODE', 'true').lower() == 'true'
    
    df = download_accident_data(dirs['raw'], engine, run_id, demo_mode)
    path = os.path.join(dirs['raw'], f"accidents_{run_id}.parquet")
    df.to_parquet(path)
    kwargs['ti'].xcom_push(key='accidents_path', value=path)
    print(f"Downloaded accidents to {path}")

def _download_vehicle_data(**kwargs):
    run_id = kwargs['ti'].xcom_pull(key='run_id', task_ids='download_accident_data')
    engine = get_db_engine()
    dirs = get_data_dirs()
    demo_mode = os.getenv('DEMO_MODE', 'true').lower() == 'true'
    
    df = download_vehicle_data(dirs['raw'], engine, run_id, demo_mode)
    path = os.path.join(dirs['raw'], f"vehicles_{run_id}.parquet")
    df.to_parquet(path)
    kwargs['ti'].xcom_push(key='vehicles_path', value=path)

def _download_casualty_data(**kwargs):
    run_id = kwargs['ti'].xcom_pull(key='run_id', task_ids='download_accident_data')
    engine = get_db_engine()
    dirs = get_data_dirs()
    demo_mode = os.getenv('DEMO_MODE', 'true').lower() == 'true'
    
    df = download_casualty_data(dirs['raw'], engine, run_id, demo_mode)
    path = os.path.join(dirs['raw'], f"casualties_{run_id}.parquet")
    df.to_parquet(path)
    kwargs['ti'].xcom_push(key='casualties_path', value=path)

def _download_weather_data(**kwargs):
    run_id = kwargs['ti'].xcom_pull(key='run_id', task_ids='download_accident_data')
    acc_path = kwargs['ti'].xcom_pull(key='accidents_path', task_ids='download_accident_data')
    
    engine = get_db_engine()
    dirs = get_data_dirs()
    demo_mode = os.getenv('DEMO_MODE', 'true').lower() == 'true'
    
    acc_df = pd.read_parquet(acc_path)
    # create dummy dates if not existing properly
    if 'date' not in acc_df.columns:
        acc_df['date'] = '2023-01-01'
        
    cache_db = os.path.join(dirs['data'], 'weather_cache.sqlite')
    weather_df = fetch_weather_for_locations(acc_df, cache_db, engine, run_id, demo_mode)
    
    path = os.path.join(dirs['raw'], f"weather_{run_id}.parquet")
    weather_df.to_parquet(path)
    kwargs['ti'].xcom_push(key='weather_path', value=path)

def _validate_raw_data(**kwargs):
    run_id = kwargs['ti'].xcom_pull(key='run_id', task_ids='download_accident_data')
    acc_path = kwargs['ti'].xcom_pull(key='accidents_path', task_ids='download_accident_data')
    veh_path = kwargs['ti'].xcom_pull(key='vehicles_path', task_ids='download_vehicle_data')
    cas_path = kwargs['ti'].xcom_pull(key='casualties_path', task_ids='download_casualty_data')
    
    engine = get_db_engine()
    dirs = get_data_dirs()
    
    acc_df = pd.read_parquet(acc_path)
    veh_df = pd.read_parquet(veh_path)
    cas_df = pd.read_parquet(cas_path)
    
    validator = DataQualityValidator(engine, run_id)
    res = validator.run_all_validations(acc_df, veh_df, cas_df)
    
    # Save valid datasets
    acc_valid_path = os.path.join(dirs['staging'], f"accidents_valid_{run_id}.parquet")
    veh_valid_path = os.path.join(dirs['staging'], f"vehicles_valid_{run_id}.parquet")
    cas_valid_path = os.path.join(dirs['staging'], f"casualties_valid_{run_id}.parquet")
    
    res['accidents']['valid'].to_parquet(acc_valid_path)
    res['vehicles']['valid'].to_parquet(veh_valid_path)
    res['casualties']['valid'].to_parquet(cas_valid_path)
    
    kwargs['ti'].xcom_push(key='acc_valid_path', value=acc_valid_path)
    kwargs['ti'].xcom_push(key='veh_valid_path', value=veh_valid_path)
    kwargs['ti'].xcom_push(key='cas_valid_path', value=cas_valid_path)

def _clean_transform(**kwargs):
    acc_valid_path = kwargs['ti'].xcom_pull(key='acc_valid_path', task_ids='validate_raw_data')
    veh_valid_path = kwargs['ti'].xcom_pull(key='veh_valid_path', task_ids='validate_raw_data')
    cas_valid_path = kwargs['ti'].xcom_pull(key='cas_valid_path', task_ids='validate_raw_data')
    
    dirs = get_data_dirs()
    
    acc_clean = clean_accidents(pd.read_parquet(acc_valid_path))
    veh_clean = clean_vehicles(pd.read_parquet(veh_valid_path))
    cas_clean = clean_casualties(pd.read_parquet(cas_valid_path))
    
    run_id = kwargs['ti'].xcom_pull(key='run_id', task_ids='download_accident_data')
    
    acc_clean_path = os.path.join(dirs['cleaned'], f"accidents_clean_{run_id}.parquet")
    veh_clean_path = os.path.join(dirs['cleaned'], f"vehicles_clean_{run_id}.parquet")
    cas_clean_path = os.path.join(dirs['cleaned'], f"casualties_clean_{run_id}.parquet")
    
    acc_clean.to_parquet(acc_clean_path)
    veh_clean.to_parquet(veh_clean_path)
    cas_clean.to_parquet(cas_clean_path)
    
    kwargs['ti'].xcom_push(key='acc_clean_path', value=acc_clean_path)
    kwargs['ti'].xcom_push(key='veh_clean_path', value=veh_clean_path)
    kwargs['ti'].xcom_push(key='cas_clean_path', value=cas_clean_path)

def _weather_join(**kwargs):
    acc_clean_path = kwargs['ti'].xcom_pull(key='acc_clean_path', task_ids='clean_transform')
    weather_path = kwargs['ti'].xcom_pull(key='weather_path', task_ids='download_weather_data')
    
    acc_df = pd.read_parquet(acc_clean_path)
    weather_df = pd.read_parquet(weather_path)
    
    enriched_df = join_accident_weather(acc_df, weather_df)
    
    run_id = kwargs['ti'].xcom_pull(key='run_id', task_ids='download_accident_data')
    dirs = get_data_dirs()
    enriched_path = os.path.join(dirs['cleaned'], f"accidents_enriched_{run_id}.parquet")
    enriched_df.to_parquet(enriched_path)
    
    kwargs['ti'].xcom_push(key='enriched_path', value=enriched_path)

def _geospatial_transform(**kwargs):
    enriched_path = kwargs['ti'].xcom_pull(key='enriched_path', task_ids='weather_join')
    df = pd.read_parquet(enriched_path)
    
    # Optional geospatial enrichments
    # df = add_postgis_geometry(df, get_db_engine()) 
    
    run_id = kwargs['ti'].xcom_pull(key='run_id', task_ids='download_accident_data')
    dirs = get_data_dirs()
    geo_path = os.path.join(dirs['cleaned'], f"accidents_geo_{run_id}.parquet")
    df.to_parquet(geo_path)
    kwargs['ti'].xcom_push(key='geo_path', value=geo_path)

def _data_quality_checks(**kwargs):
    geo_path = kwargs['ti'].xcom_pull(key='geo_path', task_ids='geospatial_transform')
    df = pd.read_parquet(geo_path)
    print(f"Final data shape: {df.shape}")

def _load_postgresql(**kwargs):
    geo_path = kwargs['ti'].xcom_pull(key='geo_path', task_ids='geospatial_transform')
    veh_clean_path = kwargs['ti'].xcom_pull(key='veh_clean_path', task_ids='clean_transform')
    cas_clean_path = kwargs['ti'].xcom_pull(key='cas_clean_path', task_ids='clean_transform')
    
    enriched_df = pd.read_parquet(geo_path)
    veh_df = pd.read_parquet(veh_clean_path)
    cas_df = pd.read_parquet(cas_clean_path)
    
    engine = get_db_engine()
    build_all(engine, enriched_df, veh_df, cas_df, enriched_df)

def _build_model_ready(**kwargs):
    engine = get_db_engine()
    build_model_ready(engine)

with DAG(
    'traffic_accident_pipeline',
    default_args=default_args,
    description='Traffic Accident Severity Analytics ETL',
    schedule_interval=None,
    catchup=False,
    tags=['traffic', 'accidents', 'etl']
) as dag:

    start = EmptyOperator(task_id='start')
    
    t_download_acc = PythonOperator(task_id='download_accident_data', python_callable=_download_accident_data)
    t_download_veh = PythonOperator(task_id='download_vehicle_data', python_callable=_download_vehicle_data)
    t_download_cas = PythonOperator(task_id='download_casualty_data', python_callable=_download_casualty_data)
    
    t_download_weather = PythonOperator(task_id='download_weather_data', python_callable=_download_weather_data)
    
    t_validate = PythonOperator(task_id='validate_raw_data', python_callable=_validate_raw_data)
    t_clean = PythonOperator(task_id='clean_transform', python_callable=_clean_transform)
    t_weather_join = PythonOperator(task_id='weather_join', python_callable=_weather_join)
    t_geo = PythonOperator(task_id='geospatial_transform', python_callable=_geospatial_transform)
    t_dq = PythonOperator(task_id='data_quality_checks', python_callable=_data_quality_checks)
    
    t_load = PythonOperator(task_id='load_postgresql', python_callable=_load_postgresql)
    t_build_mart = EmptyOperator(task_id='build_accident_mart')
    t_model_ready = PythonOperator(task_id='build_model_ready', python_callable=_build_model_ready)
    
    end = EmptyOperator(task_id='pipeline_complete')

    start >> [t_download_acc, t_download_veh, t_download_cas]
    t_download_acc >> t_download_weather
    
    [t_download_acc, t_download_veh, t_download_cas] >> t_validate
    t_validate >> t_clean
    t_clean >> t_weather_join
    t_download_weather >> t_weather_join
    
    t_weather_join >> t_geo >> t_dq
    t_dq >> t_load >> [t_build_mart, t_model_ready]
    [t_build_mart, t_model_ready] >> end
