@echo off
set AIRFLOW_HOME=%cd%\airflow
airflow db migrate
airflow dags trigger traffic_accident_pipeline
