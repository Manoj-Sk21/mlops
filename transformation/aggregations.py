import pandas as pd
from sqlalchemy import text
from ingestion.ingestion_utils import logger

def build_dim_date(engine, accidents_df: pd.DataFrame):
    """Builds the dim_date table."""
    logger.info("Building dim_date...")
    dates = pd.to_datetime(accidents_df['date']).dropna().unique()
    df = pd.DataFrame({'full_date': dates})
    df['year'] = df['full_date'].dt.year
    df['month'] = df['full_date'].dt.month
    df['day'] = df['full_date'].dt.day
    df['day_of_week'] = df['full_date'].dt.dayofweek
    df['is_weekend'] = df['day_of_week'] >= 5
    
    with engine.begin() as conn:
        conn.execute(text("CREATE SCHEMA IF NOT EXISTS analytical"))
        df.to_sql('dim_date', conn, schema='analytical', if_exists='replace', index=False)
        
def build_dim_road(engine, accidents_df: pd.DataFrame):
    """Builds the dim_road table."""
    logger.info("Building dim_road...")
    cols = ['first_road_class', 'first_road_number', 'road_type', 'speed_limit']
    df = accidents_df[cols].drop_duplicates().dropna().reset_index(drop=True)
    df['road_key'] = df.index + 1
    
    with engine.begin() as conn:
        conn.execute(text("CREATE SCHEMA IF NOT EXISTS analytical"))
        df.to_sql('dim_road', conn, schema='analytical', if_exists='replace', index=False)
    return dict(zip(zip(df.first_road_class, df.first_road_number, df.road_type, df.speed_limit), df.road_key))

def build_dim_weather(engine, enriched_df: pd.DataFrame):
    """Builds the dim_weather table."""
    logger.info("Building dim_weather...")
    cols = ['weather_conditions', 'weather_label', 'weather_code_api', 'weather_description_api']
    available_cols = [c for c in cols if c in enriched_df.columns]
    df = enriched_df[available_cols].drop_duplicates().dropna().reset_index(drop=True)
    df['weather_key'] = df.index + 1
    
    with engine.begin() as conn:
        conn.execute(text("CREATE SCHEMA IF NOT EXISTS analytical"))
        df.to_sql('dim_weather', conn, schema='analytical', if_exists='replace', index=False)

def build_dim_location(engine, accidents_df: pd.DataFrame):
    """Builds the dim_location table."""
    logger.info("Building dim_location...")
    cols = ['latitude', 'longitude', 'local_authority_district', 'lsoa_of_accident_location', 'urban_or_rural_area']
    df = accidents_df[cols].drop_duplicates().reset_index(drop=True)
    df['location_key'] = df.index + 1
    
    from .geospatial import get_region_from_coordinates
    df['region'] = df.apply(lambda row: get_region_from_coordinates(row['latitude'], row['longitude']), axis=1)
    
    with engine.begin() as conn:
        conn.execute(text("CREATE SCHEMA IF NOT EXISTS analytical"))
        df.to_sql('dim_location', conn, schema='analytical', if_exists='replace', index=False)

def build_fact_accident(engine, enriched_df: pd.DataFrame):
    """Builds the fact_accident table."""
    logger.info("Building fact_accident...")
    # Simplified version - in reality would join with dims for keys
    with engine.begin() as conn:
        conn.execute(text("CREATE SCHEMA IF NOT EXISTS analytical"))
        enriched_df.to_sql('fact_accident', conn, schema='analytical', if_exists='replace', index=False)

def build_fact_vehicle(engine, vehicles_df: pd.DataFrame):
    """Builds the fact_vehicle table."""
    logger.info("Building fact_vehicle...")
    with engine.begin() as conn:
        conn.execute(text("CREATE SCHEMA IF NOT EXISTS analytical"))
        vehicles_df.to_sql('fact_vehicle', conn, schema='analytical', if_exists='replace', index=False)

def build_fact_casualty(engine, casualties_df: pd.DataFrame):
    """Builds the fact_casualty table."""
    logger.info("Building fact_casualty...")
    with engine.begin() as conn:
        conn.execute(text("CREATE SCHEMA IF NOT EXISTS analytical"))
        casualties_df.to_sql('fact_casualty', conn, schema='analytical', if_exists='replace', index=False)

def build_model_ready(engine):
    """Builds the model_ready features view/table."""
    logger.info("Building model_ready.accident_features...")
    query = text("""
        CREATE SCHEMA IF NOT EXISTS model_ready;
        DROP TABLE IF EXISTS model_ready.accident_features;
        CREATE TABLE model_ready.accident_features AS
        SELECT 
            accident_severity AS severity,
            hour, 
            day_of_week, 
            accident_month AS month, 
            accident_year AS year, 
            is_weekend, 
            season, 
            is_rush_hour,
            latitude, 
            longitude, 
            number_of_vehicles, 
            number_of_casualties, 
            speed_limit,
            road_type, 
            road_surface_conditions AS road_surface, 
            light_conditions, 
            weather_conditions, 
            urban_or_rural_area AS urban_rural,
            junction_detail AS junction_type, 
            temperature, 
            precipitation, 
            wind_speed, 
            rain, 
            snowfall, 
            police_force
        FROM analytical.fact_accident;
    """)
    with engine.begin() as conn:
        conn.execute(query)

def build_all(engine, accidents_df, vehicles_df, casualties_df, enriched_df):
    """Orchestrates all aggregation builds."""
    build_dim_date(engine, enriched_df)
    build_dim_road(engine, enriched_df)
    build_dim_weather(engine, enriched_df)
    build_dim_location(engine, enriched_df)
    build_fact_accident(engine, enriched_df)
    build_fact_vehicle(engine, vehicles_df)
    build_fact_casualty(engine, casualties_df)
    # The actual execution of build_model_ready happens in a separate task in the DAG
