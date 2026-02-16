from src.data.db_manager import DatabaseManager
from src.data.models import TextDetection

class SearchEngine:
    def __init__(self, collection_suffix="1"):
        # Lazy imports — avoid loading CLIP/qdrant at app startup
        from src.ai.embedder import ClipEmbedder
        from src.data.vector_store import VectorStore

        self.embedder = ClipEmbedder()
        self.vector_store = VectorStore(collection_suffix=str(collection_suffix))
        self.db = DatabaseManager()
        self.video_id = int(collection_suffix) if str(collection_suffix).isdigit() else None

    def search(self, text_query, limit=10):
        # 1. Convert text to vector and search Qdrant
        query_vector = self.embedder.embed_text(text_query)
        vector_results = self.vector_store.search(query_vector, limit=limit)
        
        # 2. Search Text Detections via SQL
        text_results = self._search_internal_text(text_query)

        # 3. Format & Merge results
        formatted_results = []
        
        # Add Text Matches first (High Priority)
        for t in text_results:
            formatted_results.append({
                "score": 1.0, # Exact/Partial text match is high confidence
                "video_id": t.video_id,
                "timestamp": t.timestamp,
                "class_name": f"TEXT: {t.text_content}",
                "frame_idx": t.frame_index
            })

        # Add Vector Matches
        for hit in vector_results:
            payload = hit.payload
            formatted_results.append({
                "score": hit.score,
                "video_id": payload.get("video_id"),
                "timestamp": payload.get("timestamp"),
                "class_name": payload.get("class_name"),
                "frame_idx": payload.get("frame_idx")
            })
            
        return formatted_results[:limit*2] # Return slightly more if mixed

    def _search_internal_text(self, query):
        """
        Simple SQL LIKE search for text detections.
        """
        if not self.video_id:
            return []
            
        session = self.db.get_session()
        try:
            # Case-insensitive search using ilike or equivalent in logic
            # SQLite default is case-insensitive for ASCII, usually.
            results = session.query(TextDetection).filter(
                TextDetection.video_id == self.video_id,
                TextDetection.text_content.ilike(f"%{query}%")
            ).limit(20).all()
            return results
        except Exception as e:
            print(f"Text Search Error: {e}")
            return []
        finally:
            session.close()
