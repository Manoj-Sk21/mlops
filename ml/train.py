import numpy as np
import xgboost as xgb
from sklearn.utils.class_weight import compute_sample_weight
import logging

logger = logging.getLogger(__name__)

def get_default_params() -> dict:
    return {
        'n_estimators': 300,
        'max_depth': 6,
        'learning_rate': 0.1,
        'min_child_weight': 3,
        'subsample': 0.8,
        'colsample_bytree': 0.8,
        'objective': 'multi:softprob',
        'num_class': 3,
        'eval_metric': 'mlogloss',
        'random_state': 42
    }

def compute_class_weights(y: np.ndarray) -> np.ndarray:
    """
    Calculate class weights from training data using sklearn compute_sample_weight.
    """
    return compute_sample_weight('balanced', y)

def train_model(X_train, y_train, X_val, y_val, feature_names, params=None) -> xgb.XGBClassifier:
    """
    Train XGBoost model with class imbalance handling.
    """
    if params is None:
        params = get_default_params()
        
    # XGBoost requires labels to be 0-indexed: 0, 1, 2
    # Severity is 1=Fatal, 2=Serious, 3=Slight. Map to 0, 1, 2
    y_train_mapped = y_train - 1
    y_val_mapped = y_val - 1
        
    sample_weight = compute_class_weights(y_train_mapped)
    
    params_with_es = {**params, 'early_stopping_rounds': 20}
    model = xgb.XGBClassifier(**params_with_es)
    
    logger.info("Training XGBoost model...")
    model.fit(
        X_train, y_train_mapped,
        eval_set=[(X_val, y_val_mapped)],
        sample_weight=sample_weight,
        verbose=True
    )
    logger.info("Training complete.")
    
    return model
