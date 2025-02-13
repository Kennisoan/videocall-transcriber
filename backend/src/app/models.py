from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Text, JSON
from sqlalchemy.orm import relationship
from .database import Base


class Recording(Base):
    __tablename__ = "recordings"

    id = Column(Integer, primary_key=True, index=True)
    created_at = Column(DateTime, default=datetime.now(timezone.utc))
    source = Column(String)
    meeting_name = Column(String, nullable=True)
    filename = Column(String, unique=True, index=True)
    transcript = Column(Text)
    diarized_transcript = Column(JSON)
    speakers = Column(JSON)
    tldr = Column(Text, nullable=True)
    duration = Column(Integer, nullable=True)
