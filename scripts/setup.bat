@echo off
echo Setting up Virtual Environment...
python -m venv venv
call venv\Scripts\activate.bat

echo Installing requirements...
pip install -r requirements.txt

echo Creating data directories...
if not exist data\raw mkdir data\raw
if not exist data\staging mkdir data\staging
if not exist data\cleaned mkdir data\cleaned
if not exist data\analytical mkdir data\analytical
if not exist data\model_ready mkdir data\model_ready
if not exist data\rejected mkdir data\rejected
if not exist models mkdir models

if not exist .env (
    echo Creating .env from .env.example...
    copy .env.example .env
)

echo Setup complete!
