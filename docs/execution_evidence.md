# Execution Evidence Checklist

| # | Evidence Item | Screenshot Required | Status | Notes |
|---|--------------|--------------------|---------|---------|
| 1 | UK Road Safety data source webpage | Yes | [ ] Pending | Capture browser showing dft.gov.uk download page |
| 2 | Raw CSV files in data/raw/ | Yes | [ ] Pending | Tree command or file explorer view |
| 3 | Airflow DAG graph view | Yes | [ ] Pending | Capture from Airflow UI |
| 4 | Successful Airflow DAG run | Yes | [ ] Pending | Show green success states for all tasks |
| 5 | Data quality validation results | Yes | [ ] Pending | Query `meta.rejected_records` |
| 6 | PostgreSQL tables | Yes | [ ] Pending | Run `\dt analytical.*` in psql |
| 7 | Analytical view query results | Yes | [ ] Pending | Select top 5 rows from a view |
| 8 | Streamlit Overview page | Yes | [ ] Pending | Dashboard landing page |
| 9 | Streamlit Time Analysis page | Yes | [ ] Pending | Dashboard temporal charts |
| 10 | Streamlit Weather & Road page | Yes | [ ] Pending | Dashboard weather correlations |
| 11 | Streamlit Hotspots map | Yes | [ ] Pending | Dashboard Folium map |
| 12 | Streamlit Vehicle & Casualty page | Yes | [ ] Pending | Dashboard vehicle breakdowns |
| 13 | MLflow experiment list | Yes | [ ] Pending | MLflow UI showing runs |
| 14 | MLflow run metrics | Yes | [ ] Pending | Detail view of a run showing F1/Recall |
| 15 | MLflow model registry | Yes | [ ] Pending | Model registered as Production |
| 16 | FastAPI Swagger UI (/docs) | Yes | [ ] Pending | Browser showing OpenAPI spec |
| 17 | FastAPI prediction response | Yes | [ ] Pending | JSON response from /predict |
| 18 | Docker containers running | Yes | [ ] Pending | `docker ps` output |
| 19 | Streamlit prediction page | Yes | [ ] Pending | UI form making inference request |
| 20 | Monitoring drift results | Yes | [ ] Pending | Query or dashboard showing PSI/drift metrics |
| 21 | Test suite results (pytest) | Yes | [ ] Pending | Terminal showing passing tests and coverage |

## Instructions for Capturing
- Ensure timestamps are visible in screenshots if possible.
- Replace the `[ ] Pending` with `[x] Complete` as screenshots are gathered and saved in an `evidence/` folder.
- Embed the screenshots directly below each table item in the final version of this document.
