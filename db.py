import os
from sqlalchemy import create_engine
from dotenv import load_dotenv

load_dotenv()

def get_db_engine():
    """
    Creates and returns a SQLAlchemy engine for connecting to the database.
    """
    return create_engine(
        f"postgresql+psycopg2://{os.getenv('DATABASE_USER', 'postgres')}:{os.getenv('DATABASE_PASSWORD', 'postgres')}"
        f"@{os.getenv('DATABASE_HOST', 'localhost')}:{os.getenv('DATABASE_PORT', '5432')}"
        f"/{os.getenv('DATABASE_NAME', 'traffic_accidents')}"
    )
