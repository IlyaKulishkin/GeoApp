import logging
import threading
import asyncio
from contextlib import asynccontextmanager
from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy import text
from sqlalchemy.orm import Session

from fastapi_service.config import PROJECT_NAME, VERSION
from fastapi_service.database import Base, engine, get_db
from fastapi_service.routers import artifacts
from fastapi_service.rabbit_consumer import start_consumer

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)
    logger.info("FastAPI started successfully")

    stop_event = threading.Event()
    loop = asyncio.get_running_loop()
    consumer_task = loop.run_in_executor(None, start_consumer, stop_event)
    logger.info("RabbitMQ consumer task started")
    yield
    logger.info("Stopping RabbitMQ consumer...")
    stop_event.set()
    await asyncio.wait_for(consumer_task, timeout=5.0)


app = FastAPI(
    title=PROJECT_NAME,
    docs_url="/api/docs",
    lifespan=lifespan
)

app.include_router(artifacts.router)


@app.get("/")
def root():
    return {
        "service": PROJECT_NAME,
        "version": VERSION,
        "docs": "/api/docs",
        "health": "/health"
    }


@app.get("/health")
def health(db: Session = Depends(get_db)):
    try:
        db.execute(text("SELECT 1"))
        return {
            "status": "ok",
            "database": "connected"
        }
    except Exception:
        raise HTTPException(
            status_code=503,
            detail="Database unavailable"
        )
