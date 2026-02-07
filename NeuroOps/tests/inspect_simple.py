import sys
from qdrant_client import QdrantClient

def inspect():
    try:
        print("Connecting to Qdrant...", flush=True)
        # Assuming local path from vector_store or default
        client = QdrantClient(path="./qdrant_storage") 
        
        collection_name = "neuroops_observations"
        
        print(f"Scrolling {collection_name}...", flush=True)
        points, _ = client.scroll(
            collection_name=collection_name,
            limit=10,
            with_payload=True,
            with_vectors=False
        )
        
        print(f"Found {len(points)} points:", flush=True)
        for p in points:
            vid = p.payload.get('video_id')
            cls = p.payload.get('class_name')
            print(f" - ID: {p.id} | VideoID: {vid} (Type: {type(vid)}) | Class: {cls}", flush=True)
            
    except Exception as e:
        print(f"Error: {e}", flush=True)

if __name__ == "__main__":
    inspect()
