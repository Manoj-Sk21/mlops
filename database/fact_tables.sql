CREATE TABLE IF NOT EXISTS analytical.fact_accident (
    accident_id VARCHAR(50) PRIMARY KEY,
    date_key INT REFERENCES analytical.dim_date(date_key),
    road_key INT REFERENCES analytical.dim_road(road_key),
    weather_key INT REFERENCES analytical.dim_weather(weather_key),
    location_key INT REFERENCES analytical.dim_location(location_key),
    severity_key INT REFERENCES analytical.dim_severity(severity_key),
    accident_time TIME,
    number_of_vehicles INT,
    number_of_casualties INT,
    latitude FLOAT,
    longitude FLOAT,
    geom GEOMETRY(Point, 4326),
    did_police_attend BOOLEAN,
    special_conditions VARCHAR(200),
    carriageway_hazards VARCHAR(200)
);

CREATE INDEX IF NOT EXISTS idx_fact_accident_date ON analytical.fact_accident(date_key);
CREATE INDEX IF NOT EXISTS idx_fact_accident_road ON analytical.fact_accident(road_key);
CREATE INDEX IF NOT EXISTS idx_fact_accident_weather ON analytical.fact_accident(weather_key);
CREATE INDEX IF NOT EXISTS idx_fact_accident_location ON analytical.fact_accident(location_key);
CREATE INDEX IF NOT EXISTS idx_fact_accident_severity ON analytical.fact_accident(severity_key);
CREATE INDEX IF NOT EXISTS idx_fact_accident_time ON analytical.fact_accident(accident_time);

CREATE TABLE IF NOT EXISTS analytical.fact_vehicle (
    id SERIAL PRIMARY KEY,
    accident_id VARCHAR(50) REFERENCES analytical.fact_accident(accident_id),
    vehicle_reference INT,
    vehicle_type VARCHAR(100),
    vehicle_manoeuvre VARCHAR(100),
    sex_of_driver VARCHAR(20),
    age_of_driver INT,
    age_band_of_driver VARCHAR(50),
    engine_capacity INT,
    age_of_vehicle INT,
    journey_purpose VARCHAR(100),
    skidding VARCHAR(100),
    hit_object_in VARCHAR(100),
    first_point_of_impact VARCHAR(100),
    propulsion_code VARCHAR(50)
);

CREATE INDEX IF NOT EXISTS idx_fact_vehicle_accident ON analytical.fact_vehicle(accident_id);

CREATE TABLE IF NOT EXISTS analytical.fact_casualty (
    id SERIAL PRIMARY KEY,
    accident_id VARCHAR(50) REFERENCES analytical.fact_accident(accident_id),
    vehicle_reference INT,
    casualty_reference INT,
    casualty_class VARCHAR(50),
    casualty_severity INT,
    sex_of_casualty VARCHAR(20),
    age_of_casualty INT,
    age_band VARCHAR(50),
    casualty_type VARCHAR(100),
    pedestrian_location VARCHAR(100),
    pedestrian_movement VARCHAR(100)
);

CREATE INDEX IF NOT EXISTS idx_fact_casualty_accident ON analytical.fact_casualty(accident_id);

-- Model Ready Tables
CREATE TABLE IF NOT EXISTS model_ready.accident_features (
    accident_id VARCHAR(50) PRIMARY KEY,
    severity INT NOT NULL,
    hour INT,
    day_of_week INT,
    month INT,
    year INT,
    is_weekend BOOLEAN,
    season VARCHAR(20),
    is_rush_hour BOOLEAN,
    latitude FLOAT,
    longitude FLOAT,
    number_of_vehicles INT,
    number_of_casualties INT,
    speed_limit INT,
    road_type VARCHAR(100),
    road_surface VARCHAR(100),
    light_conditions VARCHAR(100),
    weather_condition VARCHAR(100),
    urban_rural VARCHAR(50),
    junction_type VARCHAR(100),
    temperature FLOAT,
    precipitation FLOAT,
    wind_speed FLOAT,
    rain FLOAT,
    snowfall FLOAT,
    police_force VARCHAR(200)
);

-- Monitoring Tables
CREATE TABLE IF NOT EXISTS monitoring.drift_log (
    id SERIAL PRIMARY KEY,
    run_id VARCHAR(100),
    drift_type VARCHAR(50),
    feature_name VARCHAR(100),
    metric_name VARCHAR(50),
    metric_value FLOAT,
    threshold FLOAT,
    is_drifted BOOLEAN,
    reference_distribution JSONB,
    current_distribution JSONB,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS monitoring.performance_log (
    id SERIAL PRIMARY KEY,
    run_id VARCHAR(100),
    model_version VARCHAR(100),
    metric_name VARCHAR(50),
    metric_value FLOAT,
    dataset_size INT,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS monitoring.api_log (
    id SERIAL PRIMARY KEY,
    request_id VARCHAR(100),
    endpoint VARCHAR(200),
    method VARCHAR(10),
    status_code INT,
    latency_ms FLOAT,
    request_body JSONB,
    response_body JSONB,
    error_message TEXT,
    model_version VARCHAR(100),
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS monitoring.false_negative_log (
    id SERIAL PRIMARY KEY,
    run_id VARCHAR(100),
    prediction_id VARCHAR(100),
    predicted_severity INT,
    actual_severity INT,
    model_version VARCHAR(100),
    features JSONB,
    created_at TIMESTAMP DEFAULT NOW()
);
