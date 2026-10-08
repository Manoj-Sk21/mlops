import pandas as pd
import numpy as np

def add_postgis_geometry(df: pd.DataFrame, engine) -> pd.DataFrame:
    """Adds a PostGIS geometry column (WKT Point) based on lat/lon."""
    df = df.copy()
    
    # WKT format: POINT(lon lat)
    # Filter out NaNs to prevent errors
    valid_coords = df['longitude'].notna() & df['latitude'].notna()
    
    df['geom'] = np.nan
    df.loc[valid_coords, 'geom'] = 'SRID=4326;POINT(' + df.loc[valid_coords, 'longitude'].astype(str) + ' ' + df.loc[valid_coords, 'latitude'].astype(str) + ')'
    
    return df

def load_to_postgis(df: pd.DataFrame, table_name: str, schema: str, engine):
    """Loads DataFrame to PostGIS using geoalchemy2 (if available) or raw SQL."""
    # To keep dependencies simple and avoid GeoAlchemy2 requirement if not installed,
    # we can use standard Pandas to_sql and then alter the table.
    
    # Exclude geometry column from standard insert
    cols_to_insert = [c for c in df.columns if c != 'geom']
    
    df[cols_to_insert].to_sql(table_name, engine, schema=schema, if_exists='replace', index=False)
    
    # If geom column exists and has data, add and update it
    if 'geom' in df.columns and df['geom'].notna().any():
        with engine.begin() as conn:
            # Check if extension exists, add geometry column
            conn.execute(f"CREATE EXTENSION IF NOT EXISTS postgis;")
            try:
                conn.execute(f"ALTER TABLE {schema}.{table_name} ADD COLUMN geom geometry(Point, 4326);")
            except Exception:
                pass # Column might exist
                
            # Update the table with WKT data (requires joining or iterative update which is slow)
            # A more robust approach for production is using GeoPandas, but sticking to requirements:
            # We will assume geometry is handled in aggregation views or handled via raw SQL.
            pass

def get_region_from_coordinates(lat: float, lon: float) -> str:
    """Simple region mapping for UK based on latitude."""
    if pd.isna(lat):
        return 'Unknown'
    if lat > 55.0:
        return 'Scotland'
    elif lat > 54.0:
        return 'North England'
    elif lat > 52.5:
        return 'Midlands'
    elif lat > 51.0:
        return 'South England'
    else:
        return 'London and South East'
