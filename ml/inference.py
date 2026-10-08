import os
import joblib
import pandas as pd
import numpy as np
from datetime import datetime
import mlflow
import xgboost as xgb
from .features import FeatureEngineer

class InferencePipeline:
    def __init__(self, model_path=None, feature_engineer_path=None, model=None, feature_engineer=None):
        if model is not None and feature_engineer is not None:
            self.model = model
            self.feature_engineer = feature_engineer
        elif model_path and feature_engineer_path:
            self.model = joblib.load(model_path) if not model_path.endswith('.json') else xgb.XGBClassifier().load_model(model_path)
            if not isinstance(self.model, xgb.XGBClassifier) and isinstance(self.model, xgb.Booster):
                # wrap it or keep as booster, though XGBClassifier is expected
                pass
            self.feature_engineer = FeatureEngineer.load(feature_engineer_path)
        else:
            raise ValueError("Must provide either objects or paths to load them.")
            
        self.model_version = 'unknown'
        self.class_names = {0: 'Fatal', 1: 'Serious', 2: 'Slight'}

    @classmethod
    def from_mlflow(cls, model_name: str, stage: str = 'Production'):
        model_uri = f'models:/{model_name}/{stage}'
        model = mlflow.xgboost.load_model(model_uri)
        
        # Load feature engineer from artifacts
        client = mlflow.tracking.MlflowClient()
        versions = client.get_latest_versions(model_name, stages=[stage])
        if not versions:
            raise ValueError(f"No model found for {model_name} in stage {stage}")
        
        run_id = versions[0].run_id
        fe_path = mlflow.artifacts.download_artifacts(run_id=run_id, artifact_path="feature_engineer.joblib")
        feature_engineer = FeatureEngineer.load(fe_path)
        
        instance = cls(model=model, feature_engineer=feature_engineer)
        instance.model_version = versions[0].version
        return instance

    def preprocess(self, input_data: dict) -> np.ndarray:
        df = pd.DataFrame([input_data])
        # Handle parsed time etc if needed, but assuming features match
        X, _ = self.feature_engineer.transform(df)
        return X

    def predict(self, input_data: dict) -> dict:
        X = self.preprocess(input_data)
        
        prediction = self.model.predict(X)[0]
        probabilities = self.model.predict_proba(X)[0]
        
        return {
            'predicted_severity': int(prediction) + 1,  # Convert back from 0,1,2 to 1,2,3
            'predicted_label': self.class_names[int(prediction)],
            'probabilities': {
                'Fatal': float(probabilities[0]),
                'Serious': float(probabilities[1]),
                'Slight': float(probabilities[2])
            },
            'model_version': self.model_version,
            'timestamp': datetime.now().isoformat()
        }

    def predict_batch(self, input_list: list) -> list:
        df = pd.DataFrame(input_list)
        X, _ = self.feature_engineer.transform(df)
        predictions = self.model.predict(X)
        probabilities = self.model.predict_proba(X)
        
        results = []
        for i in range(len(predictions)):
            results.append({
                'predicted_severity': int(predictions[i]) + 1,
                'predicted_label': self.class_names[int(predictions[i])],
                'probabilities': {
                    'Fatal': float(probabilities[i][0]),
                    'Serious': float(probabilities[i][1]),
                    'Slight': float(probabilities[i][2])
                },
                'model_version': self.model_version,
                'timestamp': datetime.now().isoformat()
            })
        return results
