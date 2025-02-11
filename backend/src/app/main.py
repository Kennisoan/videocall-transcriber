from fastapi import FastAPI, Depends, HTTPException, Header, Cookie
from fastapi.responses import FileResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from . import crud, models, schemas
from .database import Base, engine, get_db
import os
from pydantic import BaseModel
import requests
from typing import Optional
import logging

app = FastAPI()

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:1234", "http://localhost:3000",
                   "http://localhost:80", "http://localhost"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

GLOBAL_PASSWORD = os.environ.get("APP_GLOBAL_PASSWORD", "supersecret")
# This should be more secure in production
AUTH_TOKEN = os.environ.get("AUTH_TOKEN", "myauthtoken")

logger = logging.getLogger(__name__)


class MeetLinkRequest(BaseModel):
    meet_url: str


def verify_token(x_token: Optional[str] = Header(None), authToken: Optional[str] = Cookie(None)):
    token = x_token or authToken
    if not token or token != AUTH_TOKEN:
        raise HTTPException(status_code=403, detail="Not authenticated")
    return token


@app.on_event("startup")
def startup_event():
    # Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)


@app.get("/")
def root():
    return {"message": "Hello from the Video Call Transcriber API"}


@app.get("/recordings", response_model=list[schemas.Recording])
def list_recordings(skip: int = 0, limit: int = 100, db: Session = Depends(get_db), token: str = Depends(verify_token)):
    recordings = crud.get_recordings(db, skip=skip, limit=limit)
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


@app.delete("/recordings/{recording_id}", response_model=schemas.DeleteResponse)
def delete_recording(recording_id: int, db: Session = Depends(get_db), token: str = Depends(verify_token)):
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


@app.post("/start_recording")
def forward_recording_request(request: MeetLinkRequest, token: str = Depends(verify_token)):
    recorder_api_url = "http://meet_recorder:8001/join"
    try:
        r = requests.post(recorder_api_url, json={
                          "meet_url": request.meet_url})
        r.raise_for_status()
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Could not forward recording request: {str(e)}")
    return r.json()


@app.get("/recorder_state")
def get_recorder_state(token: str = Depends(verify_token)):
    recorder_api_url = "http://meet_recorder:8001/state"
    try:
        # Add timeout to prevent long waits
        r = requests.get(recorder_api_url, timeout=5)
        r.raise_for_status()
        return r.json()
    except Exception as e:
        logger.warning(f"Could not get recorder state: {str(e)}")
        return {"state": "unavailable"}


class LoginRequest(BaseModel):
    password: str


@app.post("/login")
def login(credentials: LoginRequest):
    if credentials.password == GLOBAL_PASSWORD:
        response = JSONResponse({"token": AUTH_TOKEN})
        response.set_cookie(key="authToken", value=AUTH_TOKEN, httponly=True)
        return response
    raise HTTPException(status_code=401, detail="Incorrect password")
