from sqlalchemy.orm import Session
from . import models, schemas


def get_recordings(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.Recording).offset(skip).limit(limit).all()


def get_recording(db: Session, recording_id: int):
    return db.query(models.Recording).filter(models.Recording.id == recording_id).first()


def create_recording(db: Session, recording: schemas.RecordingCreate):
    db_recording = models.Recording(**recording.dict())
    db.add(db_recording)
    db.commit()
    db.refresh(db_recording)
    return db_recording


def delete_recording(db: Session, recording_id: int) -> bool:
    """Delete a recording from the database

    Returns:
        bool: True if recording was deleted, False if recording was not found
    """
    recording = get_recording(db, recording_id)
    if recording is None:
        return False

    db.delete(recording)
    db.commit()
    return True
