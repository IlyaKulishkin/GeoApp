from typing import List
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError

from ..config import logger
from ..database import get_db, Artifact, DjangoUser
from ..schemas import ArtifactCreate, ArtifactUpdate, ArtifactOut
from ..dependencies import get_current_user


router = APIRouter(prefix="/api/artifacts", tags=["artifacts"])


@router.post("/", response_model=ArtifactOut, status_code=status.HTTP_201_CREATED)
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


@router.get("/", response_model=List[ArtifactOut])
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


@router.patch("/{art_id}", response_model=ArtifactOut)
def update_artifact(
    art_id: int,
    data: ArtifactUpdate,
    user: DjangoUser = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    try:
        obj = db.query(Artifact).filter(
            Artifact.id == art_id,
            Artifact.owner_id == user.id
        ).first()

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


@router.delete("/{art_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_artifact(
    art_id: int,
    user: DjangoUser = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    obj = db.query(Artifact).filter(
        Artifact.id == art_id,
        Artifact.owner_id == user.id
    ).first()

    if not obj:
        raise HTTPException(404, "Artifact not found")

    try:
        db.delete(obj)
        db.commit()
    except Exception:
        db.rollback()
        raise HTTPException(500, "Database error")
