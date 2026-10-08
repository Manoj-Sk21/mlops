import os
import logging
from ml.inference import InferencePipeline

logger = logging.getLogger(__name__)

class ModelManager:
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def initialize(self):
        if self._initialized: 
            return
            
        model_name = os.getenv('MODEL_NAME', 'traffic_accident_severity_model')
        
        try:
            logger.info("Attempting to load model from MLflow registry...")
            self.pipeline = InferencePipeline.from_mlflow(model_name=model_name)
            logger.info("Model loaded from MLflow successfully.")
        except Exception as e:
            logger.warning(f"Failed to load from MLflow: {e}. Falling back to local models.")
            model_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'models')
            model_path = os.path.join(model_dir, 'model.joblib')
            fe_path = os.path.join(model_dir, 'feature_engineer.joblib')
            
            if os.path.exists(model_path) and os.path.exists(fe_path):
                self.pipeline = InferencePipeline(
                    model_path=model_path,
                    feature_engineer_path=fe_path
                )
                logger.info("Local model loaded successfully.")
            else:
                logger.error("No local model found. Prediction will fail.")
                self.pipeline = None
                
        self._initialized = True
    
    def predict(self, input_data: dict) -> dict:
        if not self.is_loaded():
            raise RuntimeError("Model is not loaded.")
        return self.pipeline.predict(input_data)
        
    def get_version(self) -> str:
        if self.is_loaded():
            return self.pipeline.model_version
        return "unknown"
        
    def is_loaded(self) -> bool:
        return self.pipeline is not None

def get_model_manager() -> ModelManager:
    return ModelManager()
