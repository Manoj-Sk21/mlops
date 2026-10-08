import os
import json
import pandas as pd
import numpy as np
from sqlalchemy import text
from typing import Dict, List, Any

class FalseNegativeMonitor:
    def __init__(self, engine=None):
        from . import get_db_engine
        self.engine = engine or get_db_engine()
        self.max_fn_rate = float(os.getenv('MAX_FALSE_NEGATIVE_RATE', '0.15'))

    def log_false_negative(self, prediction_id: str, predicted_severity: int, actual_severity: int, 
                           model_version: str, features: dict, run_id: str) -> None:
        # Severity: 1=Fatal, 2=Serious, 3=Slight
        # False negative: actual is more severe than predicted (lower number is more severe)
        if actual_severity < predicted_severity:
            with self.engine.begin() as conn:
                conn.execute(
                    text("""
                        INSERT INTO monitoring.false_negative_log 
                        (run_id, prediction_id, predicted_severity, actual_severity, 
                         model_version, features, created_at)
                        VALUES (:run_id, :pred_id, :pred_sev, :act_sev, :model_version, :features, NOW())
                    """),
                    {
                        'run_id': run_id,
                        'pred_id': prediction_id,
                        'pred_sev': predicted_severity,
                        'act_sev': actual_severity,
                        'model_version': model_version,
                        'features': json.dumps(features) if features else None
                    }
                )

    def calculate_false_negative_rate(self, y_true: np.ndarray, y_pred: np.ndarray) -> Dict[str, float]:
        # Fatal: actual=1, predicted=2 or 3
        actual_fatal = np.sum(y_true == 1)
        fn_fatal = np.sum((y_true == 1) & (y_pred > 1))
        fatal_fn_rate = fn_fatal / actual_fatal if actual_fatal > 0 else 0.0
        
        # Serious: actual=2, predicted=3
        actual_serious = np.sum(y_true == 2)
        fn_serious = np.sum((y_true == 2) & (y_pred == 3))
        serious_fn_rate = fn_serious / actual_serious if actual_serious > 0 else 0.0
        
        total_more_severe = actual_fatal + actual_serious
        total_fn = fn_fatal + fn_serious
        overall_fn_rate = total_fn / total_more_severe if total_more_severe > 0 else 0.0
        
        return {
            'fatal_fn_rate': float(fatal_fn_rate),
            'serious_fn_rate': float(serious_fn_rate),
            'overall_fn_rate': float(overall_fn_rate),
            'fatal_fn_count': int(fn_fatal),
            'serious_fn_count': int(fn_serious)
        }

    def get_false_negative_trend(self, time_window_days: int = 30) -> pd.DataFrame:
        query = """
            SELECT DATE(created_at) as date, COUNT(*) as fn_count, 
                   SUM(CASE WHEN actual_severity = 1 THEN 1 ELSE 0 END) as fatal_fn,
                   SUM(CASE WHEN actual_severity = 2 THEN 1 ELSE 0 END) as serious_fn
            FROM monitoring.false_negative_log
            WHERE created_at >= NOW() - INTERVAL ':days days'
            GROUP BY DATE(created_at)
            ORDER BY date
        """
        with self.engine.connect() as conn:
            return pd.read_sql(text(query), conn, params={'days': time_window_days})

    def check_fn_alert(self, fn_rate: float) -> Dict[str, Any]:
        alert = fn_rate > self.max_fn_rate
        message = f"False negative rate {fn_rate:.4f} exceeds threshold {self.max_fn_rate}" if alert else "Normal FN rate"
        
        return {
            'alert': alert,
            'fn_rate': fn_rate,
            'threshold': self.max_fn_rate,
            'message': message
        }
