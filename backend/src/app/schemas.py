from pydantic import BaseModel
from datetime import datetime
from typing import Optional, List, Dict


class SpeakerInfo(BaseModel):
    name: str
    profile_pic: str
    duration: float


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
    speakers: Optional[Dict[str, SpeakerInfo]] = None

    class Config:
        orm_mode = True
        json_encoders = {
            datetime: lambda v: v.isoformat() + 'Z'
        }


class DeleteResponse(BaseModel):
    message: str


class RecordingList(BaseModel):
    id: int
    created_at: datetime
    source: str
    meeting_name: Optional[str] = None
    filename: str
    duration: Optional[int] = None
    tldr: Optional[str] = None
    speakers: Optional[Dict[str, SpeakerInfo]] = None

    class Config:
        orm_mode = True
        json_encoders = {
            datetime: lambda v: v.isoformat() + 'Z'
        }


class UserBase(BaseModel):
    username: str
    name: Optional[str] = None


class UserCreate(UserBase):
    password: str


class User(UserBase):
    id: int
    is_admin: bool
    created_at: datetime

    class Config:
        orm_mode = True
        json_encoders = {
            datetime: lambda v: v.isoformat() + 'Z'
        }


class UpdateUserName(BaseModel):
    name: str


class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    username: Optional[str] = None


class LoginRequest(BaseModel):
    username: str
    password: str


class UserPermissionBase(BaseModel):
    group_name: str
    can_edit: bool = False


class UserPermissionCreate(UserPermissionBase):
    pass


class UserPermission(UserPermissionBase):
    id: int
    user_id: int
    created_at: datetime

    class Config:
        orm_mode = True
        json_encoders = {
            datetime: lambda v: v.isoformat() + 'Z'
        }


class UserWithPermissions(User):
    permissions: List[UserPermission] = []

    class Config:
        orm_mode = True
