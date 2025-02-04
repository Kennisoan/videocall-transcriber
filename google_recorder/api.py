from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import threading
import logging

from main import GoogleMeetRecorder

app = FastAPI()
logger = logging.getLogger("google_recorder_api")


class JoinRequest(BaseModel):
    meet_url: str


# Global variables to manage recording state
recording_thread = None
recorder = None


@app.on_event("startup")
def startup_event():
    global recorder
    try:
        recorder = GoogleMeetRecorder(headless=True)
        recorder.login_to_google()
        logger.info("Recorder initialized and logged in to Google.")
    except Exception as e:
        logger.error(f"Failed to initialize recorder: {e}")
        raise e


def start_recording_in_background(meet_url: str):
    global recording_thread, recorder
    try:
        recorder.join_meet(meet_url)
    except Exception as e:
        logger.error(f"Failed to record meeting: {e}")
    finally:
        recording_thread = None


@app.post("/join")
def join_meet(request: JoinRequest):
    global recording_thread
    if recording_thread is not None:
        raise HTTPException(
            status_code=400, detail="Recorder is already running a recording.")
    recording_thread = threading.Thread(
        target=start_recording_in_background, args=(request.meet_url,))
    recording_thread.start()
    return {"message": "Recording started"}
