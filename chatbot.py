import streamlit as st
import chromadb
from chromadb.utils import embedding_functions
from groq import Groq
import uuid
import json
from feedback_manager import log_chat, update_feedback_log
from google_sheets_logger import log_to_sheet, update_sheet_feedback

# Configuration
DB_PATH = "data/chroma_db"
COLLECTION_NAME = "rag_knowledge_base"
# MODEL_NAME = "llama3.2:3b" 
MODEL_NAME = "llama-3.1-8b-instant" # Groq Llama 3 model

# Initialize Groq Client
try:
    GROQ_API_KEY = st.secrets["GROQ_API_KEY"]
except Exception:
    st.error("Missing GROQ_API_KEY in secrets.toml or Streamlit Cloud Secrets.")
    st.stop()

client = Groq(api_key=GROQ_API_KEY)

# Page Config
st.set_page_config(page_title="Member Help Center Bot", page_icon="🤖", layout="wide")

# Custom CSS for "Premium" look
st.markdown("""
<style>
    /* =========================================
       ACCESSIBILITY & THEME OVERRIDES 
       ========================================= */
    
    /* 1. Main App Background & Text */
    .stApp {
        background-color: #ffffff !important;
        color: #000000 !important;
    }
    
    /* FORCE Black text on everything inside the main area */
    .stApp > header, .stApp > div, .stApp > footer {
        color: #000000 !important;
    }
    .stApp p, .stApp h1, .stApp h2, .stApp h3, .stApp h4, .stApp h5, .stApp h6, .stApp span, .stApp div {
        color: #000000 !important;
    }
    
    /* 2. Sidebar styling - Aggressive Overrides */
    [data-testid="stSidebar"], section[data-testid="stSidebar"], [data-testid="stSidebarNav"] {
        background-color: #f0f2f6 !important;
        border-right: 1px solid #dce0e6;
    }
    /* Force all text in sidebar to be dark */
    [data-testid="stSidebar"] *, [data-testid="stSidebar"] p, [data-testid="stSidebar"] span, [data-testid="stSidebar"] div, [data-testid="stSidebar"] label {
        color: #262730 !important; 
    }

    /* 3. Button Styling (Reset Button, etc.) - High Contrast */
    div[data-testid="stButton"] > button {
        background-color: #ffffff !important;
        color: #262730 !important;
        border: 1px solid #dce0e6 !important;
        font-weight: 500 !important;
    }
    div[data-testid="stButton"] > button:hover {
        border-color: #ff4b4b !important;
        color: #ff4b4b !important;
        background-color: #f0f2f6 !important;
    }
    div[data-testid="stButton"] > button:active {
        box-shadow: none;
        background-color: #e6e9ef !important;
    }

    /* 4. Chat Input & Text Input Styling */
    textarea, input {
        background-color: #ffffff !important;
        color: #000000 !important;
        caret-color: #000000 !important;
        border: 1px solid #dce0e6 !important;
    }
    div[data-testid="stChatInput"] {
        background-color: #ffffff !important;
        border-top: 1px solid #dce0e6 !important;
    }
    
    /* 5. Chat Messages */
    .stChatMessage {
        background-color: #f9f9f9 !important;
        color: #000000 !important;
        border: 1px solid #e0e0e0 !important;
        border-radius: 8px !important;
        padding: 15px !important;
        margin-bottom: 10px !important;
    }
    
    /* 6. Radio button text override (Specific fix) */
    .stRadio {
        background-color: transparent !important;
    }
    .stRadio label, .stRadio div, .stRadio p {
        color: #000000 !important;
    }

    /* 7. Blinking Cursor Animation */
    @keyframes blink {
        50% { opacity: 0; }
    }
    .thinking-text {
        color: #000000 !important;
        font-weight: 500;
        font-style: italic;
        display: flex;
        align-items: center;
    }
    .cursor {
        display: inline-block;
        width: 8px;
        height: 18px;
        background-color: #000000;
        animation: blink 1s step-end infinite;
        margin-left: 5px;
    }

</style>
""", unsafe_allow_html=True)

# -----------------------------------------------------------------------------
# Backend / RAG Logic
# -----------------------------------------------------------------------------

# Helper to format time
def get_time_str():
    import datetime
    return datetime.datetime.now().strftime("%H:%M:%S")

@st.cache_resource
def get_collection():
    """Load ChromaDB collection once."""
    client = chromadb.PersistentClient(path=DB_PATH)
    ef = embedding_functions.SentenceTransformerEmbeddingFunction(model_name="all-MiniLM-L6-v2")
    return client.get_collection(name=COLLECTION_NAME, embedding_function=ef)

def query_rag(collection, query, category, n_results=3):
    """Retrieve relevant documents filtered by category.
    
    Performance: Using n_results=3 provides better context while maintaining speed.
    """
    results = collection.query(
        query_texts=[query],
        n_results=n_results,
        where={"category": category} # Strict filtering
    )
    return results

    return results

# Create a helper to safely get content from chunk/response
def get_content(item):
    # Try attribute access first (Pydantic/Object)
    try:
        return item.message.content
    except AttributeError:
        pass
    # Try dict access
    try:
        return item['message']['content']
    except (TypeError, KeyError):
        pass
    # Debug fallback
    # print(f"DEBUG: Could not extract content from {item}", flush=True)
    return ""

def generate_response_stream(query, context_text):
    """Generate answer using Llama 3.2 with streaming."""
    import datetime
    current_date = datetime.datetime.now().strftime("%d %B %Y")
    
    # --- INTELLIGENT LAYER: Check for Date logic ---
    date_context = ""
    try:
        from date_logic import calculate_opt_out_dates
        # We try to see if the user mentioned a date relevant to enrollment
        # Heuristic: If parsing returns a date, we inject the math.
        # Ideally we only do this if the query seems relevant, but for "Advanced Reasoning" demo we can be eager.
        calc_result = calculate_opt_out_dates(query)
        if calc_result:
            date_context = f"\n\n*** DATE CALCULATION RESULT ***\n{calc_result['summary']}\n*********************************\n"
    except Exception as e:
        print(f"Date logic error: {e}")
    # -----------------------------------------------

    # Add conversation history for context
    conversation_context = ""
    if len(st.session_state.messages) > 1:
        # Get last 3 exchanges (6 messages) for context
        recent_messages = st.session_state.messages[-6:]
        conversation_context = "\n\nRECENT CONVERSATION:\n"
        for msg in recent_messages:
            role = msg['role'].upper()
            content = msg['content'][:150]  # Truncate for context
            conversation_context += f"{role}: {content}...\n"
    
    system_prompt = (
        "You are a helpful and strict assistant for a Help Center. "
        f"TODAY'S DATE: {current_date}\n"
        "INSTRUCTIONS:\n"
        "1. **Greetings & Pleasantries**: If the user says 'Hello', 'Good morning', 'Thanks', or 'Thank you', respond politely and naturally. You do NOT need context for this.\n"
        "2. **Information Queries**: For questions about NEST, pensions, or account details, you must answer based **ONLY** on the provided context below. "
        "3. **Privacy & Security**: You are a public help bot. You do **NOT** have access to member accounts. **NEVER** ask for personal details like NEST ID, NNI, or Date of Birth. If a user asks about their specific account (e.g., 'What is my balance?'), explain that you cannot access their account and guide them to log in to the website.\n"
        "If the context contains instructions, options, or steps (e.g., 'Website', 'Phone', 'Post'), you MUST summarize them clearly for the user. "
        "ADVANCED REASONING: If the CALCULATED DATE RESULT (below) is available, use it to answer specific date questions perfectly. "
        "Do NOT try to do the math yourself if the result is provided. Trust the 'DATE CALCULATION RESULT'. "
        "Do NOT simply say 'check the link' if the content is available in the text. "
        "Do NOT fabricate information. "
        "Do NOT mention external resources or say '(link provided)' unless the link path is explicitly present in the CONTEXT. "
        "Always format links as Markdown: `[Link Text](url)`. "
        "Be conversational but do NOT ask identifying questions. "
        "If the answer is not in the context, say 'I cannot find that information in the help articles provided.'\n\n"
        "CONTEXT:\n" + context_text + date_context + conversation_context
    )
    
    # Enable Streaming with optimized parameters
    stream = client.chat.completions.create(
        model=MODEL_NAME, 
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": query}
        ],
        stream=True,
        temperature=0.3,
        max_tokens=512
    )

    print("DEBUG: Starting Stream...", flush=True)
    for chunk in stream:
        content = chunk.choices[0].delta.content
        if content:
            yield content

def predict_next_topic(query, answer):
    """Predict a relevant follow-up topic."""
    prompt = (
        f"Based on the user's question: '{query}' and your answer: '{answer}', "
        "predict ONE likely follow-up topic keywords based on the context. "
        "Output ONLY the topic keywords (e.g. 'Opting Out', 'Pension Transfer'). "
        "Do NOT frame it as a question. Do not include 'Do you need info on'. "
    )
    
    print("DEBUG: Calling predict_next_topic", flush=True)
    try:
        response = client.chat.completions.create(
            model=MODEL_NAME, 
            messages=[
                {"role": "user", "content": prompt}
            ], 
            stream=False
        )
        
        return response.choices[0].message.content
    except Exception as e:
        print(f"DEBUG: Error in predict_next_topic: {e}", flush=True)
        return ""


import datetime

# -----------------------------------------------------------------------------
# UI Logic
# -----------------------------------------------------------------------------

# Initialize Session ID (for chat logging)
if "session_id" not in st.session_state:
    st.session_state.session_id = str(uuid.uuid4())

if "chat_ended" not in st.session_state:
    st.session_state.chat_ended = False

if "messages" not in st.session_state:
    st.session_state.messages = [{
        "role": "assistant",
        "content": "Hello! Welcome to the Member Help Center. To get started, please tell me your name.",
        "timestamp": get_time_str()
    }]

if "conversation_step" not in st.session_state:
    st.session_state.conversation_step = "ASK_NAME" # Steps: ASK_NAME, READY

# Header Area with End Chat
col_title, col_end = st.columns([0.75, 0.25])
with col_title:
    st.title("🤖 Member Help Center Assistant")
with col_end:
    st.markdown('<div style="height: 15px;"></div>', unsafe_allow_html=True) # Vertical alignment
    if not st.session_state.chat_ended:
        if st.button("End Chat", type="primary", use_container_width=True):
            st.session_state.chat_ended = True
            log_chat(
                session_id=st.session_state.session_id,
                user_name=st.session_state.get('user_name', 'Anonymous'),
                conversation_history=st.session_state.messages
            )
            # Log to Google Sheets
            log_to_sheet(
                session_id=st.session_state.session_id,
                user_name=st.session_state.get('user_name', 'Anonymous'),
                transcript=str(st.session_state.messages)
            )
            st.rerun()



# Helper to format time (Moved to top)
# def get_time_str():
#     return datetime.datetime.now().strftime("%H:%M:%S")

# Sidebar - Settings (Minimal)
with st.sidebar:
    st.header("Settings")
    st.info("💡 This chatbot serves **Member** queries only.")
    st.divider()

# 2. Display Chat History
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])
        if "timestamp" in message:
            st.caption(f"_{message['timestamp']}_")

# Chat Controls Removed (Moved to Header)


# Post-Chat Options
if st.session_state.chat_ended:
    st.divider()
    st.markdown("### Chat Ended")
    
    # Feedback Form
    with st.expander("📝 Provide Feedback", expanded=True):
        with st.form("feedback_form"):
            rating = st.slider("Rate experience:", 1, 10, 5)
            text = st.text_area("Comments (optional):")
            if st.form_submit_button("Submit Feedback"):
                # Update CSV
                if update_feedback_log(st.session_state.session_id, rating, text):
                    st.success("Feedback submitted!")
                else:
                    st.error("Error saving feedback.")
                
                # Update Google Sheet
                update_sheet_feedback(st.session_state.session_id, rating, text)
    
    col_dl, col_new = st.columns(2)
    
    with col_dl:
        # Generate Transcript
        user_name_dl = st.session_state.get('user_name', 'Anonymous')
        chat_text = f"Chat Session: {st.session_state.session_id}\n"
        chat_text += f"Date: {get_time_str()}\n"
        chat_text += f"Member: {user_name_dl}\n\n"
        for msg in st.session_state.messages:
            role = "Bot" if msg["role"] == "assistant" else user_name_dl
            chat_text += f"{role}: {msg['content']}\n\n"
            
        st.download_button(
            label="📥 Save Transcript",
            data=chat_text,
            file_name=f"chat_{st.session_state.session_id[:8]}.txt",
            mime="text/plain",
            use_container_width=True
        )
        
    with col_new:
        if st.button("🔄 Start New Chat (Skip)", type="primary", use_container_width=True):
            st.session_state.messages = [{
                "role": "assistant",
                "content": "Hello! Welcome to the Member Help Center. To get started, please tell me your name.",
                "timestamp": get_time_str()
            }]
            st.session_state.session_id = str(uuid.uuid4())
            st.session_state.chat_ended = False
            if "user_name" in st.session_state:
                del st.session_state.user_name
            st.session_state.conversation_step = "ASK_NAME"
            if "last_prediction" in st.session_state:
                del st.session_state.last_prediction
            st.rerun()



# 3. Handle User Input & Logic
# We use a flag to process response so buttons can trigger it too
process_response = False
user_input_text = None

# Determine prompt text
if st.session_state.conversation_step == "ASK_NAME":
    prompt_placeholder = "Enter your name..."
else:
    user_name = st.session_state.get("user_name", "User")
    prompt_placeholder = f"How can I help you, {user_name}?"

if prompt := st.chat_input(prompt_placeholder, disabled=st.session_state.chat_ended):
    user_input_text = prompt
    # User sent a message
    st.session_state.messages.append({
        "role": "user",
        "content": prompt,
        "timestamp": get_time_str()
    })
    
    # Display it immediately (duplicate of history loop but needed for immediate feedback)
    with st.chat_message("user"):
        st.markdown(prompt)
        st.caption(f"_{get_time_str()}_")
    
    process_response = True

# 4. Check if we have a pending "Button Triggered" message to process
# (This happens if st.rerun() was called after adding a user message programmatically)
if not process_response and st.session_state.messages and st.session_state.messages[-1]["role"] == "user":
    # If the last message was user and we haven't answered it yet (check length parity or manual flag)
    # Simple heuristic: If last message is User, Bot must answer.
    # Note: 'messages' includes the initial greeting (Assistant) -> User (Name) -> Assistant (Welcome) -> User (Question)
    # So if last is User, we respond.
    # CAUTION: We need to distinguish "Name Input" user message vs "Query" user message.
    process_response = True

# 5. Process Logic (State Machine)
if process_response and not st.session_state.chat_ended: # Only process if chat is not ended
    last_user_msg = st.session_state.messages[-1]["content"]
    
    # SCENARIO A: User just entered their Name
    if st.session_state.conversation_step == "ASK_NAME":
        # Save name
        st.session_state.user_name = last_user_msg
        st.session_state.conversation_step = "READY"
        
        # Bot responds: "Nice to meet you..."
        with st.chat_message("assistant"):
            response_msg = f"How can I help you, {st.session_state.user_name}?"
            st.markdown(response_msg)
            st.caption(f"_{get_time_str()}_")
            
            st.session_state.messages.append({
                "role": "assistant",
                "content": response_msg,
                "timestamp": get_time_str()
            })
        st.rerun() # Refresh to update chat input placeholder to "How can I help..."

    # SCENARIO B: Normal Q&A
    elif st.session_state.conversation_step == "READY":
        with st.chat_message("assistant"):
            # Placeholder for "Thinking" GIF (Show briefly while retrieving)
            thinking_placeholder = st.empty()
            # Text-based Thinking Animation
            thinking_placeholder.markdown(
                '<p class="thinking-text">Bot is thinking<span class="cursor"></span></p>', 
                unsafe_allow_html=True
            ) 
            
            try:
                collection = get_collection()
                
                # Retrieve Context (Member category only)
                results = query_rag(collection, last_user_msg, "Member")
                docs = results['documents'][0]
                metadatas = results['metadatas'][0]
                
                if not docs:
                    context_text = "No relevant documents found."
                else:
                    context_parts = []
                    for doc, meta in zip(docs, metadatas):
                        context_parts.append(f"Source ({meta['category']}): {meta['header']}\n{doc}")
                    context_text = "\n---\n".join(context_parts)
                
                # Remove Thinking GIF once we start generating
                # thinking_placeholder.empty() <--- REMOVED: Now handled in wrapper
                
                # Wrapper to clear UI placeholder only when first chunk arrives
                def clear_placeholder_on_first_yield(generator, placeholder):
                    is_first = True
                    for chunk in generator:
                        if is_first:
                            placeholder.empty()
                            is_first = False
                        yield chunk
                
                # Generate Answer (Streamed)
                stream_generator = generate_response_stream(last_user_msg, context_text)
                
                # Pass the wrapper to st.write_stream
                answer_text = st.write_stream(clear_placeholder_on_first_yield(stream_generator, thinking_placeholder))
                
                # Add timestamp (rendered after stream finishes)
                st.caption(f"_{get_time_str()}_")
                
                st.session_state.messages.append({
                    "role": "assistant",
                    "content": answer_text,
                    "timestamp": get_time_str()
                })
                
                # Predict Follow-up (Runs AFTER streaming is done)
                prediction_text = predict_next_topic(last_user_msg, answer_text)
                st.session_state.last_prediction = prediction_text

                
                # Force rerun to show buttons below
                st.rerun()
                
            except Exception as e:
                thinking_placeholder.empty()
                st.error(f"An error occurred: {e}")

# 6. Interactive Follow-up Buttons (Always show if prediction exists and last msg was assistant)
# Ensure we only show buttons if the LAST message was indeed the assistant answering
if "last_prediction" in st.session_state and st.session_state.messages and st.session_state.messages[-1]["role"] == "assistant":
    prediction_text = st.session_state.last_prediction
    
    st.divider()
    st.markdown(f"**Predicted Topic:** Do you want to know about **{prediction_text}**?")
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("✅ Yes, tell me more", use_container_width=True):
            # 1. Add User Query programmatically
            follow_up_query = f"Tell me more about {prediction_text}"
            st.session_state.messages.append({
                "role": "user",
                "content": follow_up_query,
                "timestamp": get_time_str()
            })
            # 2. Clear prediction so buttons vanish
            del st.session_state.last_prediction
            # 3. Rerun - This will hit the "Check parity" logic in step 4 and trigger Step 5 (Scenario B)
            st.rerun()
            
    with col2:
        if st.button("❌ No, I'm good", use_container_width=True):
            user_name = st.session_state.get("user_name", "User")
            # 1. Bot closes this topic
            st.session_state.messages.append({
                "role": "assistant",
                "content": f"How else can I help you, {user_name}?",
                "timestamp": get_time_str()
            })
            # 2. Clear prediction
            del st.session_state.last_prediction
            # 3. Rerun to update chat
            st.rerun()

