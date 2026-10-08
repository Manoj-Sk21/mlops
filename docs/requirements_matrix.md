# Requirements Traceability Matrix

| # | PDF Requirement | Implemented? | Location | Evidence |
|---|----------------|-------------|----------|----------|
| 1 | Integrate accident and weather datasets | ✅ Yes | ingestion/accident_ingestion.py, ingestion/weather_ingestion.py, transformation/weather_join.py | Weather enrichment via Open-Meteo API joined on time+location |
| 2 | Location- and time-aware analytical database | ✅ Yes | database/schema.sql, database/dimensions.sql | PostgreSQL with PostGIS geometry columns (`dim_location`, `dim_date`) |
| 3 | Visualize accident patterns | ✅ Yes | dashboard/pages/ | 5+ meaningful Streamlit views with filters (Plotly, Folium) |
| 4 | MLOps workflow for severity classification | ✅ Yes | ml/pipeline.py, api/main.py, monitoring/ | XGBoost + MLflow + FastAPI + Docker + Monitoring implementation |
| 5 | Raw copy of extracted data | ✅ Yes | data/raw/, raw schema in PostgreSQL | CSV files stored and raw database tables present |
| 6 | Extraction metadata logging | ✅ Yes | database/schema.sql (`meta.ingestion_log`), ingestion/utils.py | Logs source, status, row_count, duration, run_id |
| 7 | Error handling for extraction | ✅ Yes | ingestion/utils.py | Try/except blocks and `retry_with_backoff` decorator |
| 8 | Failed record logging | ✅ Yes | database/schema.sql (`meta.rejected_records`), transformation/validation.py | JSONB record storage with rejection reason |
| 9 | Repeatable ingestion workflow | ✅ Yes | airflow/dags/traffic_accident_pipeline.py | Airflow DAG defined and schedulable |
| 10 | Apache Airflow DAG | ✅ Yes | airflow/dags/traffic_accident_pipeline.py | Full DAG with all ingestion, validation, and transformation tasks |
| 11 | Star schema database design | ✅ Yes | database/schema.sql, database/fact_tables.sql | Implemented 5 dimensions and 3 fact tables with PK/FKs |
| 12 | PostGIS spatial features | ✅ Yes | database/dimensions.sql | Geometry column and spatial index in `dim_location` |
| 13 | Data quality validation rules | ✅ Yes | transformation/validation.py, docs/validation_rules.md | 20+ implemented rules (null checks, bounds, referential integrity) |
| 14 | Weather API enrichment | ✅ Yes | ingestion/weather_ingestion.py | Open-Meteo REST API integration |
| 15 | Geospatial API enrichment | ✅ Yes | ingestion/osm_ingestion.py | OpenStreetMap Overpass API integration |
| 16 | Analytical views/Data Mart | ✅ Yes | database/analytical_views.sql | 5+ pre-aggregated views for dashboard consumption |
| 17 | Dashboard KPI metrics | ✅ Yes | dashboard/app.py | Streamlit overview page with metrics and delta indicators |
| 18 | Dashboard Filters | ✅ Yes | dashboard/components/filters.py | Sidebar filters for date range, severity, and region |
| 19 | ML Model Training (XGBoost) | ✅ Yes | ml/train.py | XGBClassifier with hyperparameter definitions |
| 20 | Handle Class Imbalance | ✅ Yes | ml/train.py | `compute_sample_weight('balanced')` implemented |
| 21 | Chronological Data Split | ✅ Yes | ml/data_prep.py | Ordered split (70/15/15) implemented |
| 22 | Model Evaluation Metrics | ✅ Yes | ml/evaluate.py | Recall, Macro-F1, Confusion Matrix calculated and logged |
| 23 | MLflow Experiment Tracking | ✅ Yes | ml/pipeline.py | `mlflow.start_run()` with params and metrics logged |
| 24 | Model Versioning & Registry | ✅ Yes | ml/pipeline.py | Model registered and transitioned between stages |
| 25 | FastAPI Inference Endpoint | ✅ Yes | api/main.py | `/predict` and `/health` endpoints implemented |
| 26 | Docker Containerization | ✅ Yes | Dockerfile, docker-compose.yml | Multi-container setup for API, MLflow, and Dashboard |
| 27 | Model Monitoring (Drift) | ✅ Yes | monitoring/drift_detection.py | PSI calculated for feature distributions |
| 28 | Retraining Criteria definitions | ✅ Yes | docs/mlops.md, monitoring/retrain_check.py | Configurable thresholds implemented and documented |
| 29 | Comprehensive README | ✅ Yes | README.md | Includes all required 25 sections |
| 30 | Architecture Diagram | ✅ Yes | docs/architecture.md | Mermaid diagram spanning Source to MLOps |
| 31 | Data Dictionary | ✅ Yes | docs/data_dictionary.md | Detailed schema documentation |
| 32 | Unit Testing | ✅ Yes | tests/ | pytest suite covering validations and transformations |

*(Note: Matrix covers the comprehensive requirements set out in the PDF specification. Extend as needed during development.)*
