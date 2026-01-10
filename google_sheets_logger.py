
import streamlit as st
import pandas as pd
from datetime import datetime

try:
    from streamlit_gsheets import GSheetsConnection
except ImportError:
    GSheetsConnection = None

def get_sheet_connection():
    """Establishes connection to Google Sheets."""
    if GSheetsConnection is None:
        print("GSheetsConnection module not found. Skipping GSheets logging.")
        return None

    try:
        return st.connection("gsheets", type=GSheetsConnection)
    except Exception as e:
        print(f"Failed to connect to Google Sheets: {e}")
        return None

def log_to_sheet(session_id, user_name, transcript):
    """Appends a new chat session to the Google Sheet."""
    conn = get_sheet_connection()
    if not conn:
        return

    try:
        # 1. Read existing data
        # ttl=0 ensures we don't cache old data (risk of overwriting)
        existing_data = conn.read(ttl=0) 
        
        # 2. Prepare new row
        new_row = pd.DataFrame([{
            "Timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "Session_ID": str(session_id),
            "User_Name": user_name,
            "Transcript": transcript,
            "Rating": "",
            "Feedback": ""
        }])
        
        # 3. Append
        updated_df = pd.concat([existing_data, new_row], ignore_index=True)
        
        # 4. Update Sheet
        conn.update(data=updated_df)
        
    except Exception as e:
        print(f"Error logging to sheet: {e}")
        # Configure fallback or retry if needed

def update_sheet_feedback(session_id, rating, feedback):
    """Updates an existing row with feedback."""
    conn = get_sheet_connection()
    if not conn:
        return

    try:
        df = conn.read(ttl=0)
        
        # Find row with matching Session_ID
        # Ensure Session_ID column is string for comparison
        df['Session_ID'] = df['Session_ID'].astype(str)
        session_id = str(session_id)
        
        if session_id in df['Session_ID'].values:
            df.loc[df['Session_ID'] == session_id, 'Rating'] = rating
            df.loc[df['Session_ID'] == session_id, 'Feedback'] = feedback
            conn.update(data=df)
        else:
            print(f"Session ID {session_id} not found for feedback update.")
            
    except Exception as e:
        print(f"Error updating sheet feedback: {e}")
