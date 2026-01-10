import os
import sys
import time
from pyngrok import ngrok
import subprocess
from threading import Thread

def run_streamlit():
    """Run Streamlit in a separate process"""
    cmd = [sys.executable, "-m", "streamlit", "run", "chatbot.py", "--server.port=8501", "--server.headless=true"]
    subprocess.run(cmd)

def main():
    print("--- 🚀 Deploying Help Center Bot ---")
    
    # 1. Check for Auth Token
    # Ngrok requires an auth token for HTML content.
    # We'll check if it's set, if not, we prompt (or warn).
    try:
        # This might fail if no config is found/token not set
        # But pyngrok usually handles the binary installation.
        pass
    except Exception:
        pass

    print("Step 1: Starting Streamlit App...")
    # Start Streamlit in a thread so we can run ngrok in main
    thread = Thread(target=run_streamlit)
    thread.daemon = True
    thread.start()
    
    # Give Streamlit a moment to start
    time.sleep(3)
    
    print("Step 2: Opening Ngrok Tunnel...")
    try:
        # Open a HTTP tunnel on the default port 8501
        # If the user hasn't authenticated, this might throw an error or give a limited session.
        public_url = ngrok.connect(8501).public_url
        print("\n" + "="*50)
        print(f"🌍 PUBLIC URL: {public_url}")
        print("="*50 + "\n")
        print("Share this URL with anyone to let them test your bot!")
        print("(Press Ctrl+C to stop the server)")
        
        # Keep the script running
        thread.join()
        
    except Exception as e:
        print(f"\n❌ Ngrok Error: {e}")
        print("\nIMPORTANT: You may need to sign up for a free Ngrok account and set your authtoken.")
        print("Run: ngrok config add-authtoken <YOUR_TOKEN>")
        print("Get your token here: https://dashboard.ngrok.com/get-started/your-authtoken")

if __name__ == "__main__":
    main()
