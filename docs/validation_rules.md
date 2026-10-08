# Validation Rules

## Validation Strategy
The data validation strategy ensures that only high-quality data enters the analytical and ML layers. Checks are performed at the Staging layer before loading into Cleaned and Analytical layers.

## Error Handling Approach
- **Critical Errors:** Lead to immediate rejection of the record. The record is logged in `meta.rejected_records` for analysis.
- **Warnings:** The problematic field is set to NULL or a default 'Unknown' value, but the record is kept.

## Rules List

| # | Rule Name | Table | Column(s) | Rule | Severity | Action on Failure |
|---|-----------|-------|-----------|------|----------|-------------------|
| 1 | Missing accident_index | accidents | accident_index | NOT NULL | Critical | Reject record |
| 2 | Duplicate accident_index | accidents | accident_index | UNIQUE | Critical | Keep first, reject duplicate |
| 3 | Invalid latitude | accidents | latitude | 49.0 <= lat <= 61.0 | Critical | Reject record |
| 4 | Invalid longitude | accidents | longitude | -8.0 <= lon <= 2.0 | Critical | Reject record |
| 5 | Invalid severity | accidents | accident_severity | IN (1,2,3) | Critical | Reject record |
| 6 | Invalid date | accidents | date | Valid date, 2000-2030 | Warning | Set to NULL |
| 7 | Invalid time | accidents | time | Valid HH:MM | Warning | Set to NULL |
| 8 | Missing vehicles count | accidents | number_of_vehicles | NOT NULL, > 0 | Critical | Reject record |
| 9 | Missing casualties count| accidents | number_of_casualties| NOT NULL, > 0 | Critical | Reject record |
| 10 | Invalid road type | accidents | road_type | IN (1,2,3,6,7,9) | Warning | Set to 9 (Unknown) |
| 11 | Invalid weather | accidents | weather_conditions| IN (1-9) | Warning | Set to 9 (Unknown) |
| 12 | Invalid road surface | accidents | road_surface_conditions| IN (1-7) | Warning | Set to NULL |
| 13 | Invalid light conditions| accidents | light_conditions | IN (1,4,5,6,7) | Warning | Set to NULL |
| 14 | Missing vehicle_reference| vehicles | vehicle_reference | NOT NULL | Critical | Reject record |
| 15 | Invalid vehicle type | vehicles | vehicle_type | Valid code list | Warning | Set to Unknown |
| 16 | Missing casualty_ref | casualties| casualty_reference | NOT NULL | Critical | Reject record |
| 17 | Invalid casualty class | casualties| casualty_class | IN (1,2,3) | Warning | Set to NULL |
| 18 | Invalid casualty severity| casualties| casualty_severity | IN (1,2,3) | Critical | Reject record |
| 19 | Date in future | accidents | date | <= CURRENT_DATE | Critical | Reject record |
| 20 | Unmatched accident FK | vehicles | accident_index | Exists in accidents| Critical | Reject record |

## Rejected Records Process
Records failing critical validation are inserted as JSONB into the `meta.rejected_records` table along with a `rejection_reason` string. A daily report aggregates rejection reasons to help identify upstream data issues.

## Data Quality Metrics
- Percentage of records rejected.
- Distribution of rejection reasons.
- Number of fields imputed (Warnings).
