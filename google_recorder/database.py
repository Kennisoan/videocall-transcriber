from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime
import os
import logging

logger = logging.getLogger(__name__)

Base = declarative_base()


class Recording(Base):
    __tablename__ = "recordings"
    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String, unique=True, index=True)
    transcript = Column(Text)
    source = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)


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

    def add_recording(self, filename, source, transcript=None):
        """Add a new recording to the database"""
        try:
            # Log the transcript before storing
            if transcript:
                logger.info(
                    "About to store transcript in database. First 1000 chars:")
                # Use repr to see escape sequences
                logger.info(repr(transcript[:1000]))
                logger.info("Number of newlines in transcript: %d",
                            transcript.count('\n'))

            recording = Recording(
                filename=filename,
                source=source,
                transcript=transcript
            )
            self.session.add(recording)
            self.session.commit()

            # Verify what was actually stored
            stored_recording = self.session.query(
                Recording).filter_by(filename=filename).first()
            if stored_recording and stored_recording.transcript:
                logger.info("Stored transcript in database. First 100 chars:")
                logger.info(repr(stored_recording.transcript[:100]))
                logger.info("Number of newlines in stored transcript: %d",
                            stored_recording.transcript.count('\n'))

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
