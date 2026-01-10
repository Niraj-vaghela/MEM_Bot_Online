import ollama

MODEL_NAME = "llama3.2:3b"

print("--- Testing Ollama Streaming ---")
try:
    stream = ollama.chat(
        model=MODEL_NAME, 
        messages=[{"role": "user", "content": "hi"}],
        stream=True
    )
    
    print(f"Stream object type: {type(stream)}")
    
    for i, chunk in enumerate(stream):
        print(f"Chunk {i} type: {type(chunk)}")
        print(f"Chunk {i} content: {chunk}")
        
        # Test subscripting
        try:
            val = chunk['message']['content']
            print(f"Chunk {i} subscript success: {val}")
        except Exception as e:
            print(f"Chunk {i} subscript FAILED: {e}")
            break
            
        if i >= 1: break # Just test first few

except Exception as e:
    print(f"Top Level Error: {e}")
