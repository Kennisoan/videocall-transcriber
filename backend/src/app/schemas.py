from pydantic import BaseModel
from datetime import datetime
from typing import Optional


class RecordingBase(BaseModel):
    filename: str
    transcript: Optional[str] = None
    source: str


class RecordingCreate(RecordingBase):
    pass


class Recording(RecordingBase):
    id: int
    created_at: datetime

    class Config:
        orm_mode = True
        json_encoders = {
            datetime: lambda v: v.isoformat() + 'Z'
        }


class DeleteResponse(BaseModel):
    message: str
