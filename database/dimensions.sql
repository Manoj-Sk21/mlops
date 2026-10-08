-- Dimension tables for the analytical schema

CREATE TABLE IF NOT EXISTS analytical.dim_date (
    date_key INTEGER PRIMARY KEY, -- YYYYMMDD format
    full_date DATE UNIQUE NOT NULL,
    year INT,
    quarter INT,
    month INT,
    month_name VARCHAR(20),
    day INT,
    day_of_week INT,
    day_name VARCHAR(20),
    is_weekend BOOLEAN,
    week_of_year INT,
    season VARCHAR(20)
);

CREATE TABLE IF NOT EXISTS analytical.dim_severity (
    severity_key INTEGER PRIMARY KEY,
    severity_code INTEGER UNIQUE NOT NULL,
    severity_label VARCHAR(50) NOT NULL,
    severity_description VARCHAR(200)
);

INSERT INTO analytical.dim_severity (severity_key, severity_code, severity_label, severity_description)
VALUES
    (1, 1, 'Fatal', 'Fatal injury accident'),
    (2, 2, 'Serious', 'Serious injury accident'),
    (3, 3, 'Slight', 'Slight injury accident')
ON CONFLICT (severity_key) DO NOTHING;

CREATE TABLE IF NOT EXISTS analytical.dim_road (
    road_key SERIAL PRIMARY KEY,
    road_type VARCHAR(100),
    road_class VARCHAR(50),
    speed_limit INTEGER,
    road_surface VARCHAR(100),
    junction_type VARCHAR(100),
    junction_control VARCHAR(100),
    light_conditions VARCHAR(100),
    urban_rural VARCHAR(50),
    UNIQUE(road_type, road_class, speed_limit, road_surface, junction_type, junction_control, light_conditions, urban_rural)
);

CREATE TABLE IF NOT EXISTS analytical.dim_weather (
    weather_key SERIAL PRIMARY KEY,
    weather_condition VARCHAR(100),
    temperature FLOAT,
    temperature_band VARCHAR(50),
    precipitation FLOAT,
    precipitation_band VARCHAR(50),
    wind_speed FLOAT,
    wind_band VARCHAR(50),
    rain FLOAT,
    snowfall FLOAT
);

CREATE TABLE IF NOT EXISTS analytical.dim_location (
    location_key SERIAL PRIMARY KEY,
    latitude FLOAT NOT NULL,
    longitude FLOAT NOT NULL,
    geom GEOMETRY(Point, 4326),
    local_authority VARCHAR(200),
    police_force VARCHAR(200),
    lsoa VARCHAR(50),
    region VARCHAR(100)
);

CREATE INDEX IF NOT EXISTS idx_dim_location_latlon ON analytical.dim_location(latitude, longitude);
CREATE INDEX IF NOT EXISTS idx_dim_location_geom ON analytical.dim_location USING GIST(geom);
