# ============================================================
# Traffic Accident Severity — Local Run Script (No Docker)
# ============================================================
# Usage: Right-click -> Run with PowerShell
#        OR: powershell -ExecutionPolicy Bypass -File run_local.ps1
# ============================================================

$ProjectDir = $PSScriptRoot

Write-Host ""
Write-Host "============================================" -ForegroundColor Cyan
Write-Host " Traffic Accident Severity - Starting Up" -ForegroundColor Cyan
Write-Host "============================================" -ForegroundColor Cyan
Write-Host ""

# --- 1. MLflow Tracking Server ---
Write-Host "[1/3] Starting MLflow server on http://localhost:5000 ..." -ForegroundColor Yellow
Start-Process powershell -ArgumentList @(
    "-NoExit",
    "-Command",
    "cd '$ProjectDir'; Write-Host 'MLflow Server' -ForegroundColor Cyan; python -m mlflow server --host 0.0.0.0 --port 5000 --backend-store-uri sqlite:///mlflow.db --default-artifact-root ./mlruns"
) -WindowStyle Normal

Start-Sleep -Seconds 4

# --- 2. FastAPI ---
Write-Host "[2/3] Starting FastAPI on http://localhost:8000 ..." -ForegroundColor Yellow
Start-Process powershell -ArgumentList @(
    "-NoExit",
    "-Command",
    "cd '$ProjectDir'; Write-Host 'FastAPI Server' -ForegroundColor Green; python -m uvicorn api.main:app --host 0.0.0.0 --port 8000 --reload"
) -WindowStyle Normal

Start-Sleep -Seconds 3

# --- 3. Streamlit Dashboard ---
Write-Host "[3/3] Starting Streamlit dashboard on http://localhost:8501 ..." -ForegroundColor Yellow
Start-Process powershell -ArgumentList @(
    "-NoExit",
    "-Command",
    "cd '$ProjectDir'; Write-Host 'Streamlit Dashboard' -ForegroundColor Magenta; python -m streamlit run dashboard/app.py --server.port 8501"
) -WindowStyle Normal

Write-Host ""
Write-Host "============================================" -ForegroundColor Green
Write-Host " All services starting in separate windows!" -ForegroundColor Green
Write-Host "============================================" -ForegroundColor Green
Write-Host ""
Write-Host "  MLflow    -> http://localhost:5000" -ForegroundColor Cyan
Write-Host "  FastAPI   -> http://localhost:8000" -ForegroundColor Green
Write-Host "  API Docs  -> http://localhost:8000/docs" -ForegroundColor Green
Write-Host "  Streamlit -> http://localhost:8501" -ForegroundColor Magenta
Write-Host ""
Write-Host "Press any key to exit this launcher..." -ForegroundColor Gray
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
