from pydantic import BaseModel, Field, field_validator
from typing import Dict, Optional

VALID_ROAD_TYPES = [
    'Single carriageway', 'Dual carriageway', 'Roundabout',
    'One way street', 'Slip road', 'Unknown'
]
VALID_WEATHER = [
    'Fine no high winds', 'Raining no high winds', 'Snowing no high winds',
    'Fine + high winds', 'Raining + high winds', 'Snowing + high winds',
    'Fog or mist', 'Other', 'Unknown'
]
VALID_ROAD_SURFACES = ['Dry', 'Wet / damp', 'Snow', 'Frost / ice', 'Flood', 'Oil or diesel', 'Mud']
VALID_LIGHT = ['Daylight', 'Darkness - lights lit', 'Darkness - lights unlit', 'Darkness - no lighting']
VALID_URBAN_RURAL = ['Urban', 'Rural']


class PredictionRequest(BaseModel):
    # Core temporal/location
    date: str = Field(..., description="Accident date in YYYY-MM-DD format")
    time: str = Field(..., description="Accident time in HH:MM format")
    latitude: float = Field(..., ge=49.0, le=61.0, description='UK latitude (49–61)')
    longitude: float = Field(..., ge=-8.0, le=2.0, description='UK longitude (-8 to 2)')

    # Road characteristics
    road_type: str = Field(default='Single carriageway', description='Type of road')
    speed_limit: int = Field(default=30, ge=10, le=70, description='Posted speed limit (mph)')
    road_surface: str = Field(default='Dry', description='Road surface condition')
    junction_type: str = Field(default='Not at junction', description='Junction detail')
    light_conditions: str = Field(default='Daylight', description='Light conditions')
    urban_rural: str = Field(default='Urban', description='Urban or Rural area')

    # Traffic context
    number_of_vehicles: int = Field(default=2, ge=1, le=50, description='Number of vehicles involved')
    number_of_casualties: int = Field(default=1, ge=0, le=100, description='Number of casualties')

    # Weather (optional — defaults used when not provided)
    weather_condition: str = Field(default='Fine no high winds', description='Weather condition label')
    temperature: Optional[float] = Field(default=12.0, ge=-20.0, le=45.0, description='Air temperature (°C)')
    precipitation: Optional[float] = Field(default=0.0, ge=0.0, description='Daily precipitation (mm)')
    rain: Optional[float] = Field(default=0.0, ge=0.0, description='Daily rain (mm)')
    snowfall: Optional[float] = Field(default=0.0, ge=0.0, description='Daily snowfall (cm)')
    wind_speed: Optional[float] = Field(default=10.0, ge=0.0, description='Max wind speed (km/h)')

    @field_validator('date')
    @classmethod
    def validate_date(cls, v: str) -> str:
        from datetime import datetime
        try:
            datetime.strptime(v, '%Y-%m-%d')
        except ValueError:
            raise ValueError('date must be in YYYY-MM-DD format')
        return v

    @field_validator('time')
    @classmethod
    def validate_time(cls, v: str) -> str:
        from datetime import datetime
        try:
            datetime.strptime(v, '%H:%M')
        except ValueError:
            raise ValueError('time must be in HH:MM format')
        return v


class PredictionResponse(BaseModel):
    predicted_severity: int
    predicted_label: str
    probabilities: Dict[str, float]
    model_version: str
    request_id: str
    timestamp: str


class HealthResponse(BaseModel):
    status: str
    model_loaded: bool
    model_version: str
    timestamp: str


class ErrorResponse(BaseModel):
    error: str
    detail: str
    request_id: str

