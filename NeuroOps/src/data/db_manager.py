import os
from .models import init_db, Video, Detection

class DatabaseManager:
    def __init__(self, db_path=None):
        if db_path is None:
            # Default to database/neuroops.db
            base_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
            db_path = os.path.join(base_dir, 'database', 'neuroops.db')
        
        self.Session = init_db(db_path)

    def get_session(self):
        return self.Session()

    def add_video(self, path, filename, checksum=None):
        session = self.get_session()
        try:
            # Check if exists first
            existing = session.query(Video).filter_by(file_path=path).first()
            if existing:
                return existing.id
                
            video = Video(file_path=path, filename=filename, checksum=checksum)
            session.add(video)
            session.commit()
            return video.id
        except Exception as e:
            session.rollback()
            print(f"DB Error: {e}")
            return None
        finally:
            session.close()

    def get_video_by_path(self, path):
        session = self.get_session()
        video = session.query(Video).filter_by(file_path=path).first()
        session.close()
        return video

    def clear_detections_for_video(self, video_id):
        session = self.get_session()
        try:
            session.query(Detection).filter_by(video_id=video_id).delete()
            session.commit()
        except Exception as e:
            session.rollback()
            print(f"DB Error clearing detections: {e}")
        finally:
            session.close()

    def get_path_by_id(self, video_id):
        session = self.get_session()
        try:
            video = session.query(Video).filter_by(id=video_id).first()
            return video.file_path if video else None
        finally:
            session.close()
