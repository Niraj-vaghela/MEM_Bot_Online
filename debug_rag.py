import chromadb
from chromadb.utils import embedding_functions
import ollama

DB_PATH = "data/chroma_db"
COLLECTION_NAME = "rag_knowledge_base"
MODEL_NAME = "llama3.2:3b"

def query_rag(text):
    client = chromadb.PersistentClient(path=DB_PATH)
    ef = embedding_functions.SentenceTransformerEmbeddingFunction(model_name="all-MiniLM-L6-v2")
    collection = client.get_collection(name=COLLECTION_NAME, embedding_function=ef)
    
    results = collection.query(
        query_texts=[text],
        n_results=2
    )
    return results

def get_llm_response(query, context):
    system_prompt = (
        "You are a helpful and strict assistant for a Help Center. "
        "You must answer the user's question based ONLY on the provided context below. "
        "If the context contains instructions, options, or steps, you MUST summarize them clearly. "
        "Do NOT use outside knowledge. "
        "Do NOT fabricate information. "
        "If the answer is not in the context, say 'I cannot find that information'.\n\n"
        "CONTEXT:\n" + context
    )
    
    response = ollama.chat(
        model=MODEL_NAME,
        messages=[
            {'role': 'system', 'content': system_prompt},
            {'role': 'user', 'content': query},
        ]
    )
    return response['message']['content']

def test_query(q):
    print(f"\n--- Testing Query: '{q}' ---")
    results = query_rag(q)
    
    # Print Retrieved Docs
    context_parts = []
    print("Retrieved Documents:")
    if results['documents']:
        for i, doc in enumerate(results['documents'][0]):
            meta = results['metadatas'][0][i]
            print(f"[{i+1}] {meta.get('url')} (Header: {meta.get('header')})")
            context_parts.append(f"Header: {meta.get('header')}\n\n{doc}")
    
    context = "\n---\n".join(context_parts)
    
    # Generate
    print("\nGenerating Response...")
    ans = get_llm_response(q, context)
    print("Response:")
    print(ans)

if __name__ == "__main__":
    q1 = "I was enrolled on 3rd Jan 2026, when is my opt out end date?"
    
    test_query(q1)
