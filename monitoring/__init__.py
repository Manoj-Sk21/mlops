import os
from sqlalchemy import create_engine
from dotenv import load_dotenv

load_dotenv()

def get_db_engine():
    return create_engine(
        f"postgresql+psycopg2://{os.getenv('DATABASE_USER', 'postgres')}:{os.getenv('DATABASE_PASSWORD', 'postgres')}"
        f"@{os.getenv('DATABASE_HOST', 'localhost')}:{os.getenv('DATABASE_PORT', '5432')}"
        f"/{os.getenv('DATABASE_NAME', 'traffic_accidents')}"
    )

from .data_quality import InputDataQualityMonitor
from .drift import DriftDetector
from .performance import PerformanceMonitor
from .latency import LatencyMonitor
from .false_negatives import FalseNegativeMonitor

__all__ = [
    'get_db_engine',
    'InputDataQualityMonitor',
    'DriftDetector',
    'PerformanceMonitor',
    'LatencyMonitor',
    'FalseNegativeMonitor'
]
