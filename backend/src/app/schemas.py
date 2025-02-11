from pydantic import BaseModel
from datetime import datetime
from typing import Optional, List, Dict


class TranscriptSegment(BaseModel):
    speaker: str
    text: str
    start: datetime
    end: datetime


class RecordingBase(BaseModel):
    filename: str
    transcript: Optional[str] = None
    source: str


class RecordingCreate(RecordingBase):
    pass


class Recording(RecordingBase):

    id: int
    created_at: datetime
    source: str
    meeting_name: Optional[str] = None
    filename: str
    transcript: Optional[str] = None
    diarized_transcript: Optional[List[TranscriptSegment]] = None
    speakers: Optional[Dict[str, str]] = None

    class Config:
        orm_mode = True
        json_encoders = {
            datetime: lambda v: v.isoformat() + 'Z'
        }


class DeleteResponse(BaseModel):
    message: str
