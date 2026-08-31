import time
from sqlalchemy import create_engine, text

from fastapi_service.config import DATABASE_URL, logger


def get_engine_with_retry(max_retries=10, delay=3):
    for attempt in range(max_retries):
        try:
            engine = create_engine(DATABASE_URL, pool_pre_ping=True)
            with engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            logger.info(f"Successfully connected to database on attempt {attempt + 1}")
            return engine
        except Exception as e:
            logger.warning(f"Database connection attempt {attempt + 1} failed: {e}")
            if attempt < max_retries - 1:
                time.sleep(delay)
            else:
                raise
