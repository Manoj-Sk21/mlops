"""
Full setup script: creates all DB tables, seeds demo data, trains the ML model.
Run once before launching services.
"""
import os
import sys
import logging

# Ensure project root is on path
ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, ROOT)

from dotenv import load_dotenv
load_dotenv(os.path.join(ROOT, '.env'))

import psycopg2
from sqlalchemy import create_engine

logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s %(message)s')
logger = logging.getLogger(__name__)

DB_HOST = os.getenv('DATABASE_HOST', 'localhost')
DB_PORT = os.getenv('DATABASE_PORT', '5433')
DB_NAME = os.getenv('DATABASE_NAME', 'traffic_accidents')
DB_USER = os.getenv('DATABASE_USER', 'postgres')
DB_PASS = os.getenv('DATABASE_PASSWORD', 'manoj007')

DB_URL = f"postgresql+psycopg2://{DB_USER}:{DB_PASS}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

SQL_FILES = [
    os.path.join(ROOT, 'database', 'schema.sql'),
    os.path.join(ROOT, 'database', 'dimensions.sql'),
    os.path.join(ROOT, 'database', 'fact_tables.sql'),
    os.path.join(ROOT, 'database', 'analytical_views.sql'),
]

SEED_FILE = os.path.join(ROOT, 'database', 'seed_demo.sql')


def get_raw_conn():
    """Raw psycopg2 connection — needed for PL/pgSQL blocks with % characters."""
    return psycopg2.connect(
        host=DB_HOST, port=int(DB_PORT), dbname=DB_NAME,
        user=DB_USER, password=DB_PASS
    )


def run_sql_file_raw(filepath):
    """Run a SQL file using raw psycopg2 (avoids SQLAlchemy % escaping in PL/pgSQL)."""
    logger.info(f"Running SQL: {os.path.basename(filepath)}")
    with open(filepath, 'r', encoding='utf-8') as f:
        sql = f.read()
    conn = get_raw_conn()
    conn.autocommit = True
    try:
        with conn.cursor() as cur:
            cur.execute(sql)
        logger.info(f"  Done: {os.path.basename(filepath)}")
    except Exception as e:
        logger.warning(f"  Warning {os.path.basename(filepath)}: {e}")
    finally:
        conn.close()


def check_seeded():
    try:
        conn = get_raw_conn()
        with conn.cursor() as cur:
            cur.execute("SELECT COUNT(*) FROM analytical.fact_accident")
            result = cur.fetchone()[0]
        conn.close()
        return result > 0, result
    except Exception:
        return False, 0


def main():
    logger.info("=" * 60)
    logger.info("  Traffic Accident Severity - Full Setup")
    logger.info("=" * 60)

    engine = create_engine(DB_URL)

    # Step 1: Schema & tables
    logger.info("\n[1/3] Setting up database schema & tables...")
    for sql_file in SQL_FILES:
        run_sql_file_raw(sql_file)

    # Step 2: Seed demo data
    logger.info("\n[2/3] Seeding demo data...")
    already_seeded, count = check_seeded()
    if already_seeded:
        logger.info(f"  Already seeded ({count} accidents). Skipping.")
    else:
        run_sql_file_raw(SEED_FILE)
        _, count = check_seeded()
        logger.info(f"  Seeded {count} accidents into DB.")

    # Step 3: Train ML model
    logger.info("\n[3/3] Training ML model...")
    model_path = os.path.join(ROOT, 'models', 'model.joblib')
    if os.path.exists(model_path):
        logger.info(f"  Model already exists at: {model_path}. Skipping training.")
    else:
        try:
            from ml.pipeline import run_training_pipeline
            results = run_training_pipeline(engine=engine)
            logger.info(f"  Model trained! Run ID: {results['run_id']}")
            metrics = results.get('metrics', {})
            for k, v in metrics.items():
                if isinstance(v, (int, float)):
                    logger.info(f"     {k}: {v:.4f}")
        except Exception as e:
            logger.error(f"  Training failed: {e}")
            import traceback
            traceback.print_exc()
            raise

    logger.info("\n" + "=" * 60)
    logger.info("  Setup complete! Run run_local.ps1 to start services.")
    logger.info("=" * 60)
    logger.info("\n  Services:")
    logger.info("  MLflow    -> http://localhost:5000")
    logger.info("  FastAPI   -> http://localhost:8000/docs")
    logger.info("  Streamlit -> http://localhost:8501\n")


if __name__ == '__main__':
    main()
