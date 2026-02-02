from qdrant_client import QdrantClient
from qdrant_client.http import models
import os
import uuid

# Singleton instance
_client_instance = None

def get_qdrant_client(path="./qdrant_storage"):
    global _client_instance
    if _client_instance is None:
        _client_instance = QdrantClient(path=path)
    return _client_instance

class VectorStore:
    def __init__(self, collection_suffix="default"):
        self.client = get_qdrant_client()
        self.collection_name = f"neuroops_{collection_suffix}"
        self.identity_collection = "neuroops_identities"
        self.vector_size = 512 
        
        self._init_collection(self.collection_name)
        self._init_collection(self.identity_collection)

    def _init_collection(self, name):
        collections = self.client.get_collections()
        exists = any(c.name == name for c in collections.collections)
        
        if exists:
            # Check for dimension mismatch
            info = self.client.get_collection(name)
            if info.config.params.vectors.size != self.vector_size:
                print(f"[VECTOR STORE] Dimension mismatch for {name} (Expected {self.vector_size}, Got {info.config.params.vectors.size}). Recreating...")
                self.client.delete_collection(name)
                exists = False

        if not exists:
            self.client.create_collection(
                collection_name=name,
                vectors_config=models.VectorParams(
                    size=self.vector_size,
                    distance=models.Distance.COSINE
                )
            )

    def add_embedding(self, vector, metadata):
        return self._add_point(self.collection_name, vector, metadata)

    def add_identity(self, vector, metadata):
        return self._add_point(self.identity_collection, vector, metadata)

    def _add_point(self, collection, vector, metadata):
        point_id = str(uuid.uuid4())
        self.client.upsert(
            collection_name=collection,
            points=[
                models.PointStruct(
                    id=point_id,
                    vector=vector,
                    payload=metadata
                )
            ]
        )
        return point_id

    def search(self, query_vector, limit=5, score_threshold=0.2):
        # Use query_points as it is more robust across versions or local mode
        results = self.client.query_points(
            collection_name=self.collection_name,
            query=query_vector,
            limit=limit,
            score_threshold=score_threshold
        ).points
        return results

    def clear_collection(self):
        """Deletes and recreates the collection to wipe data."""
        self.client.delete_collection(self.collection_name)
        self._init_collection(self.collection_name)
