from datetime import datetime
from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Text
from sqlalchemy.orm import relationship
from .database import Base


class Recording(Base):
    __tablename__ = "recordings"

    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String, unique=True, index=True)
    transcript = Column(Text)
    source = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)
