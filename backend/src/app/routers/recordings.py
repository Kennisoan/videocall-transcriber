from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
import os
from fastapi.responses import FileResponse

from ..dependencies import get_db, verify_token
from .. import crud, schemas

router = APIRouter(
    prefix="/recordings",
    tags=["recordings"]
)


@router.get("/", response_model=List[schemas.RecordingList])
def list_recordings(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    token: str = Depends(verify_token)
):
    recordings = crud.get_recordings(db, skip=skip, limit=limit)
    return [schemas.RecordingList.from_orm(recording) for recording in recordings]


@router.get("/{recording_id}", response_model=schemas.Recording)
def get_recording(
    recording_id: int,
    db: Session = Depends(get_db),
    token: str = Depends(verify_token)
):
    recording = crud.get_recording(db, recording_id=recording_id)
    if recording is None:
        raise HTTPException(status_code=404, detail="Recording not found")
    return schemas.Recording.from_orm(recording)


@router.get("/{recording_id}/audio")
def get_recording_audio(recording_id: int, db: Session = Depends(get_db)):
    recording = crud.get_recording(db, recording_id=recording_id)
    if recording is None:
        raise HTTPException(status_code=404, detail="Recording not found")

    file_path = os.path.join("/recordings", recording.filename)
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="Audio file not found")

    return FileResponse(
        file_path,
        media_type="audio/mpeg",
        filename=recording.filename
    )


@router.get("/{recording_id}/transcript")
def get_recording_transcript(recording_id: int, db: Session = Depends(get_db)):
    recording = crud.get_recording(db, recording_id=recording_id)
    if recording is None:
        raise HTTPException(status_code=404, detail="Recording not found")

    if not recording.transcript:
        raise HTTPException(
            status_code=404, detail="No transcript available for this recording")

    temp_dir = "/tmp"
    os.makedirs(temp_dir, exist_ok=True)
    temp_filename = os.path.join(temp_dir, f"transcript_{recording_id}.txt")

    with open(temp_filename, 'w') as f:
        f.write(recording.transcript)

    return FileResponse(
        temp_filename,
        media_type="text/plain",
        filename=f"transcript_{recording.filename}.txt",
        background=lambda: os.remove(temp_filename)
    )


@router.delete("/{recording_id}", response_model=schemas.DeleteResponse)
def delete_recording(
    recording_id: int,
    db: Session = Depends(get_db),
    token: str = Depends(verify_token)
):
    recording = crud.get_recording(db, recording_id=recording_id)
    if recording is None:
        raise HTTPException(status_code=404, detail="Recording not found")

    file_path = os.path.join("/recordings", recording.filename)
    try:
        if os.path.exists(file_path):
            os.remove(file_path)
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to delete audio file: {str(e)}")

    if not crud.delete_recording(db, recording_id):
        raise HTTPException(
            status_code=500, detail="Failed to delete recording from database")

    return {"message": "Recording deleted successfully"}
