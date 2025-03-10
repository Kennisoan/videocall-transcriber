from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime, timezone
import os
import logging

logger = logging.getLogger(__name__)

Base = declarative_base()


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


class DatabaseManager:
    def __init__(self):
        db_user = os.getenv('POSTGRES_USER', 'myuser')
        db_password = os.getenv('POSTGRES_PASSWORD', 'mypassword')
        db_host = os.getenv('POSTGRES_HOST', 'localhost')
        db_port = os.getenv('POSTGRES_PORT', '5432')
        db_name = os.getenv('POSTGRES_DB', 'mydatabase')

        db_url = f"postgresql://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}"
        self.engine = create_engine(db_url)
        Base.metadata.create_all(self.engine)
        Session = sessionmaker(bind=self.engine)
        self.session = Session()

    def add_recording(self, filename, source, meeting_name="", transcript=None, diarized_transcript=None, speakers=None, created_at=None, duration=None, tldr=None):
        """Add a new recording to the database"""
        try:
            recording = Recording(
                filename=filename,
                source=source,
                meeting_name=meeting_name,
                transcript=transcript,
                diarized_transcript=diarized_transcript,
                speakers=speakers,
                created_at=created_at if created_at is not None else datetime.now(
                    timezone.utc),
                duration=duration,
                tldr=tldr
            )
            self.session.add(recording)
            self.session.commit()

            logger.info(f"Added recording {filename} to database")
            return recording
        except Exception as e:
            logger.error(f"Failed to add recording to database: {str(e)}")
            self.session.rollback()
            raise

    def close(self):
        """Close the database session"""
        if self.session:
            self.session.close()
