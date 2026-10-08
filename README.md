# Traffic Accident Severity Analytics and Prediction

## 1. Project Overview
This project is an end-to-end Data Engineering and MLOps individual project focusing on Traffic Accident Severity Analytics and Prediction. It demonstrates a complete data pipeline starting from raw data ingestion (UK Road Safety and weather data), through ETL orchestrated by Apache Airflow, storage in a PostgreSQL/PostGIS database, and visualization via a Streamlit Dashboard. Furthermore, it incorporates an MLOps extension featuring an XGBoost model tracked with MLflow, served via FastAPI, containerized with Docker, and monitored for performance and data drift.

## 2. Objectives
The core objectives of this project are:
1. **Integrate accident and weather datasets** to provide contextual enrichment for analytical insights.
2. **Develop a location- and time-aware analytical database** utilizing PostGIS for spatial queries.
3. **Visualize accident patterns** through an interactive, multi-page dashboard.
4. **Implement an MLOps workflow** for severity classification, including tracking, deployment, and monitoring.

## 3. Architecture
The system architecture follows a layered approach:
- **Data Sources:** External CSVs and APIs.
- **Ingestion & ETL:** Python scripts orchestrated by Apache Airflow for extraction, validation, and transformation.
- **Storage Layer:** PostgreSQL with PostGIS extension, utilizing a Star Schema (Facts and Dimensions).
- **Presentation Layer:** Streamlit Dashboard.
- **MLOps Layer:** XGBoost model training, MLflow for experiment tracking and model registry, FastAPI for serving, and a comprehensive monitoring system.

*For detailed architecture diagrams, refer to [Architecture Documentation](docs/architecture.md).*

## 4. Technologies
| Component | Technology | Description |
|-----------|------------|-------------|
| Language | Python 3.11+ | Primary programming language |
| Data Processing | Pandas | Data manipulation and transformation |
| Database | PostgreSQL 16+ | Relational database management |
| Spatial Extension | PostGIS 3.4+ | Geospatial data support |
| Orchestration | Apache Airflow | Workflow scheduling and monitoring |
| Dashboard | Streamlit, Plotly, Folium | Interactive web application and visualizations |
| Machine Learning | XGBoost, scikit-learn | Model training and evaluation |
| MLOps | MLflow | Experiment tracking and model registry |
| API | FastAPI, Uvicorn | Model inference serving |
| Containerization | Docker, Docker Compose | Service isolation and deployment |
| Testing | pytest | Unit and integration testing |

## 5. Data Sources
- **UK Road Safety Open Data:** Sourced from `data.dft.gov.uk` (Accidents, Vehicles, Casualties).
- **Open-Meteo API:** Provides historical weather data for enrichment based on time and location.
- **OpenStreetMap:** Supplemental spatial data.

## 6. Dataset Access
1. **UK Road Safety Data:** Download the CSV files from the UK government data portal. Extract and place them in `data/raw/`.
2. **Open-Meteo API:** Accessed dynamically during the ETL process via REST API calls. No manual download is required.
3. **OpenStreetMap:** Accessed via Overpass API during ingestion.

## 7. Prerequisites
- Python 3.11 or higher
- PostgreSQL 16+ with PostGIS 3.4+ extension installed
- Docker and Docker Compose
- Git

## 8. Environment Setup
```bash
# Clone the repository
git clone <repository_url>
cd traffic-accident-severity

# Create and activate virtual environment
python -m venv venv
# On Windows:
venv\Scripts\activate
# On Linux/Mac:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Configure environment variables
cp .env.example .env
# Edit .env with your specific configurations
```

## 9. Database Setup
Ensure PostgreSQL is running, then execute the following SQL scripts in order:
```bash
psql -U postgres -f database/schema.sql
psql -U postgres -d accident_db -f database/dimensions.sql
psql -U postgres -d accident_db -f database/fact_tables.sql
psql -U postgres -d accident_db -f database/analytical_views.sql
# Optional: Seed demo data
psql -U postgres -d accident_db -f database/seed_demo.sql
```

## 10. PostGIS Setup
PostGIS must be enabled on the database:
```sql
CREATE EXTENSION IF NOT EXISTS postgis;
-- Verify spatial functions
SELECT postgis_full_version();
```

## 11. Airflow Setup
```bash
export AIRFLOW_HOME=$(pwd)/airflow
airflow db migrate
airflow users create --username admin --firstname Admin --lastname User --role Admin --email admin@example.com
# Start services in separate terminals or as daemons
airflow webserver --port 8080
airflow scheduler
```

## 12. Running Ingestion
To run the ingestion manually:
```bash
# DEMO_MODE config can be set in .env to limit data for testing
python -m ingestion.accident_ingestion
python -m ingestion.weather_ingestion
```

## 13. Running ETL
You can trigger the pipeline via Airflow UI or CLI:
```bash
airflow dags trigger traffic_accident_pipeline
```
Alternatively, run the Python scripts directly for debugging.

## 14. Running Dashboard
```bash
streamlit run dashboard/app.py --server.port 8501
```

## 15. Running ML Training
```bash
python -m ml.pipeline
```
Expected output includes model training progress, evaluation metrics (Recall, Macro-F1), and MLflow run details.

## 16. MLflow Setup
Start the MLflow tracking server:
```bash
mlflow server --backend-store-uri sqlite:///mlflow.db --default-artifact-root ./mlruns --host 0.0.0.0 --port 5000
```
Browse experiments at `http://localhost:5000`.

## 17. Model Registry
Models are logged to the MLflow Model Registry. You can view registered models, compare versions, and promote models to 'Staging' or 'Production' via the MLflow UI or API.

## 18. FastAPI Setup
To run the inference API locally:
```bash
uvicorn api.main:app --host 0.0.0.0 --port 8000 --reload
```
Access the Swagger UI at `http://localhost:8000/docs`.

## 19. Docker Setup
To run the entire MLOps stack (API, MLflow, Dashboard):
```bash
docker-compose up -d
```
Service descriptions:
- `api`: FastAPI inference service.
- `mlflow`: Tracking server.
- `dashboard`: Streamlit application.

## 20. Monitoring
Monitoring scripts track data drift and model performance over time. Logs are written to the `monitoring` schema in the database. Dashboards display drift metrics and false-negative rates.

## 21. Retraining
Retraining is triggered when criteria are met (e.g., Macro-F1 < 0.60, Feature drift PSI > 0.20).
```bash
python -m ml.retrain_check
```

## 22. Testing
Run the test suite:
```bash
pytest tests/ -v --cov
```
Tests cover data validation, transformations, model predictions, and API endpoints.

## 23. Troubleshooting
- **Database Connection:** Check credentials in `.env` and ensure PostgreSQL is running.
- **Airflow DAG not appearing:** Ensure `AIRFLOW_HOME` is set correctly and DAGs are in the `dags` folder.
- **Port Conflicts:** Modify ports in `docker-compose.yml` or `.env` if 8000, 8501, or 5000 are in use.

## 24. Project Demonstration Steps
1. Show Raw Data (`data/raw/`).
2. Run Database Setup.
3. Execute Airflow Pipeline.
4. Verify Data Quality Results.
5. Start and interact with the Streamlit Dashboard.
6. Execute ML Training Pipeline.
7. Show MLflow UI (Experiments & Registry).
8. Start FastAPI and demonstrate Swagger UI prediction.
9. Show Monitoring logs.

## 25. Folder Structure
```text
traffic-accident-severity/
├── airflow/            # Airflow DAGs and plugins
├── api/                # FastAPI application
├── dashboard/          # Streamlit dashboard
├── data/               # Raw, processed, and model-ready data
├── database/           # SQL schemas and scripts
├── docs/               # Project documentation
├── ingestion/          # Data extraction scripts
├── ml/                 # ML pipeline and feature engineering
├── monitoring/         # Drift detection and monitoring
├── tests/              # Pytest test suite
├── transformation/     # Data cleaning and enrichment
├── docker-compose.yml  # Docker composition
├── requirements.txt    # Python dependencies
└── README.md           # This file
```
