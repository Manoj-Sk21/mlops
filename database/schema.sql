-- Schema definitions and raw/staging tables
CREATE EXTENSION IF NOT EXISTS postgis;

CREATE SCHEMA IF NOT EXISTS raw;
CREATE SCHEMA IF NOT EXISTS staging;
CREATE SCHEMA IF NOT EXISTS cleaned;
CREATE SCHEMA IF NOT EXISTS analytical;
CREATE SCHEMA IF NOT EXISTS model_ready;
CREATE SCHEMA IF NOT EXISTS monitoring;
CREATE SCHEMA IF NOT EXISTS meta;

CREATE TABLE IF NOT EXISTS meta.ingestion_log (
    id SERIAL PRIMARY KEY,
    source_name VARCHAR(255) NOT NULL,
    source_type VARCHAR(50) NOT NULL,
    extraction_timestamp TIMESTAMP DEFAULT NOW(),
    status VARCHAR(50) NOT NULL,
    row_count INTEGER,
    file_name VARCHAR(500),
    api_endpoint VARCHAR(500),
    error_message TEXT,
    duration_seconds FLOAT,
    run_id VARCHAR(100)
);

CREATE TABLE IF NOT EXISTS meta.data_quality_results (
    id SERIAL PRIMARY KEY,
    run_id VARCHAR(100),
    check_name VARCHAR(255),
    check_type VARCHAR(100),
    table_name VARCHAR(255),
    column_name VARCHAR(255),
    status VARCHAR(50),
    details TEXT,
    records_affected INTEGER,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS meta.rejected_records (
    id SERIAL PRIMARY KEY,
    run_id VARCHAR(100),
    source_table VARCHAR(255),
    record_data JSONB,
    rejection_reason VARCHAR(500),
    rejection_details TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS meta.validation_log (
    id SERIAL PRIMARY KEY,
    run_id VARCHAR(100),
    validation_type VARCHAR(100),
    total_checks INTEGER,
    passed_checks INTEGER,
    failed_checks INTEGER,
    total_records INTEGER,
    rejected_records INTEGER,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS raw.accidents (
    accident_index TEXT,
    accident_year TEXT,
    accident_reference TEXT,
    location_easting_osgr TEXT,
    location_northing_osgr TEXT,
    longitude TEXT,
    latitude TEXT,
    police_force TEXT,
    accident_severity TEXT,
    number_of_vehicles TEXT,
    number_of_casualties TEXT,
    date TEXT,
    day_of_week TEXT,
    time TEXT,
    local_authority_district TEXT,
    local_authority_highway TEXT,
    first_road_class TEXT,
    first_road_number TEXT,
    road_type TEXT,
    speed_limit TEXT,
    junction_detail TEXT,
    junction_control TEXT,
    second_road_class TEXT,
    second_road_number TEXT,
    pedestrian_crossing_human_control TEXT,
    pedestrian_crossing_physical_facilities TEXT,
    light_conditions TEXT,
    weather_conditions TEXT,
    road_surface_conditions TEXT,
    special_conditions_at_site TEXT,
    carriageway_hazards TEXT,
    urban_or_rural_area TEXT,
    did_police_officer_attend_scene_of_accident TEXT,
    trunk_road_flag TEXT,
    lsoa_of_accident_location TEXT
);

CREATE TABLE IF NOT EXISTS raw.vehicles (
    accident_index TEXT,
    accident_year TEXT,
    accident_reference TEXT,
    vehicle_reference TEXT,
    vehicle_type TEXT,
    towing_and_articulation TEXT,
    vehicle_manoeuvre TEXT,
    vehicle_direction_from TEXT,
    vehicle_direction_to TEXT,
    vehicle_location_restricted_lane TEXT,
    junction_location TEXT,
    skidding_and_overturning TEXT,
    hit_object_in_carriageway TEXT,
    vehicle_leaving_carriageway TEXT,
    hit_object_off_carriageway TEXT,
    first_point_of_impact TEXT,
    vehicle_left_hand_drive TEXT,
    journey_purpose_of_driver TEXT,
    sex_of_driver TEXT,
    age_of_driver TEXT,
    age_band_of_driver TEXT,
    engine_capacity_cc TEXT,
    propulsion_code TEXT,
    age_of_vehicle TEXT,
    generic_make_model TEXT,
    driver_imd_decile TEXT,
    driver_home_area_type TEXT
);

CREATE TABLE IF NOT EXISTS raw.casualties (
    accident_index TEXT,
    accident_year TEXT,
    accident_reference TEXT,
    vehicle_reference TEXT,
    casualty_reference TEXT,
    casualty_class TEXT,
    sex_of_casualty TEXT,
    age_of_casualty TEXT,
    age_band_of_casualty TEXT,
    casualty_severity TEXT,
    pedestrian_location TEXT,
    pedestrian_movement TEXT,
    car_passenger TEXT,
    bus_or_coach_passenger TEXT,
    pedestrian_road_maintenance_worker TEXT,
    casualty_type TEXT,
    casualty_home_area_type TEXT,
    casualty_imd_decile TEXT
);

CREATE TABLE IF NOT EXISTS staging.accidents (
    accident_id VARCHAR(50) PRIMARY KEY,
    accident_year INT,
    longitude FLOAT,
    latitude FLOAT,
    police_force VARCHAR(200),
    accident_severity INT,
    number_of_vehicles INT,
    number_of_casualties INT,
    accident_date DATE,
    day_of_week INT,
    accident_time TIME,
    local_authority VARCHAR(200),
    road_type VARCHAR(100),
    speed_limit INT,
    junction_detail VARCHAR(100),
    junction_control VARCHAR(100),
    light_conditions VARCHAR(100),
    weather_conditions VARCHAR(100),
    road_surface_conditions VARCHAR(100),
    special_conditions VARCHAR(200),
    carriageway_hazards VARCHAR(200),
    urban_rural VARCHAR(50),
    did_police_attend BOOLEAN,
    lsoa VARCHAR(50)
);

CREATE TABLE IF NOT EXISTS staging.vehicles (
    id SERIAL PRIMARY KEY,
    accident_id VARCHAR(50),
    vehicle_reference INT,
    vehicle_type VARCHAR(100),
    vehicle_manoeuvre VARCHAR(100),
    skidding VARCHAR(100),
    hit_object_in VARCHAR(100),
    first_point_of_impact VARCHAR(100),
    journey_purpose VARCHAR(100),
    sex_of_driver VARCHAR(20),
    age_of_driver INT,
    age_band_of_driver VARCHAR(50),
    engine_capacity INT,
    propulsion_code VARCHAR(50),
    age_of_vehicle INT
);

CREATE TABLE IF NOT EXISTS staging.casualties (
    id SERIAL PRIMARY KEY,
    accident_id VARCHAR(50),
    vehicle_reference INT,
    casualty_reference INT,
    casualty_class VARCHAR(50),
    sex_of_casualty VARCHAR(20),
    age_of_casualty INT,
    age_band VARCHAR(50),
    casualty_severity INT,
    pedestrian_location VARCHAR(100),
    pedestrian_movement VARCHAR(100),
    casualty_type VARCHAR(100)
);
