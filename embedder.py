import chromadb
from chromadb.utils import embedding_functions
import json
import sys
import os

# Force unbuffered output for real-time logging
sys.stdout.reconfigure(encoding='utf-8')

INPUT_FILE = "data/scraped_content.json"
DB_PATH = "data/chroma_db"
COLLECTION_NAME = "rag_knowledge_base"

def create_embeddings():
    if not os.path.exists(INPUT_FILE):
        print(f"Input file {INPUT_FILE} not found. Run scraper.py first.")
        return

    print("Loading scraped content...", flush=True)
    with open(INPUT_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)

    print(f"Loaded {len(data)} documents. Initializing ChromaDB...")
    
    # Initialize ChromaDB Client
    client = chromadb.PersistentClient(path=DB_PATH)
    
    # Use generic Sentence Transformer embedding function
    # This automatically downloads 'all-MiniLM-L6-v2' (approx 80MB)
    ef = embedding_functions.SentenceTransformerEmbeddingFunction(model_name="all-MiniLM-L6-v2")
    
    # Get or Create Collection
    # We delete existing to ensure a fresh start on re-run (modular)
    try:
        client.delete_collection(name=COLLECTION_NAME)
        print("Deleted existing collection to rebuild.")
    except Exception:
        pass # Collection didn't exist or couldn't be deleted

    collection = client.create_collection(name=COLLECTION_NAME, embedding_function=ef)
    
    # Prepare Batches (Chroma likes batches)
    documents = []
    metadatas = []
    ids = []
    
    print("Generating embeddings and indexing...")
    member_count = 0
    skipped_count = 0
    
    for idx, item in enumerate(data):
        # Member-only validation
        if item.get("category") != "Member":
            print(f"⚠️  Skipping non-Member article: {item.get('header', 'Unknown')} (Category: {item.get('category')})")
            skipped_count += 1
            continue
        
        # Combined text for embedding context
        text_content = f"Header: {item['header']}\n\n{item['content']}"
        
        documents.append(text_content)
        metadatas.append({
            "url": item["url"],
            "category": item["category"],
            "header": item["header"]
        })
        ids.append(str(member_count))
        member_count += 1
    
    print(f"\n✅ Member articles to embed: {member_count}")
    print(f"⏭️  Non-Member articles skipped: {skipped_count}")
    
    # Add in batches of 100 to avoid hitting limits or memory issues
    batch_size = 100
    for i in range(0, len(documents), batch_size):
        batch_end = i + batch_size
        print(f"Processing batch {i} to {batch_end}...", flush=True)
        collection.add(
            documents=documents[i:batch_end],
            metadatas=metadatas[i:batch_end],
            ids=ids[i:batch_end]
        )
        
    print(f"Successfully embedded {len(documents)} documents into {DB_PATH}")

if __name__ == "__main__":
    create_embeddings()
