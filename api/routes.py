import uuid
import time
from datetime import datetime
import logging

from fastapi import APIRouter, HTTPException
from .schemas import PredictionRequest, PredictionResponse, HealthResponse
from .model_loader import get_model_manager

router = APIRouter()
logger = logging.getLogger(__name__)


@router.get("/health", response_model=HealthResponse, summary="Health check")
async def health_check():
    """Return service health status and loaded model version."""
    manager = get_model_manager()
    return HealthResponse(
        status="healthy",
        model_loaded=manager.is_loaded(),
        model_version=str(manager.get_version()) if manager.get_version() is not None else "unknown",
        timestamp=datetime.now().isoformat()
    )


@router.post("/predict", response_model=PredictionResponse, summary="Predict accident severity")
async def predict(request: PredictionRequest):
    """
    Predict the severity of a road traffic accident.

    Returns predicted severity class (1=Fatal, 2=Serious, 3=Slight),
    class probabilities, and the model version used.
    """
    req_id = str(uuid.uuid4())
    start_time = time.time()

    manager = get_model_manager()
    if not manager.is_loaded():
        raise HTTPException(status_code=503, detail="Model not loaded — run the ML training pipeline first.")

    try:
        # Build input dict, deriving temporal features from date+time
        input_data = request.model_dump()
        dt = datetime.strptime(f"{request.date} {request.time}", "%Y-%m-%d %H:%M")

        input_data['hour'] = dt.hour
        input_data['day_of_week'] = dt.weekday()   # 0=Monday … 6=Sunday
        input_data['month'] = dt.month
        input_data['year'] = dt.year
        input_data['is_weekend'] = dt.weekday() >= 5
        input_data['is_rush_hour'] = dt.hour in [7, 8, 9, 16, 17, 18]

        # Season from month
        month = dt.month
        if month in [12, 1, 2]:
            input_data['season'] = 'Winter'
        elif month in [3, 4, 5]:
            input_data['season'] = 'Spring'
        elif month in [6, 7, 8]:
            input_data['season'] = 'Summer'
        else:
            input_data['season'] = 'Autumn'

        # Weather numericals come from the request (with defaults if not supplied)
        # request.temperature, .precipitation, .rain, .snowfall, .wind_speed are
        # already in input_data from model_dump() — no override needed.

        prediction = manager.predict(input_data)
        latency_ms = (time.time() - start_time) * 1000

        logger.info(f"Request {req_id}: {prediction['predicted_label']} in {latency_ms:.1f}ms")

        # Log to monitoring (best-effort — don't fail the request if DB is down)
        try:
            from monitoring.latency import LatencyMonitor
            mon = LatencyMonitor()
            mon.log_request(
                request_id=req_id,
                endpoint="/predict",
                method="POST",
                status_code=200,
                latency_ms=latency_ms,
                request_body=input_data,
                response_body=prediction,
                error_message=None,
                model_version=prediction.get('model_version', 'unknown')
            )
        except Exception as mon_err:
            logger.warning(f"Monitoring log failed (non-critical): {mon_err}")

        return PredictionResponse(
            predicted_severity=prediction['predicted_severity'],
            predicted_label=prediction['predicted_label'],
            probabilities=prediction['probabilities'],
            model_version=str(prediction['model_version']),
            request_id=req_id,
            timestamp=prediction['timestamp']
        )

    except HTTPException:
        raise
    except Exception as exc:
        latency_ms = (time.time() - start_time) * 1000
        logger.error(f"Prediction error for request {req_id}: {exc}", exc_info=True)

        # Log failed request to monitoring
        try:
            from monitoring.latency import LatencyMonitor
            LatencyMonitor().log_request(
                request_id=req_id, endpoint="/predict", method="POST",
                status_code=500, latency_ms=latency_ms,
                request_body=request.model_dump(), response_body=None,
                error_message=str(exc), model_version="unknown"
            )
        except Exception:
            pass

        raise HTTPException(status_code=500, detail=f"Prediction failed: {exc}")

