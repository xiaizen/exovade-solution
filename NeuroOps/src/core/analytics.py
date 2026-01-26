from src.data.db_manager import DatabaseManager
from src.data.models import Detection, Video
from sqlalchemy import func

class AnalyticsEngine:
    def __init__(self):
        self.db = DatabaseManager()

    def get_class_distribution(self, video_id):
        """Returns count of detections per class for a video."""
        session = self.db.get_session()
        try:
            results = session.query(
                Detection.class_name, 
                func.count(Detection.id)
            ).filter(
                Detection.video_id == video_id
            ).group_by(
                Detection.class_name
            ).all()
            return dict(results)
        finally:
            session.close()

    def get_object_counts_over_time(self, video_id, interval_seconds=1.0):
        """Returns detected object count per second bucket."""
        # Simple implementation: grouping by integer timestamp
        session = self.db.get_session()
        try:
            # Get all timestamps
            timestamps = session.query(Detection.timestamp).filter(
                Detection.video_id == video_id
            ).all()
            
            # Aggregate in python for simplicity (SQLite math functions vary by version)
            counts = {}
            for (ts,) in timestamps:
                bucket = int(ts // interval_seconds) * interval_seconds
                counts[bucket] = counts.get(bucket, 0) + 1
            
            return sorted(counts.items())
        finally:
            session.close()
