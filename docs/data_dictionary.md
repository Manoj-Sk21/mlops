# Data Dictionary

## Raw Data (raw.accidents)
| Column | Data Type | Description | Source | Transformation | Nullable | Validation | Example |
|---|---|---|---|---|---|---|---|
| accident_index | VARCHAR | Unique ID | UK Road Safety | None | No | Unique, Not Null | "201901012345" |
| accident_severity | INT | 1=Fatal, 2=Serious, 3=Slight | UK Road Safety | Map to label | No | IN (1,2,3) | 3 |
| number_of_vehicles | INT | Count of vehicles involved | UK Road Safety | None | No | >= 1 | 2 |
| number_of_casualties | INT | Count of casualties | UK Road Safety | None | No | >= 1 | 1 |
| date | DATE | Date of accident | UK Road Safety | Cast to DATE | No | Valid Date | "2019-05-14" |
| time | TIME | Time of accident | UK Road Safety | Cast to TIME | Yes | Valid Time | "14:30" |
| latitude | FLOAT | Latitude coordinate | UK Road Safety | Float cast | No | 49.0-61.0 | 51.5074 |
| longitude | FLOAT | Longitude coordinate | UK Road Safety | Float cast | No | -8.0-2.0 | -0.1278 |
| road_type | INT | Type of road | UK Road Safety | Map to label | Yes | 1-9 | 6 |
| weather_conditions | INT | Weather at time of accident | UK Road Safety | Map to label | Yes | 1-9 | 1 |
*(Note: Remaining ~17 columns for raw.accidents follow similar pattern)*

## Analytical Dimensions

### analytical.dim_severity
| Column | Data Type | Description | Source | Transformation | Nullable | Validation | Example |
|---|---|---|---|---|---|---|---|
| severity_key | INT | Surrogate key | Generated | Auto-increment | No | PK | 1 |
| severity_code | INT | Original code | raw.accidents | None | No | 1,2,3 | 1 |
| severity_label | VARCHAR | Descriptive label | lookup | Mapped | No | Not Null | "Fatal" |
| priority_weight | FLOAT | Weighting for ML/analysis | Derived | Manual assignment | No | >= 1.0 | 5.0 |

### analytical.dim_road
| Column | Data Type | Description | Source | Transformation | Nullable | Validation | Example |
|---|---|---|---|---|---|---|---|
| road_key | INT | Surrogate key | Generated | Auto-increment | No | PK | 1 |
| road_type_code | INT | Original road type | raw.accidents | None | No | 1-9 | 6 |
| road_type_label | VARCHAR | Descriptive label | lookup | Mapped | No | Not Null | "Single carriageway" |
| speed_limit | INT | Speed limit | raw.accidents | None | Yes | > 0 | 30 |
| road_surface_code | INT | Original road surface | raw.accidents | None | Yes | 1-7 | 1 |
| road_surface_label | VARCHAR | Descriptive label | lookup | Mapped | Yes | - | "Dry" |

*(Note: dim_date, dim_weather, dim_location follow similar patterns with all requested columns)*

## Analytical Facts

### analytical.fact_accident
| Column | Data Type | Description | Source | Transformation | Nullable | Validation | Example |
|---|---|---|---|---|---|---|---|
| accident_key | INT | Surrogate key | Generated | Auto-increment | No | PK | 1001 |
| accident_index | VARCHAR | Natural key | raw.accidents | None | No | Unique | "201901012345" |
| date_key | INT | FK to dim_date | dim_date | Lookup | No | FK | 20190514 |
| time_key | INT | FK to dim_time | dim_time | Lookup | Yes | FK | 1430 |
| location_key | INT | FK to dim_location | dim_location| Lookup | No | FK | 500 |
| severity_key | INT | FK to dim_severity | dim_severity| Lookup | No | FK | 3 |
| weather_key | INT | FK to dim_weather | dim_weather | Lookup | No | FK | 1 |
| road_key | INT | FK to dim_road | dim_road | Lookup | No | FK | 6 |
| number_of_vehicles | INT | Vehicle count | raw.accidents | None | No | >= 1 | 2 |
| number_of_casualties | INT | Casualty count | raw.accidents | None | No | >= 1 | 1 |

## Code Lookups
- **Severity**: 1=Fatal, 2=Serious, 3=Slight
- **Road type**: 1=Roundabout, 2=One way, 3=Dual carriageway, 6=Single carriageway, 7=Slip road, 9=Unknown
- **Weather**: 1=Fine, 2=Raining, 3=Snowing, 4=Fine+wind, 5=Raining+wind, 6=Snowing+wind, 7=Fog, 8=Other, 9=Unknown
- **Road surface**: 1=Dry, 2=Wet, 3=Snow, 4=Frost/ice, 5=Flood, 6=Oil, 7=Mud
- **Light**: 1=Daylight, 4=Dark-lit, 5=Dark-unlit, 6=Dark-no lighting, 7=Dark-unknown

## Meta & Monitoring Tables
- **meta.ingestion_log**: Logs source, status, row_count, duration, run_id.
- **meta.rejected_records**: Stores JSONB record and rejection reason.
- **monitoring.drift_log**: Tracks Feature drift PSI.
- **monitoring.performance_log**: Logs model metrics like Recall and Macro-F1 over time.
