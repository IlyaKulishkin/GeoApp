import os
from datetime import datetime, timezone
from typing import List, Optional
from fastapi import FastAPI, Depends, HTTPException, Query
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, Field
from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime, text
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker
from sqlalchemy.exc import SQLAlchemyError
from jose import jwt, JWTError
import time
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

SECRET_KEY = os.getenv("SECRET_KEY")
if not SECRET_KEY:
    SECRET_KEY = "django-insecure-nh)1yxiocniuod6tstdav@q)#xq+j^(096y-qq4yfv&1b8ko_&"
    logger.warning("SECRET_KEY not set, using default key for development!")

ALGORITHM = "HS256"
DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    DATABASE_URL = "postgresql://geouser:geopass@db:5432/geopoints"
    logger.warning("DATABASE_URL not set, using default key for development!")


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


engine = get_engine_with_retry()
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Base(DeclarativeBase):
    pass


class DjangoUser(Base):
    __tablename__ = "auth_user"
    id = Column(Integer, primary_key=True)


class Artifact(Base):
    __tablename__ = "artifacts_fastapi"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    owner_id = Column(Integer, nullable=False)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))


class ArtifactCreate(BaseModel):
    name: str = Field(..., min_length=1)
    description: Optional[str] = None


class ArtifactUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None


class ArtifactOut(BaseModel):
    id: int
    name: str
    description: Optional[str]
    owner_id: int
    created_at: datetime

    class Config:
        from_attributes = True


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


security = HTTPBearer()


async def get_current_user(
        credentials: HTTPAuthorizationCredentials = Depends(security),
        db: Session = Depends(get_db)):
    token = credentials.credentials
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = payload.get("user_id")
        if not user_id:
            raise HTTPException(401, "Invalid token")
    except JWTError:
        raise HTTPException(401, "Invalid token")

    user = db.query(DjangoUser).filter(DjangoUser.id == user_id).first()
    if not user:
        raise HTTPException(401, "User not found")
    return user


app = FastAPI(title="Artifacts Service", docs_url="/api/docs")


@app.on_event("startup")
def startup():
    Base.metadata.create_all(bind=engine)


@app.get("/")
def root():
    return {
        "service": "Artifacts API",
        "version": "1.0.0",
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


@app.post("/api/artifacts", response_model=ArtifactOut, status_code=201)
def create_artifact(
        art: ArtifactCreate,
        user: DjangoUser = Depends(get_current_user),
        db: Session = Depends(get_db)
):
    obj = Artifact(name=art.name, description=art.description, owner_id=user.id)
    try:
        db.add(obj)
        db.commit()
        db.refresh(obj)
        return obj

    except SQLAlchemyError as e:
        db.rollback()
        logger.exception(f"Failed to create artifact for user {user.id}: {e}")
        raise HTTPException(500, "Database error")


@app.get("/api/artifacts", response_model=List[ArtifactOut])
def list_artifacts(
        limit: int = Query(20, ge=1, le=100),
        offset: int = Query(0, ge=0),
        user: DjangoUser = Depends(get_current_user),
        db: Session = Depends(get_db)
):
    try:
        return (
            db.query(Artifact)
            .filter(Artifact.owner_id == user.id)
            .offset(offset)
            .limit(limit)
            .all()
        )

    except SQLAlchemyError as e:
        logger.exception(f"Failed to list artifacts for user {user.id}: {e}")

        raise HTTPException(500, "Database error")


@app.patch("/api/artifacts/{art_id}", response_model=ArtifactOut)
def update_artifact(
        art_id: int,
        data: ArtifactUpdate,
        user: DjangoUser = Depends(get_current_user),
        db: Session = Depends(get_db)
):
    try:
        obj = (
            db.query(Artifact).
            filter(
                Artifact.id == art_id,
                Artifact.owner_id == user.id)
            .first()
        )

        if not obj:
            raise HTTPException(404, "Artifact not found")

        update_data = data.model_dump(exclude_unset=True)

        for field, value in update_data.items():
            setattr(obj, field, value)

        db.commit()
        db.refresh(obj)
        return obj

    except SQLAlchemyError as e:
        db.rollback()
        logger.exception(f"Failed to update artifact {art_id}: {e}")
        raise HTTPException(500, "Database error")


@app.delete("/api/artifacts/{art_id}", status_code=204)
def delete_artifact(
        art_id: int,
        user: DjangoUser = Depends(get_current_user),
        db: Session = Depends(get_db)
):
    obj = (
        db.query(Artifact).
        filter(
            Artifact.id == art_id,
            Artifact.owner_id == user.id)
        .first()
    )

    if not obj:
        raise HTTPException(404, "Artifact not found")

    try:
        db.delete(obj)
        db.commit()
    except Exception:
        db.rollback()
        raise HTTPException(500, "Database error")