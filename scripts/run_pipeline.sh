#!/bin/bash
export AIRFLOW_HOME=$(pwd)/airflow
airflow db migrate
airflow dags trigger traffic_accident_pipeline
