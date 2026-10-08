-- ============================================================
-- DEMO DATA FOR DEVELOPMENT AND TESTING ONLY
-- This data is synthetic and does NOT represent real accident statistics
-- Replace with actual UK Road Safety data via the ingestion pipeline
-- ============================================================

DO $$ 
DECLARE
    i INT;
    start_date DATE := '2023-01-01';
    curr_date DATE;
    dim_date_key INT;
    loc_key INT;
    rd_key INT;
    wth_key INT;
    sev_key INT;
    acc_id VARCHAR(50);
    veh_ref INT;
    cas_ref INT;
    num_veh INT;
    num_cas INT;
    r FLOAT;
BEGIN
    -- 1. Generate 120 dim_date records (2023-01-01 to 2023-04-30)
    FOR i IN 0..119 LOOP
        curr_date := start_date + i;
        dim_date_key := to_char(curr_date, 'YYYYMMDD')::INT;
        
        INSERT INTO analytical.dim_date (
            date_key, full_date, year, quarter, month, month_name, 
            day, day_of_week, day_name, is_weekend, week_of_year, season
        ) VALUES (
            dim_date_key, 
            curr_date, 
            EXTRACT(YEAR FROM curr_date), 
            EXTRACT(QUARTER FROM curr_date), 
            EXTRACT(MONTH FROM curr_date), 
            to_char(curr_date, 'Month'), 
            EXTRACT(DAY FROM curr_date), 
            EXTRACT(ISODOW FROM curr_date), 
            to_char(curr_date, 'FMDay'), 
            (EXTRACT(ISODOW FROM curr_date) IN (6, 7)), 
            EXTRACT(WEEK FROM curr_date), 
            CASE 
                WHEN EXTRACT(MONTH FROM curr_date) IN (12, 1, 2) THEN 'Winter'
                WHEN EXTRACT(MONTH FROM curr_date) IN (3, 4, 5) THEN 'Spring'
                WHEN EXTRACT(MONTH FROM curr_date) IN (6, 7, 8) THEN 'Summer'
                ELSE 'Autumn'
            END
        ) ON CONFLICT DO NOTHING;
    END LOOP;

    -- 2. Generate dim_road records
    FOR i IN 1..25 LOOP
        INSERT INTO analytical.dim_road (
            road_type, road_class, speed_limit, road_surface, junction_type, junction_control, light_conditions, urban_rural
        ) VALUES (
            (ARRAY['Single carriageway', 'Dual carriageway', 'Roundabout', 'One way street'])[floor(random() * 4 + 1)],
            (ARRAY['A', 'B', 'C', 'Unclassified', 'Motorway'])[floor(random() * 5 + 1)],
            (ARRAY[20, 30, 40, 50, 60, 70])[floor(random() * 6 + 1)],
            (ARRAY['Dry', 'Wet / damp', 'Snow', 'Frost / ice'])[floor(random() * 4 + 1)],
            (ARRAY['Not at junction', 'Roundabout', 'T or staggered junction', 'Crossroads'])[floor(random() * 4 + 1)],
            (ARRAY['Give way or uncontrolled', 'Auto traffic signal', 'Stop sign'])[floor(random() * 3 + 1)],
            (ARRAY['Daylight', 'Darkness - lights lit', 'Darkness - no lighting'])[floor(random() * 3 + 1)],
            (ARRAY['Urban', 'Rural'])[floor(random() * 2 + 1)]
        ) ON CONFLICT DO NOTHING;
    END LOOP;

    -- 3. Generate dim_weather records
    FOR i IN 1..20 LOOP
        INSERT INTO analytical.dim_weather (
            weather_condition, temperature, temperature_band, precipitation, precipitation_band, wind_speed, wind_band, rain, snowfall
        ) VALUES (
            (ARRAY['Fine no high winds', 'Raining no high winds', 'Snowing no high winds', 'Fine + high winds', 'Raining + high winds', 'Fog or mist'])[floor(random() * 6 + 1)],
            random() * 30 - 5,
            'Normal',
            random() * 10,
            'Light',
            random() * 40,
            'Normal',
            random() * 5,
            random() * 2
        ) ON CONFLICT DO NOTHING;
    END LOOP;

    -- 4. Generate dim_location records
    FOR i IN 1..50 LOOP
        INSERT INTO analytical.dim_location (
            latitude, longitude, geom, local_authority, police_force, lsoa, region
        ) VALUES (
            51.0 + random() * 4.0, -- Roughly UK Lat
            -3.0 + random() * 4.0, -- Roughly UK Lon
            ST_SetSRID(ST_MakePoint(-3.0 + random() * 4.0, 51.0 + random() * 4.0), 4326),
            (ARRAY['Westminster', 'Birmingham', 'Leeds', 'Manchester', 'Liverpool', 'Bristol'])[floor(random() * 6 + 1)],
            (ARRAY['Metropolitan Police', 'West Midlands', 'West Yorkshire', 'Greater Manchester', 'Merseyside', 'Avon and Somerset'])[floor(random() * 6 + 1)],
            'E0100000' || floor(random() * 9 + 1),
            (ARRAY['London', 'West Midlands', 'Yorkshire', 'North West', 'South West'])[floor(random() * 5 + 1)]
        ) ON CONFLICT DO NOTHING;
    END LOOP;

    -- 5. Generate 1000 fact_accident records and related tables
    FOR i IN 1..1000 LOOP
        acc_id := 'DEMO-2023-' || lpad(i::text, 4, '0');
        dim_date_key := to_char(start_date + floor(random() * 120)::int, 'YYYYMMDD')::INT;
        
        -- Severity distribution: ~3% Fatal, ~15% Serious, ~82% Slight
        r := random();
        IF r < 0.03 THEN sev_key := 1;
        ELSIF r < 0.18 THEN sev_key := 2;
        ELSE sev_key := 3;
        END IF;

        loc_key := floor(random() * 50 + 1);
        rd_key := floor(random() * 25 + 1);
        wth_key := floor(random() * 20 + 1);
        
        num_veh := floor(random() * 3 + 1); -- 1 to 3 vehicles
        num_cas := floor(random() * 3 + 1); -- 1 to 3 casualties

        INSERT INTO analytical.fact_accident (
            accident_id, date_key, road_key, weather_key, location_key, severity_key, 
            accident_time, number_of_vehicles, number_of_casualties, latitude, longitude, 
            geom, did_police_attend, special_conditions, carriageway_hazards
        ) VALUES (
            acc_id, dim_date_key, rd_key, wth_key, loc_key, sev_key,
            (time '00:00:00' + random() * (time '23:59:59' - time '00:00:00')),
            num_veh, num_cas,
            51.5 + random(), -0.1 + random(),
            ST_SetSRID(ST_MakePoint(-0.1 + random(), 51.5 + random()), 4326),
            (random() > 0.2),
            'None', 'None'
        );

        -- Insert vehicles
        FOR veh_ref IN 1..num_veh LOOP
            INSERT INTO analytical.fact_vehicle (
                accident_id, vehicle_reference, vehicle_type, vehicle_manoeuvre, 
                sex_of_driver, age_of_driver, age_band_of_driver, engine_capacity, 
                age_of_vehicle, journey_purpose, skidding, hit_object_in, 
                first_point_of_impact, propulsion_code
            ) VALUES (
                acc_id, veh_ref, 
                (ARRAY['Car', 'Van', 'Motorcycle', 'Bus'])[floor(random() * 4 + 1)],
                'Going ahead', 
                (ARRAY['Male', 'Female'])[floor(random() * 2 + 1)],
                floor(random() * 60 + 18), '26-35', 1600, 5, 'Commuting', 'None', 'None', 'Front', 'Petrol'
            );
        END LOOP;

        -- Insert casualties
        FOR cas_ref IN 1..num_cas LOOP
            INSERT INTO analytical.fact_casualty (
                accident_id, vehicle_reference, casualty_reference, casualty_class, 
                casualty_severity, sex_of_casualty, age_of_casualty, age_band, 
                casualty_type, pedestrian_location, pedestrian_movement
            ) VALUES (
                acc_id, floor(random() * num_veh + 1), cas_ref, 
                (ARRAY['Driver', 'Passenger', 'Pedestrian'])[floor(random() * 3 + 1)],
                sev_key, 
                (ARRAY['Male', 'Female'])[floor(random() * 2 + 1)],
                floor(random() * 60 + 10), '26-35', 'Car occupant', 'Not a Pedestrian', 'Not a Pedestrian'
            );
        END LOOP;

        -- Insert model_ready features
        INSERT INTO model_ready.accident_features (
            accident_id, severity, hour, day_of_week, month, year, is_weekend, season,
            is_rush_hour, latitude, longitude, number_of_vehicles, number_of_casualties,
            speed_limit, road_type, road_surface, light_conditions, weather_condition,
            urban_rural, junction_type, temperature, precipitation, wind_speed, rain, snowfall,
            police_force
        ) VALUES (
            acc_id, sev_key, 
            floor(random() * 24), floor(random() * 7), 
            floor(random() * 12 + 1), 2023, (random() > 0.7), 'Spring',
            (random() > 0.8), 51.5, -0.1, num_veh, num_cas,
            30, 'Single carriageway', 'Dry', 'Daylight', 'Fine', 'Urban', 'Not at junction',
            15.0, 0.0, 5.0, 0.0, 0.0, 'Metropolitan Police'
        );

    END LOOP;
END $$;
