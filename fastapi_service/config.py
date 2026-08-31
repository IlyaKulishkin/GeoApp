import os
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

SECRET_KEY = os.getenv("SECRET_KEY")

ALGORITHM = "HS256"
DATABASE_URL = os.getenv("DATABASE_URL")

PROJECT_NAME = "Artifacts Service"
VERSION = "1.0.0"
