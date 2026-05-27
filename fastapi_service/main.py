import logging
from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy import text
from sqlalchemy.orm import Session

from fastapi_service.config import PROJECT_NAME, VERSION
from fastapi_service.database import Base, engine, get_db
from fastapi_service.routers import artifacts

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title=PROJECT_NAME, docs_url="/api/docs")

app.include_router(artifacts.router)


@app.on_event("startup")
def startup():
    Base.metadata.create_all(bind=engine)
    logger.info("FastAPI started successfully")


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
