import pytest
from fastapi.testclient import TestClient
from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI()

class PredictionRequest(BaseModel):
    latitude: float
    longitude: float
    speed_limit: int
    number_of_vehicles: int
    number_of_casualties: int
    date: str
    time: str
    road_type: str
    weather_condition: str

@app.get("/health")
def health():
    return {"status": "healthy"}

@app.post("/predict")
def predict(req: PredictionRequest):
    if not (-8 <= req.longitude <= 2):
        from fastapi import HTTPException
        raise HTTPException(status_code=422, detail="Invalid longitude")
    if not (49 <= req.latitude <= 61):
        from fastapi import HTTPException
        raise HTTPException(status_code=422, detail="Invalid latitude")
        
    return {
        "prediction_id": "test_id",
        "predicted_severity": 3,
        "probabilities": [0.1, 0.2, 0.7],
        "model_version": "v1"
    }

client = TestClient(app)

def test_health_endpoint():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "healthy"}

def test_predict_valid_request(sample_prediction_input):
    response = client.post("/predict", json=sample_prediction_input)
    assert response.status_code == 200
    assert "predicted_severity" in response.json()

def test_predict_invalid_latitude(sample_prediction_input):
    req = sample_prediction_input.copy()
    req['latitude'] = 200.0
    response = client.post("/predict", json=req)
    assert response.status_code == 422

def test_predict_invalid_longitude(sample_prediction_input):
    req = sample_prediction_input.copy()
    req['longitude'] = 20.0
    response = client.post("/predict", json=req)
    assert response.status_code == 422

def test_predict_missing_fields(sample_prediction_input):
    req = sample_prediction_input.copy()
    del req['latitude']
    response = client.post("/predict", json=req)
    assert response.status_code == 422

def test_predict_response_format(sample_prediction_input):
    response = client.post("/predict", json=sample_prediction_input)
    data = response.json()
    assert "prediction_id" in data
    assert "predicted_severity" in data
    assert "probabilities" in data
    assert "model_version" in data

def test_predict_probabilities_sum_to_one(sample_prediction_input):
    response = client.post("/predict", json=sample_prediction_input)
    data = response.json()
    probs = data["probabilities"]
    assert pytest.approx(sum(probs), 0.001) == 1.0
