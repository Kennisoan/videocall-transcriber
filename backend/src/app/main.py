from fastapi import FastAPI, Depends, HTTPException
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from . import crud, models, schemas
from .database import Base, engine, get_db
import os

app = FastAPI()

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:1234",
                   "http://localhost:80", "http://localhost"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def startup_event():
    Base.metadata.create_all(bind=engine)


@app.get("/")
def root():
    return {"message": "Hello from the Video Call Transcriber API"}


@app.get("/recordings/", response_model=list[schemas.Recording])
def list_recordings(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    recordings = crud.get_recordings(db, skip=skip, limit=limit)
    # Convert SQLAlchemy models to Pydantic models
    return [schemas.Recording.from_orm(recording) for recording in recordings]


@app.get("/recordings/{recording_id}/audio")
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


@app.get("/recordings/{recording_id}/transcript")
def get_recording_transcript(recording_id: int, db: Session = Depends(get_db)):
    """Download the transcript of a recording as a text file"""
    recording = crud.get_recording(db, recording_id=recording_id)
    if recording is None:
        raise HTTPException(status_code=404, detail="Recording not found")

    if not recording.transcript:
        raise HTTPException(
            status_code=404, detail="No transcript available for this recording")

    # Create a temporary file with the transcript
    temp_dir = "/tmp"  # Use system temp directory
    os.makedirs(temp_dir, exist_ok=True)
    temp_filename = os.path.join(temp_dir, f"transcript_{recording_id}.txt")

    with open(temp_filename, 'w') as f:
        f.write(recording.transcript)

    return FileResponse(
        temp_filename,
        media_type="text/plain",
        filename=f"transcript_{recording.filename}.txt",
        background=lambda: os.remove(temp_filename)  # Clean up after sending
    )


@app.delete("/recordings/{recording_id}", response_model=schemas.DeleteResponse)
def delete_recording(recording_id: int, db: Session = Depends(get_db)):
    """Delete a recording and its associated files"""
    recording = crud.get_recording(db, recording_id=recording_id)
    if recording is None:
        raise HTTPException(status_code=404, detail="Recording not found")

    # Delete the audio file first
    file_path = os.path.join("/recordings", recording.filename)
    try:
        if os.path.exists(file_path):
            os.remove(file_path)
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to delete audio file: {str(e)}")

    # Delete from database using CRUD operation
    if not crud.delete_recording(db, recording_id):
        raise HTTPException(
            status_code=500, detail="Failed to delete recording from database")

    return {"message": "Recording deleted successfully"}
