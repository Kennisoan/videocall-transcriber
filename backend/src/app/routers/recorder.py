from fastapi import APIRouter, Depends, HTTPException
import requests
import logging
from pydantic import BaseModel

router = APIRouter(
    prefix="/recorder",
    tags=["recorder"]
)

logger = logging.getLogger(__name__)


class MeetLinkRequest(BaseModel):
    meet_url: str


@router.post("/start")
def forward_recording_request(request: MeetLinkRequest):
    recorder_api_url = "http://meet_recorder:8001/join"
    try:
        r = requests.post(recorder_api_url, json={
                          "meet_url": request.meet_url})
        r.raise_for_status()
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Could not forward recording request: {str(e)}")
    return r.json()


@router.get("/state")
def get_recorder_state():
    recorder_api_url = "http://meet_recorder:8001/state"
    try:
        r = requests.get(recorder_api_url, timeout=5)
        r.raise_for_status()
        return r.json()
    except Exception as e:
        logger.warning(f"Could not get recorder state: {str(e)}")
        return {"state": "unavailable"}
