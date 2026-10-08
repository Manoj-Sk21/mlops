# Architecture Overview

## Overview
This document outlines the architecture for the Traffic Accident Severity Analytics and Prediction project. The architecture is designed to handle the end-to-end lifecycle of data, from ingestion to model serving and monitoring.

## Complete Architecture Diagram

```mermaid
graph TD
  subgraph Sources
    A[UK Road Safety CSVs] 
    B[Open-Meteo API]
    C[OpenStreetMap]
  end
  
  subgraph Ingestion
    D[accident_ingestion.py]
    E[weather_ingestion.py]
    F[osm_ingestion.py]
  end
  
  subgraph Raw Storage
    G[Raw Files / DB Tables]
  end
  
  subgraph Orchestration
    H[Apache Airflow]
  end
  
  subgraph Transformation
    I[Staging Layer]
    J[Data Quality Checks]
    K[Cleaned Layer]
    L[Weather Join]
  end
  
  subgraph Database
    M[(PostgreSQL/PostGIS)]
    N[Analytical Data Mart]
  end
  
  subgraph Presentation
    O[Streamlit Dashboard]
  end
  
  subgraph MLOps
    P[Model-Ready Data]
    Q[Feature Engineering]
    R[XGBoost Training]
    S[MLflow Tracking]
    T[Model Registry]
    U[FastAPI Service]
    V[Docker Container]
  end
  
  subgraph Monitoring
    W[Drift Detection]
    X[Performance Monitoring]
    Y[Retraining Trigger]
  end

  A --> D
  B --> E
  C --> F
  D --> G
  E --> G
  F --> G
  G --> I
  I --> J
  J --> K
  K --> L
  L --> M
  M --> N
  N --> O
  N --> P
  P --> Q
  Q --> R
  R --> S
  S --> T
  T --> U
  U --> V
  V --> O
  U --> W
  W --> X
  X --> Y
  Y --> P
  
  H -.-> Ingestion
  H -.-> Transformation
```

## Data Flow Diagram
```mermaid
graph LR
  A[Raw Data] --> B[Data Validation]
  B -->|Valid| C[Transformation]
  B -->|Invalid| D[Rejected Records]
  C --> E[Data Mart]
  E --> F[Feature Store]
  F --> G[Model Inference]
```

## Database Schema Diagram
```mermaid
erDiagram
  FACT_ACCIDENT {
    int accident_key PK
    int date_key FK
    int location_key FK
    int weather_key FK
    int severity_key FK
    int road_key FK
    int number_of_vehicles
    int number_of_casualties
  }
  DIM_DATE {
    int date_key PK
    date full_date
    int year
    int month
    int day
    int day_of_week
  }
  DIM_LOCATION {
    int location_key PK
    float latitude
    float longitude
    geometry geom
    string lsoa_code
  }
  DIM_WEATHER {
    int weather_key PK
    string weather_conditions
    float temperature
    float precipitation
  }
  DIM_SEVERITY {
    int severity_key PK
    string severity_label
  }
  DIM_ROAD {
    int road_key PK
    string road_type
    string speed_limit
  }
  
  FACT_ACCIDENT ||--|| DIM_DATE : "occurs on"
  FACT_ACCIDENT ||--|| DIM_LOCATION : "occurs at"
  FACT_ACCIDENT ||--|| DIM_WEATHER : "has weather"
  FACT_ACCIDENT ||--|| DIM_SEVERITY : "has severity"
  FACT_ACCIDENT ||--|| DIM_ROAD : "on road"
```

## Technology Stack
| Component | Technology |
|-----------|------------|
| Backend | Python 3.11+ |
| Database | PostgreSQL 16+, PostGIS 3.4+ |
| Orchestration | Apache Airflow |
| Visualization | Streamlit, Plotly, Folium |
| ML Framework | XGBoost, scikit-learn |
| MLOps | MLflow, FastAPI, Docker |

## Layer Descriptions
- **Source:** External datasets (CSVs, APIs).
- **Ingestion:** Python scripts fetching data.
- **Raw:** Untouched data as it arrives.
- **Staging:** Initial loading zone, basic type casting.
- **Cleaned:** Data post-validation and standardization.
- **Analytical:** Star schema optimized for querying.
- **Model-Ready:** Flattened data with engineered features for ML.

## MLOps Architecture
The MLOps pipeline encompasses model training using XGBoost, experiment tracking and model versioning via MLflow, and serving through a containerized FastAPI application. It includes automated pipelines for feature engineering and retraining.

## Monitoring Architecture
Monitoring tracks data drift (e.g., Population Stability Index for feature distributions) and model performance (e.g., Recall, False Negatives). Metrics are logged to the database, and alerts trigger automated retraining when thresholds are breached.
