from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Text, JSON, Boolean
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


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=True)
    username = Column(String, unique=True, index=True)
    hashed_password = Column(String)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.now(timezone.utc))

    # Relationship with permissions
    permissions = relationship("UserPermission", back_populates="user")


class UserPermission(Base):
    __tablename__ = "user_permissions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"))
    # This corresponds to meeting_name in recordings
    group_name = Column(String, index=True)
    can_edit = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.now(timezone.utc))

    # Relationship with user
    user = relationship("User", back_populates="permissions")
