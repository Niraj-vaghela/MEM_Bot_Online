import pandas as pd
import json
import os

# Define paths - Member-only chatbot
FILE_PATHS = {
    "Member": r"C:\Users\Niraj\Desktop\vs_code_Nov_2025\Lama_Prompt_bot\MEM_HC_URLs.xlsx"
    # Employer and Connector removed - this is a Member-only chatbot
}

OUTPUT_FILE = "data/url_list.json"

def ingest_urls():
    all_urls = []
    
    # Ensure data directory exists
    os.makedirs("data", exist_ok=True)

    for category, path in FILE_PATHS.items():
        print(f"Reading {category} from {path}...")
        try:
            # Check if file exists to give better error messages
            if not os.path.exists(path):
                print(f"Error: File not found: {path}")
                continue
                
            df = pd.read_excel(path)
            
            # Normalize column names to find 'URLs' (case insensitive match if needed, but user said 'URLs')
            if 'URLs' not in df.columns:
                print(f"Error: 'URLs' column not found in {path}. Columns: {df.columns.tolist()}")
                continue
            
            urls = df['URLs'].dropna().tolist()
            print(f"Found {len(urls)} URLs for {category}.")
            
            for url in urls:
                all_urls.append({
                    "url": str(url).strip(),
                    "category": category
                })
                
        except Exception as e:
            print(f"Failed to read {path}: {e}")

    # Save to JSON
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(all_urls, f, indent=4)
    
    print(f"Successfully saved {len(all_urls)} URLs to {OUTPUT_FILE}")

if __name__ == "__main__":
    ingest_urls()
