"""
Feedback Manager - Handles user feedback collection and storage for the chatbot.
"""
import csv
import os
from datetime import datetime
from pathlib import Path

FEEDBACK_FILE = "data/chat_logs.csv"
HEADERS = ["Sr. no", "Date", "Unique ID", "Member Name", "Transcript", "Feedback Rating", "Feedback Text"]

def init_chat_logs():
    """Initialize the CSV file with headers if it doesn't exist."""
    if not os.path.exists(FEEDBACK_FILE):
        os.makedirs(os.path.dirname(FEEDBACK_FILE), exist_ok=True)
        with open(FEEDBACK_FILE, mode="w", newline="", encoding="utf-8") as file:
            writer = csv.writer(file)
            writer.writerow(HEADERS)

def get_next_sr_no():
    """Calculate the next Serial Number based on existing rows."""
    if not os.path.exists(FEEDBACK_FILE):
        return 1
    try:
        with open(FEEDBACK_FILE, mode="r", encoding="utf-8") as file:
            reader = list(csv.reader(file))
            if len(reader) <= 1: # Only header or empty
                return 1
            last_row = reader[-1]
            if last_row and last_row[0].isdigit():
                return int(last_row[0]) + 1
            return len(reader) # Fallback
    except Exception:
        return 1

def log_chat(user_name, session_id, conversation_history, feedback_rating=None, feedback_text=None):
    """Log the chat session to CSV."""
    init_chat_logs()
    
    # Get current date and time
    now = datetime.now()
    chat_date = now.strftime("%Y-%m-%d %H:%M:%S")
    
    # Calculate Sr. no
    sr_no = get_next_sr_no()
    
    # Format conversation history
    history_str = ""
    for msg in conversation_history:
        role = msg["role"].capitalize()
        content = msg["content"]
        history_str += f"{role}: {content}\n"
    
    # Write to CSV
    row = [
        sr_no,
        chat_date,
        session_id,
        user_name,
        history_str.strip(),
        feedback_rating if feedback_rating else "",
        feedback_text if feedback_text else ""
    ]
    
    try:
        with open(FEEDBACK_FILE, mode="a", newline="", encoding="utf-8") as file:
            writer = csv.writer(file)
            writer.writerow(row)
        print(f"Chat logged successfully: Session {session_id}")
    except Exception as e:
        print(f"Error logging chat: {e}")

def update_feedback_log(session_id, rating, text):
    """Update an existing chat log with feedback."""
    if not os.path.exists(FEEDBACK_FILE):
        return False
        
    updated_rows = []
    found = False
    
    try:
        with open(FEEDBACK_FILE, mode="r", newline="", encoding="utf-8") as file:
            reader = list(csv.reader(file))
            header = reader[0]
            updated_rows.append(header)
            
            # Find the row with matching session_id
            # Session ID is at index 2 in new schema
            session_idx = 2
            
            for row in reader[1:]:
                if len(row) > session_idx and row[session_idx] == session_id:
                    # Update Rating (Index 5) and Text (Index 6)
                    row[5] = rating
                    row[6] = text
                    found = True
                updated_rows.append(row)
        
        if found:
            with open(FEEDBACK_FILE, mode="w", newline="", encoding="utf-8") as file:
                writer = csv.writer(file)
                writer.writerows(updated_rows)
            return True
    except Exception as e:
        print(f"Error updating feedback: {e}")
        return False
    
    return False
