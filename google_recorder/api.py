from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import threading
import logging

from main import GoogleMeetRecorder
from state import RecorderState, set_state, get_state

app = FastAPI()
logger = logging.getLogger("google_recorder_api")


class JoinRequest(BaseModel):
    meet_url: str


# Global variables to manage recording
recording_thread = None
recorder = None


@app.get("/state")
def get_recorder_state():
    return {"state": get_state()}


@app.on_event("startup")
def startup_event():
    global recorder
    try:
        logger.info("Initializing recorder...")
        set_state(RecorderState.INITIALIZING)
        recorder = GoogleMeetRecorder(headless=True)
        recorder.login_to_google()
        logger.info("Recorder initialized and logged in to Google.")
        set_state(RecorderState.READY)
    except Exception as e:
        logger.error(f"Failed to initialize recorder: {e}")
        raise e


def start_recording_in_background(meet_url: str):
    global recording_thread, recorder
    try:
        set_state(RecorderState.JOINING)
        recorder.join_meet(meet_url)
    except Exception as e:
        logger.error(f"Failed to record meeting: {e}")
        set_state(RecorderState.READY)
    finally:
        recording_thread = None


@app.post("/join")
def join_meet(request: JoinRequest):
    global recording_thread
    if recording_thread is not None:
        raise HTTPException(
            status_code=400, detail="Recorder is already running a recording.")
    if get_state() != RecorderState.READY:
        raise HTTPException(
            status_code=400, detail=f"Recorder is not ready. Current state: {get_state()}")
    recording_thread = threading.Thread(
        target=start_recording_in_background, args=(request.meet_url,))
    recording_thread.start()
    return {"message": "Recording started"}
