from src.data.vector_store import VectorStore, get_qdrant_client

print("Initializing VectorStore (checking code version)...")
store = VectorStore("1")
print(f"VectorStore.vector_size = {store.vector_size}")

client = get_qdrant_client()
collections = client.get_collections().collections

print(f"\nFound {len(collections)} collections:")
for c in collections:
    info = client.get_collection(c.name)
    size = info.config.params.vectors.size
    print(f" - {c.name}: {size} dims")
    
    if c.name == "neuroops_1" and size == 512:
        print("   [!] mismatch detected in debug script. Forcing deletion...")
        client.delete_collection("neuroops_1")
        print("   [+] neuroops_1 deleted.")
