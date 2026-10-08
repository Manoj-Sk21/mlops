import os
import numpy as np
import pandas as pd
from sqlalchemy import text
from typing import Dict, List, Any
from sklearn.metrics import accuracy_score, recall_score, f1_score, confusion_matrix

class PerformanceMonitor:
    def __init__(self, engine=None):
        from . import get_db_engine
        self.engine = engine or get_db_engine()
        self.min_recall = float(os.getenv('MIN_RECALL_THRESHOLD', '0.50'))
        self.min_macro_f1 = float(os.getenv('MIN_MACRO_F1_THRESHOLD', '0.60'))

    def evaluate_performance(self, y_true: np.ndarray, y_pred: np.ndarray, model_version: str) -> Dict:
        acc = accuracy_score(y_true, y_pred)
        macro_recall = recall_score(y_true, y_pred, average='macro', zero_division=0)
        macro_f1 = f1_score(y_true, y_pred, average='macro', zero_division=0)
        
        per_class_recall = recall_score(y_true, y_pred, average=None, zero_division=0).tolist()
        per_class_f1 = f1_score(y_true, y_pred, average=None, zero_division=0).tolist()
        cm = confusion_matrix(y_true, y_pred).tolist()
        
        return {
            'accuracy': float(acc),
            'macro_recall': float(macro_recall),
            'macro_f1': float(macro_f1),
            'per_class_recall': per_class_recall,
            'per_class_f1': per_class_f1,
            'confusion_matrix': cm,
            'model_version': model_version
        }

    def check_performance_degradation(self, current_metrics: Dict) -> Dict:
        alerts = []
        if current_metrics.get('macro_recall', 1.0) < self.min_recall:
            alerts.append(f"Macro recall {current_metrics['macro_recall']:.4f} is below threshold {self.min_recall}")
            
        if current_metrics.get('macro_f1', 1.0) < self.min_macro_f1:
            alerts.append(f"Macro F1 {current_metrics['macro_f1']:.4f} is below threshold {self.min_macro_f1}")
            
        return {
            'degraded': len(alerts) > 0,
            'alerts': alerts
        }

    def log_performance(self, metrics: Dict, model_version: str, dataset_size: int, run_id: str) -> None:
        with self.engine.begin() as conn:
            for metric_name in ['accuracy', 'macro_recall', 'macro_f1']:
                if metric_name in metrics:
                    conn.execute(
                        text("""
                            INSERT INTO monitoring.performance_log 
                            (run_id, model_version, metric_name, metric_value, dataset_size, created_at)
                            VALUES (:run_id, :model_version, :metric_name, :metric_value, :dataset_size, NOW())
                        """),
                        {
                            'run_id': run_id,
                            'model_version': model_version,
                            'metric_name': metric_name,
                            'metric_value': metrics[metric_name],
                            'dataset_size': dataset_size
                        }
                    )

    def get_performance_history(self, model_version: str = None, limit: int = 50) -> pd.DataFrame:
        query = "SELECT * FROM monitoring.performance_log"
        params = {}
        if model_version:
            query += " WHERE model_version = :model_version"
            params['model_version'] = model_version
            
        query += " ORDER BY created_at DESC LIMIT :limit"
        params['limit'] = limit
        
        with self.engine.connect() as conn:
            df = pd.read_sql(text(query), conn, params=params)
        return df

    def check_retraining_needed(self) -> Dict:
        # In a real scenario, this would query recent logs and combine metrics
        # For simplicity, returning a mock structure here assuming a check was run
        return {
            'retraining_needed': False,
            'reasons': [],
            'criteria': {
                'f1_below_threshold': False,
                'recall_below_threshold': False,
                'fn_above_threshold': False,
                'drift_detected': False
            }
        }
