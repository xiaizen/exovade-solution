from sqlalchemy import create_engine, Column, Integer, String, Float, ForeignKey, Text, JSON
from sqlalchemy.orm import declarative_base, relationship
from sqlalchemy.orm import sessionmaker
import os

Base = declarative_base()

class Video(Base):
    __tablename__ = 'videos'

    id = Column(Integer, primary_key=True)
    file_path = Column(String, unique=True, nullable=False)
    filename = Column(String, nullable=False)
    duration = Column(Float)
    fps = Column(Float)
    resolution = Column(String) # e.g. "1920x1080"
    checksum = Column(String, unique=True) # md5 hash for uniqueness
    status = Column(String, default="PENDING") # PENDING, PROCESSED, ERROR

    detections = relationship("Detection", back_populates="video", cascade="all, delete-orphan")
    summaries = relationship("SceneSummary", back_populates="video", cascade="all, delete-orphan")

class SceneSummary(Base):
    __tablename__ = 'scene_summaries'
    
    id = Column(Integer, primary_key=True)
    video_id = Column(Integer, ForeignKey('videos.id'))
    timestamp = Column(Float)
    content = Column(String)
    prompt_used = Column(String)
    
    video = relationship("Video", back_populates="summaries")


class Detection(Base):
    __tablename__ = 'detections'

    id = Column(Integer, primary_key=True)
    video_id = Column(Integer, ForeignKey('videos.id'), nullable=False)
    frame_index = Column(Integer, nullable=False)
    timestamp = Column(Float, nullable=False) # Seconds from start
    class_name = Column(String, nullable=False)
    confidence = Column(Float, nullable=False)
    bbox_xyxy = Column(JSON, nullable=False) # Store as [x1, y1, x2, y2]
    embedding_id = Column(String, nullable=True) # UUID for Qdrant point

    video = relationship("Video", back_populates="detections")

def init_db(db_path):
    # Ensure usage of absolute path and forward slashes for Windows compatibility
    db_path = os.path.abspath(db_path).replace('\\', '/')
    
    # Ensure directory exists
    db_dir = os.path.dirname(db_path)
    if not os.path.exists(db_dir):
        os.makedirs(db_dir, exist_ok=True)
        
    engine = create_engine(f'sqlite:///{db_path}')
    Base.metadata.create_all(engine)
    return sessionmaker(bind=engine)
