import os
import joblib
from datetime import datetime
import mlflow
import logging

from .data import load_model_ready_data, split_data, get_class_distribution
from .features import FeatureEngineer
from .train import train_model, get_default_params
from .evaluate import evaluate_model, log_metrics_to_mlflow

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def run_training_pipeline(engine=None) -> dict:
    """Run the complete ML training pipeline."""
    
    # 1. Load data
    df = load_model_ready_data(engine)
    if df is None or df.empty:
        raise ValueError("No data loaded.")
        
    logger.info(f'Loaded {len(df)} records')
    
    # 2. Show class distribution
    dist = get_class_distribution(df)
    
    # 3. Split data chronologically
    train_df, val_df, test_df = split_data(df)
    
    # 4. Feature engineering
    fe = FeatureEngineer()
    X_train, feature_names = fe.fit_transform(train_df)
    y_train = train_df['severity'].values
    
    X_val, _ = fe.transform(val_df)
    y_val = val_df['severity'].values
    
    X_test, _ = fe.transform(test_df)
    y_test = test_df['severity'].values
    
    # 5. MLflow experiment — use remote server if available, else local sqlite DB
    os.environ['MLFLOW_ALLOW_FILE_STORE'] = 'true'
    tracking_uri = os.getenv('MLFLOW_TRACKING_URI', 'http://localhost:5000')
    try:
        import socket
        host = tracking_uri.split('//')[1].split(':')[0]
        port = int(tracking_uri.split(':')[-1])
        s = socket.create_connection((host, port), timeout=2)
        s.close()
    except Exception:
        tracking_uri = 'sqlite:///mlflow.db'
        logger.info('MLflow server not reachable — using local sqlite tracking (sqlite:///mlflow.db)')
    mlflow.set_tracking_uri(tracking_uri)
    mlflow.set_experiment(os.getenv('MLFLOW_EXPERIMENT_NAME', 'traffic-accident-severity'))
    
    with mlflow.start_run(run_name=f'xgboost_{datetime.now().strftime("%Y%m%d_%H%M%S")}'):
        # 6. Train
        params = get_default_params()
        model = train_model(X_train, y_train, X_val, y_val, feature_names, params)
        
        # 7. Evaluate
        metrics = evaluate_model(model, X_test, y_test, feature_names)
        
        # 8. Log to MLflow
        artifacts_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'artifacts')
        log_metrics_to_mlflow(metrics, params, model, fe, artifacts_dir)
        
        # 9. Save model locally
        model_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'models')
        os.makedirs(model_dir, exist_ok=True)
        joblib.dump(model, os.path.join(model_dir, 'model.joblib'))
        fe.save(os.path.join(model_dir, 'feature_engineer.joblib'))
        
        # 10. Register model
        model_uri = f'runs:/{mlflow.active_run().info.run_id}/model'
        model_name = os.getenv('MODEL_NAME', 'traffic_accident_severity_model')
        try:
            result = mlflow.register_model(model_uri, model_name)
            client = mlflow.tracking.MlflowClient()
            client.transition_model_version_stage(model_name, result.version, 'Production')
        except Exception as e:
            logger.warning(f'Model registration note: {e}')
            
        return {'metrics': metrics, 'model_path': model_dir, 'run_id': mlflow.active_run().info.run_id}

if __name__ == '__main__':
    run_training_pipeline()
