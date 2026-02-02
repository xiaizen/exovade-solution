from qdrant_client import QdrantClient

print("Force clearing Qdrant collections...")
try:
    client = QdrantClient(path="./qdrant_storage")
    collections = client.get_collections().collections
    
    for c in collections:
        if c.name.startswith("neuroops"):
            print(f"Deleting {c.name}...")
            client.delete_collection(c.name)
            
    print("All neuroops collections cleared.")
except Exception as e:
    print(f"Error: {e}")
