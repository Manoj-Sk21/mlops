import os
import json
import pandas as pd
from sqlalchemy import text
from typing import Dict, Any

class LatencyMonitor:
    def __init__(self, engine=None):
        from . import get_db_engine
        self.engine = engine or get_db_engine()

    def log_request(self, request_id: str, endpoint: str, method: str, status_code: int, 
                    latency_ms: float, request_body: dict, response_body: dict, 
                    error_message: str, model_version: str) -> None:
        with self.engine.begin() as conn:
            conn.execute(
                text("""
                    INSERT INTO monitoring.api_log 
                    (request_id, endpoint, method, status_code, latency_ms, 
                     request_body, response_body, error_message, model_version, created_at)
                    VALUES (:request_id, :endpoint, :method, :status_code, :latency_ms,
                            :req_body, :resp_body, :error, :model_version, NOW())
                """),
                {
                    'request_id': request_id,
                    'endpoint': endpoint,
                    'method': method,
                    'status_code': status_code,
                    'latency_ms': latency_ms,
                    'req_body': json.dumps(request_body) if request_body else None,
                    'resp_body': json.dumps(response_body) if response_body else None,
                    'error': error_message,
                    'model_version': model_version
                }
            )

    def get_latency_stats(self, time_window_hours: int = 24) -> Dict[str, Any]:
        query = """
            SELECT 
                COUNT(*) as total_requests,
                AVG(latency_ms) as avg_latency_ms,
                PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY latency_ms) as p50_latency,
                PERCENTILE_CONT(0.95) WITHIN GROUP (ORDER BY latency_ms) as p95_latency,
                PERCENTILE_CONT(0.99) WITHIN GROUP (ORDER BY latency_ms) as p99_latency,
                SUM(CASE WHEN status_code >= 400 THEN 1 ELSE 0 END) as error_count
            FROM monitoring.api_log
            WHERE created_at >= NOW() - INTERVAL ':hours hours'
        """
        
        with self.engine.connect() as conn:
            result = conn.execute(text(query), {'hours': time_window_hours}).mappings().first()
            
            # Get status code distribution
            status_dist = conn.execute(
                text("""
                    SELECT status_code, COUNT(*) as count 
                    FROM monitoring.api_log 
                    WHERE created_at >= NOW() - INTERVAL ':hours hours'
                    GROUP BY status_code
                """),
                {'hours': time_window_hours}
            ).mappings().all()
            
        stats = dict(result) if result else {}
        stats['error_rate'] = stats.get('error_count', 0) / stats.get('total_requests', 1) if stats.get('total_requests') else 0
        stats['status_code_distribution'] = {str(row['status_code']): row['count'] for row in status_dist}
        
        return stats

    def get_request_history(self, limit: int = 100) -> pd.DataFrame:
        query = """
            SELECT request_id, endpoint, method, status_code, latency_ms, created_at 
            FROM monitoring.api_log 
            ORDER BY created_at DESC LIMIT :limit
        """
        with self.engine.connect() as conn:
            return pd.read_sql(text(query), conn, params={'limit': limit})

    def check_latency_alerts(self, p95_threshold_ms: float = 1000) -> Dict[str, Any]:
        stats = self.get_latency_stats(1) # check last hour
        p95 = stats.get('p95_latency')
        
        is_alert = False
        message = "Normal latency"
        
        if p95 and p95 > p95_threshold_ms:
            is_alert = True
            message = f"High latency alert: p95 is {p95:.2f}ms (threshold: {p95_threshold_ms}ms)"
            
        return {
            'alert': is_alert,
            'p95_latency': p95,
            'threshold_ms': p95_threshold_ms,
            'message': message
        }
