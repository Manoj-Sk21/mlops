import os
import uuid
import time
import logging
from datetime import datetime
from functools import wraps
from dotenv import load_dotenv
from sqlalchemy import create_engine, text

load_dotenv()

# Logger
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s %(levelname)s [%(name)s] %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S',
)
logger = logging.getLogger('traffic_pipeline')


def get_db_engine():
    """Create and return a SQLAlchemy database engine."""
    return create_engine(
        f"postgresql://{os.getenv('DATABASE_USER', 'postgres')}:{os.getenv('DATABASE_PASSWORD', 'postgres')}"
        f"@{os.getenv('DATABASE_HOST', 'localhost')}:{os.getenv('DATABASE_PORT', '5432')}"
        f"/{os.getenv('DATABASE_NAME', 'traffic_accidents')}",
        pool_pre_ping=True,
    )


def get_data_dirs():
    """Return dict of all data directories, creating them if they don't exist."""
    base = os.getenv('DATA_DIR', os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'data'))
    dirs = {
        'base':        base,
        'raw':         os.path.join(base, 'raw'),
        'staging':     os.path.join(base, 'staging'),
        'cleaned':     os.path.join(base, 'cleaned'),
        'analytical':  os.path.join(base, 'analytical'),
        'model_ready': os.path.join(base, 'model_ready'),
        'rejected':    os.path.join(base, 'rejected'),
    }
    for d in dirs.values():
        os.makedirs(d, exist_ok=True)
    return dirs


def generate_run_id():
    """Generate a unique pipeline run ID."""
    return str(uuid.uuid4())


def log_ingestion(engine, source_name, source_type, status, row_count=None,
                  file_name=None, api_endpoint=None, error_message=None,
                  duration=None, run_id=None):
    """Insert a record into meta.ingestion_log."""
    if engine is None:
        logger.warning('DB engine is None — skipping ingestion log.')
        return
    try:
        with engine.begin() as conn:
            conn.execute(text("""
                INSERT INTO meta.ingestion_log
                    (source_name, source_type, status, row_count, file_name,
                     api_endpoint, error_message, duration_seconds, run_id)
                VALUES
                    (:source_name, :source_type, :status, :row_count, :file_name,
                     :api_endpoint, :error_message, :duration, :run_id)
            """), {
                'source_name':   source_name,
                'source_type':   source_type,
                'status':        status,
                'row_count':     row_count,
                'file_name':     file_name,
                'api_endpoint':  api_endpoint,
                'error_message': error_message,
                'duration':      duration,
                'run_id':        run_id,
            })
    except Exception as exc:
        logger.error(f'Failed to write ingestion log: {exc}')


def log_rejected_record(engine, run_id, source_table, record_data, reason, details=None):
    """Insert a rejected record into meta.rejected_records."""
    if engine is None:
        return
    import json
    try:
        with engine.begin() as conn:
            conn.execute(text("""
                INSERT INTO meta.rejected_records
                    (run_id, source_table, record_data, rejection_reason, rejection_details)
                VALUES
                    (:run_id, :source_table, :record_data::jsonb, :reason, :details)
            """), {
                'run_id':       run_id,
                'source_table': source_table,
                'record_data':  json.dumps(record_data),
                'reason':       reason,
                'details':      details,
            })
    except Exception as exc:
        logger.error(f'Failed to write rejected record: {exc}')


def log_data_quality(engine, run_id, check_name, check_type, table_name,
                     column_name, status, details, records_affected=None):
    """Insert a data quality check result."""
    if engine is None:
        return
    try:
        with engine.begin() as conn:
            conn.execute(text("""
                INSERT INTO meta.data_quality_results
                    (run_id, check_name, check_type, table_name, column_name,
                     status, details, records_affected)
                VALUES
                    (:run_id, :check_name, :check_type, :table_name, :column_name,
                     :status, :details, :records_affected)
            """), {
                'run_id':           run_id,
                'check_name':       check_name,
                'check_type':       check_type,
                'table_name':       table_name,
                'column_name':      column_name,
                'status':           status,
                'details':          details,
                'records_affected': records_affected,
            })
    except Exception as exc:
        logger.error(f'Failed to write data quality result: {exc}')


def log_validation_summary(engine, run_id, validation_type, total_checks,
                           passed, failed, total_records, rejected):
    """Insert a validation summary row."""
    if engine is None:
        return
    try:
        with engine.begin() as conn:
            conn.execute(text("""
                INSERT INTO meta.validation_log
                    (run_id, validation_type, total_checks, passed_checks,
                     failed_checks, total_records, rejected_records)
                VALUES
                    (:run_id, :validation_type, :total_checks, :passed,
                     :failed, :total_records, :rejected)
            """), {
                'run_id':          run_id,
                'validation_type': validation_type,
                'total_checks':    total_checks,
                'passed':          passed,
                'failed':          failed,
                'total_records':   total_records,
                'rejected':        rejected,
            })
    except Exception as exc:
        logger.error(f'Failed to write validation summary: {exc}')


def setup_logging(name='traffic_pipeline', level=logging.INFO):
    """Return a configured logger."""
    log = logging.getLogger(name)
    log.setLevel(level)
    return log


def retry_with_backoff(max_retries=3, base_delay=2):
    """Decorator that retries a function with exponential backoff on exception."""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            last_exc = None
            for attempt in range(max_retries):
                try:
                    return func(*args, **kwargs)
                except Exception as exc:
                    last_exc = exc
                    wait = base_delay * (2 ** attempt)
                    logger.warning(f'{func.__name__} attempt {attempt+1}/{max_retries} failed: {exc}. Retrying in {wait}s...')
                    time.sleep(wait)
            raise last_exc
        return wrapper
    return decorator
