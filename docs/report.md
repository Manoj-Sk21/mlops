# Traffic Accident Severity Analytics — Project Report (Part 1)

## 1. Introduction
Traffic accidents remain a significant public health issue globally. In the UK, extensive data on road safety is collected to understand the factors contributing to accidents. This project aims to ingest, clean, enrich, and analyze the UK Road Safety Open Data. The ultimate goal is to build an end-to-end data pipeline and a predictive MLOps workflow to identify the severity of accidents, providing actionable insights for policymakers and safety planners.

## 2. Problem Understanding
Accident severity is influenced by a complex interplay of temporal, spatial, environmental, and behavioral factors. Predicting severity helps emergency services allocate resources effectively and allows urban planners to identify high-risk zones. The primary questions addressed are: What spatial/temporal patterns exist? How does weather impact severity? Can we accurately predict severity using historical data?

## 3. Project Objectives
1. **Integrate accident and weather datasets** to provide contextual enrichment.
2. **Develop a location- and time-aware analytical database** (using PostGIS).
3. **Visualize accident patterns** via an interactive Streamlit dashboard.
4. **Implement a comprehensive MLOps workflow** for severity classification.

## 4. Data Sources
- **UK Road Safety Open Data:** 
  - URL: `https://data.dft.gov.uk/road-accidents-safety-data/`
  - Description: Contains tables for accidents, vehicles, and casualties.
  - Extraction: HTTP download of CSVs during ingestion.
- **Open-Meteo API:**
  - URL: `https://api.open-meteo.com/v1/forecast`
  - Description: Historical weather data.
  - Variables: Temperature, precipitation, weather codes.
  - Extraction: REST API called using lat/lon and time from the accident data.
- **OpenStreetMap:**
  - URL: `https://overpass-api.de/api/interpreter`
  - Description: Provides granular road network details.
  - Extraction: Overpass API queries.

## 5. Architecture
The architecture spans ingestion, transformation, storage, and consumption layers. An Airflow DAG orchestrates extraction scripts that pull data into a raw area. Transformation processes clean and validate this data, enriching it with Open-Meteo data before loading it into a PostgreSQL/PostGIS Data Mart structured as a Star Schema. The consumption layer includes a Streamlit Dashboard and an ML pipeline.
*Reference: [architecture.md](architecture.md)*

## 6. Data Ingestion
Ingestion scripts are robust, featuring try/except blocks and retry mechanisms with exponential backoff for API calls. Metadata about each run (start time, duration, rows extracted, status) is logged in `meta.ingestion_log`. The extraction is scheduled via Apache Airflow.

## 7. ETL Pipeline
The ETL pipeline handles standardizing dates, casting data types, and mapping numerical codes to descriptive labels (e.g., Severity 1 -> 'Fatal'). Weather enrichment involves joining Open-Meteo API responses based on accident timestamp and location. 

## 8. Data Validation
Over 20 validation rules are enforced. Critical failures (e.g., missing coordinates or out-of-bounds dates) result in the record being sent to `meta.rejected_records` as JSONB. Warnings result in imputation or default values.

## 9. Database Design
The analytical database uses a Star Schema in PostgreSQL. 
- **Facts:** `fact_accident`, `fact_vehicle`, `fact_casualty`.
- **Dimensions:** `dim_date`, `dim_location` (with PostGIS geometry), `dim_weather`, `dim_road`, `dim_severity`.

## 10. Analytical Data Mart
Views are created to pre-aggregate data for the dashboard, such as `vw_accidents_by_lsoa` and `vw_severity_by_weather`. This optimizes query performance.

## 11. Dashboard
The Streamlit dashboard includes 5 distinct views:
1. Overview KPIs
2. Time Analysis (Trends by year/month/hour)
3. Weather & Road conditions
4. Hotspots Map (Folium integration)
5. Vehicle & Casualty breakdown

## 12. Results and Interpretation
[PLACEHOLDER: Replace with actual results after pipeline execution]
Initial analysis shows strong correlations between adverse weather conditions, specific road types (e.g., single carriageways), and higher severity rates. Temporal analysis highlights peaks during rush hours.

## 13. Pipeline Execution Evidence
[PLACEHOLDER: Replace with actual screenshots after execution]
Reference the [Execution Evidence Checklist](execution_evidence.md) for details on successful pipeline runs.

## 14. Limitations
- **Data Completeness:** Historical data may have reporting biases.
- **API Limits:** Free tiers for Open-Meteo restrict bulk processing rates.
- **Demo Mode:** The pipeline often runs on a subset of data to save time during development.

## 15. Conclusion
Part 1 successfully establishes a resilient, automated data engineering pipeline. The Star Schema and enriched data provide a solid foundation for robust analytical querying and future predictive modeling.

## 16. Future Work / Part 2 MLOps Extension
Part 2 extends this foundation by engineering features for an XGBoost classification model to predict accident severity. The workflow will incorporate MLflow for experiment tracking, FastAPI for real-time inference, Docker for containerization, and a robust monitoring setup for data drift and model performance evaluation.
