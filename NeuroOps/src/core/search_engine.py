from src.ai.embedder import ClipEmbedder
from src.data.vector_store import VectorStore
from src.data.db_manager import DatabaseManager

class SearchEngine:
    def __init__(self, collection_suffix="1"):
        self.embedder = ClipEmbedder()
        self.vector_store = VectorStore(collection_suffix=str(collection_suffix)) 
        # self.db = DatabaseManager() 
        # self.db = DatabaseManager()

    def search(self, text_query, limit=10):
        # 1. Convert text to vector
        query_vector = self.embedder.embed_text(text_query)
        
        # 2. Search Qdrant
        results = self.vector_store.search(query_vector, limit=limit)
        
        # 3. Format results
        formatted_results = []
        for hit in results:
            payload = hit.payload
            formatted_results.append({
                "score": hit.score,
                "video_id": payload.get("video_id"),
                "timestamp": payload.get("timestamp"),
                "class_name": payload.get("class_name"),
                "frame_idx": payload.get("frame_idx")
            })
            
        return formatted_results
