# Member Help Center Bot (Version 3)

A streamlined RAG (Retrieval-Augmented Generation) chatbot focused exclusively on **Member** queries, powered by ChromaDB and Ollama's Llama 3.2.

## 🎯 Overview

This is version 3 of the Help Center chatbot, simplified to serve only Member-category queries. It provides intelligent, context-aware responses using a local RAG architecture with advanced date calculation capabilities.

## ✨ Features

- **Member-Focused**: Hard-coded to serve only Member queries (no category selection needed)
- **RAG-Powered**: Uses ChromaDB for efficient semantic search and retrieval
- **Advanced Date Reasoning**: Calculates opt-out deadlines with working day logic and UK bank holidays
- **Interactive Follow-ups**: Predicts and suggests relevant next topics
- **Personalized Experience**: Asks for user's name and personalizes responses
- **Real-time Streaming**: Streams responses for better user experience
- **Clean UI**: Streamlit-based interface with accessibility-focused design

## 🛠️ Tech Stack

- **Frontend**: Streamlit
- **LLM**: Ollama (Llama 3.2:3b)
- **Vector DB**: ChromaDB
- **Embeddings**: SentenceTransformers (all-MiniLM-L6-v2)
- **Date Logic**: Python datetime, dateparser, holidays

## 📋 Prerequisites

- Python 3.8+
- [Ollama](https://ollama.ai/) installed with `llama3.2:3b` model
- ChromaDB data (pre-populated with Member content)

## 🚀 Installation

1. **Install dependencies**:
```bash
pip install -r requirements.txt
```

2. **Verify Ollama is running**:
```bash
ollama list
# Ensure llama3.2:3b is available
```

3. **Ensure ChromaDB data exists**:
- The `data/chroma_db` folder should contain your pre-ingested Member documents
- The database filters for `category: "Member"` automatically

## ▶️ Usage

**Run the chatbot**:
```bash
streamlit run chatbot.py
```

Or use the batch file:
```bash
run_app.bat
```

The app will open in your browser at `http://localhost:8501`

## 🆚 Differences from V2

| Feature | V2 | V3 (Member-Only) |
|---------|-----|------------------|
| **Category Selection** | Multi-category (Member/Employer/Connector) | Member-only (hard-coded) |
| **Sidebar UI** | Category selector dropdown | Info message only |
| **Query Filtering** | Dynamic based on user selection | Always filters for "Member" |
| **Page Title** | "Help Center Assistant" | "Member Help Center Assistant" |
| **State Management** | Tracks category switching | Simplified (no category state) |

## 📁 Project Structure

```
Mem only chat bot/
├── chatbot.py              # Main Streamlit application
├── date_logic.py           # Advanced date calculation logic
├── embedder.py             # Embedding utilities
├── scraper.py              # Web scraping utilities
├── ingest_urls.py          # Data ingestion script
├── requirements.txt        # Python dependencies
├── run_app.bat            # Windows batch launcher
└── data/
    ├── chroma_db/         # Vector database
    ├── scraped_content.json
    └── url_list.json
```

## 🧪 Testing

1. **Basic Query**: "How do I opt out?"
2. **Date Calculation**: "If I enrolled on 3rd Jan 2026, when can I opt out?"
3. **Follow-up Prediction**: Check if suggested topics are relevant
4. **Name Flow**: Reset and verify personalized greeting

## 🔧 Configuration

Key settings in `chatbot.py`:
- `DB_PATH`: Location of ChromaDB (`data/chroma_db`)
- `COLLECTION_NAME`: ChromaDB collection (`rag_knowledge_base`)
- `MODEL_NAME`: Ollama model (`llama3.2:3b`)
- Category filter: Hard-coded to `"Member"` (line 360)

## 📝 Notes

- This version maintains the same ChromaDB database as v2 (contains all categories)
- The application simply filters to only retrieve Member documents
- All other functionality (date logic, streaming, predictions) remains unchanged

## 🤝 Support

For issues or questions, refer to the implementation documentation or contact the development team.
