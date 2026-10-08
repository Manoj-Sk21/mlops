-- Analytical views for dashboards and reporting

CREATE OR REPLACE VIEW analytical.severity_distribution AS
SELECT 
    s.severity_label, 
    COUNT(*) as accident_count, 
    ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER(), 2) as percentage 
FROM analytical.fact_accident a
JOIN analytical.dim_severity s ON a.severity_key = s.severity_key
GROUP BY s.severity_label;

CREATE OR REPLACE VIEW analytical.accident_hourly_summary AS
SELECT 
    EXTRACT(HOUR FROM accident_time) as hour, 
    COUNT(*) as total_accidents, 
    SUM(CASE WHEN s.severity_code = 1 THEN 1 ELSE 0 END) as fatal_count, 
    SUM(CASE WHEN s.severity_code = 2 THEN 1 ELSE 0 END) as serious_count, 
    SUM(CASE WHEN s.severity_code = 3 THEN 1 ELSE 0 END) as slight_count, 
    SUM(number_of_casualties) as total_casualties, 
    ROUND(AVG(number_of_vehicles), 2) as avg_vehicles
FROM analytical.fact_accident a
JOIN analytical.dim_severity s ON a.severity_key = s.severity_key
GROUP BY EXTRACT(HOUR FROM accident_time)
ORDER BY hour;

CREATE OR REPLACE VIEW analytical.accident_daily_summary AS
SELECT 
    d.full_date, 
    d.day_name, 
    d.is_weekend, 
    COUNT(*) as total_accidents, 
    SUM(CASE WHEN s.severity_code = 1 THEN 1 ELSE 0 END) as fatal_count,
    SUM(CASE WHEN s.severity_code = 2 THEN 1 ELSE 0 END) as serious_count,
    SUM(CASE WHEN s.severity_code = 3 THEN 1 ELSE 0 END) as slight_count,
    SUM(number_of_casualties) as total_casualties
FROM analytical.fact_accident a
JOIN analytical.dim_date d ON a.date_key = d.date_key
JOIN analytical.dim_severity s ON a.severity_key = s.severity_key
GROUP BY d.full_date, d.day_name, d.is_weekend
ORDER BY d.full_date;

CREATE OR REPLACE VIEW analytical.accident_weather_summary AS
SELECT 
    w.weather_condition, 
    COUNT(*) as total_accidents, 
    SUM(CASE WHEN s.severity_code = 1 THEN 1 ELSE 0 END) as fatal_count,
    SUM(CASE WHEN s.severity_code = 2 THEN 1 ELSE 0 END) as serious_count,
    SUM(CASE WHEN s.severity_code = 3 THEN 1 ELSE 0 END) as slight_count,
    ROUND(AVG(a.number_of_casualties), 2) as avg_casualties_per_accident
FROM analytical.fact_accident a
JOIN analytical.dim_weather w ON a.weather_key = w.weather_key
JOIN analytical.dim_severity s ON a.severity_key = s.severity_key
GROUP BY w.weather_condition
ORDER BY total_accidents DESC;

CREATE OR REPLACE VIEW analytical.accident_road_summary AS
SELECT 
    r.road_type, 
    r.speed_limit, 
    r.road_surface, 
    COUNT(*) as total_accidents, 
    SUM(CASE WHEN s.severity_code = 1 THEN 1 ELSE 0 END) as fatal_count,
    SUM(CASE WHEN s.severity_code = 2 THEN 1 ELSE 0 END) as serious_count,
    SUM(CASE WHEN s.severity_code = 3 THEN 1 ELSE 0 END) as slight_count
FROM analytical.fact_accident a
JOIN analytical.dim_road r ON a.road_key = r.road_key
JOIN analytical.dim_severity s ON a.severity_key = s.severity_key
GROUP BY r.road_type, r.speed_limit, r.road_surface
ORDER BY total_accidents DESC;

CREATE OR REPLACE VIEW analytical.accident_location_hotspots AS
SELECT 
    l.latitude, 
    l.longitude, 
    l.local_authority, 
    l.police_force, 
    COUNT(*) as total_accidents, 
    SUM(CASE WHEN s.severity_code = 1 THEN 1 ELSE 0 END) as fatal_count, 
    SUM(CASE WHEN s.severity_code = 2 THEN 1 ELSE 0 END) as serious_count
FROM analytical.fact_accident a
JOIN analytical.dim_location l ON a.location_key = l.location_key
JOIN analytical.dim_severity s ON a.severity_key = s.severity_key
GROUP BY l.latitude, l.longitude, l.local_authority, l.police_force
ORDER BY total_accidents DESC;

CREATE OR REPLACE VIEW analytical.vehicle_casualty_summary AS
SELECT 
    v.vehicle_type, 
    COUNT(DISTINCT v.id) as total_vehicles, 
    COUNT(DISTINCT v.accident_id) as accidents_involved,
    COUNT(c.id) as casualty_count
FROM analytical.fact_vehicle v
LEFT JOIN analytical.fact_casualty c ON v.accident_id = c.accident_id AND v.vehicle_reference = c.vehicle_reference
GROUP BY v.vehicle_type
ORDER BY accidents_involved DESC;

CREATE OR REPLACE VIEW analytical.monthly_trend AS
SELECT 
    d.year, 
    d.month, 
    COUNT(*) as total_accidents, 
    SUM(CASE WHEN s.severity_code = 1 THEN 1 ELSE 0 END) as fatal_count,
    SUM(CASE WHEN s.severity_code = 2 THEN 1 ELSE 0 END) as serious_count,
    SUM(CASE WHEN s.severity_code = 3 THEN 1 ELSE 0 END) as slight_count
FROM analytical.fact_accident a
JOIN analytical.dim_date d ON a.date_key = d.date_key
JOIN analytical.dim_severity s ON a.severity_key = s.severity_key
GROUP BY d.year, d.month
ORDER BY d.year, d.month;

CREATE OR REPLACE VIEW analytical.weekday_hour_heatmap AS
SELECT 
    d.day_of_week, 
    EXTRACT(HOUR FROM a.accident_time) as hour, 
    COUNT(*) as accident_count
FROM analytical.fact_accident a
JOIN analytical.dim_date d ON a.date_key = d.date_key
GROUP BY d.day_of_week, EXTRACT(HOUR FROM a.accident_time)
ORDER BY d.day_of_week, hour;
