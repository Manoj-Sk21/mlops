import re
from datetime import datetime
from sqlalchemy import text
from typing import Dict, List, Any

class InputDataQualityMonitor:
    def __init__(self, engine=None):
        from . import get_db_engine
        self.engine = engine or get_db_engine()

    def validate_prediction_input(self, input_data: dict) -> dict:
        errors = []
        warnings = []
        
        # Check required fields
        required_fields = ['latitude', 'longitude', 'speed_limit', 'number_of_vehicles', 
                          'number_of_casualties', 'date', 'time', 'road_type', 'weather_condition']
        
        for field in required_fields:
            if field not in input_data:
                errors.append(f"Missing required field: {field}")
                
        if errors:
            return {'is_valid': False, 'errors': errors, 'warnings': warnings}

        # Validate ranges
        try:
            lat = float(input_data.get('latitude', 0))
            if not (49 <= lat <= 61):
                errors.append(f"Latitude {lat} out of UK range (49-61)")
                
            lon = float(input_data.get('longitude', 0))
            if not (-8 <= lon <= 2):
                errors.append(f"Longitude {lon} out of UK range (-8 to 2)")
                
            speed_limit = int(input_data.get('speed_limit', 0))
            if not (10 <= speed_limit <= 70):
                errors.append(f"Speed limit {speed_limit} out of valid range (10-70)")
                
            vehicles = int(input_data.get('number_of_vehicles', 0))
            if vehicles < 1:
                errors.append(f"Number of vehicles {vehicles} must be >= 1")
                
            casualties = int(input_data.get('number_of_casualties', -1))
            if casualties < 0:
                errors.append(f"Number of casualties {casualties} must be >= 0")
                
        except (ValueError, TypeError) as e:
            errors.append(f"Numeric conversion error: {str(e)}")

        # Validate date and time formats
        date_str = input_data.get('date', '')
        try:
            datetime.strptime(date_str, '%Y-%m-%d')
        except ValueError:
            errors.append(f"Invalid date format: {date_str}. Expected YYYY-MM-DD")
            
        time_str = input_data.get('time', '')
        try:
            datetime.strptime(time_str, '%H:%M')
        except ValueError:
            try:
                datetime.strptime(time_str, '%H:%M:%S')
            except ValueError:
                errors.append(f"Invalid time format: {time_str}. Expected HH:MM or HH:MM:SS")

        # Validate categorical values (basic check)
        valid_road_types = ['Single carriageway', 'Dual carriageway', 'Roundabout', 'One way street', 'Slip road', 'Unknown']
        if input_data.get('road_type') not in valid_road_types:
            warnings.append(f"Unknown road_type: {input_data.get('road_type')}")
            
        valid_weather = ['Fine no high winds', 'Raining no high winds', 'Snowing no high winds', 
                         'Fine + high winds', 'Raining + high winds', 'Snowing + high winds', 'Fog or mist', 'Other', 'Unknown']
        if input_data.get('weather_condition') not in valid_weather:
            warnings.append(f"Unknown weather_condition: {input_data.get('weather_condition')}")

        return {
            'is_valid': len(errors) == 0,
            'errors': errors,
            'warnings': warnings
        }

    def log_quality_check(self, request_id: str, result: dict, engine=None) -> None:
        eng = engine or self.engine
        # In a real system, you might log this to a quality_log table
        # We'll just print or log using standard logger here for simplicity,
        # or execute an insert if table exists.
        pass
