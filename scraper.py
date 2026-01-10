import requests
from bs4 import BeautifulSoup
import json
import os
import time
from urllib.parse import urljoin

INPUT_FILE = "data/url_list.json"
OUTPUT_FILE = "data/scraped_content.json"

STOP_CLASSES = {
    "related_articles", 
    "table-outer-wrapper", 
    "article-help-feedback", 
    "feedback-wrapper", 
    "was-this-page-helpful"
}

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
}

def scrape_url(url):
    try:
        response = requests.get(url, headers=HEADERS, timeout=10)
        response.raise_for_status()
        soup = BeautifulSoup(response.content, "html.parser")
        
        # 1. Extract Header
        header_tag = soup.find("h1")
        header = header_tag.get_text(strip=True) if header_tag else "No Header Found"
        
        # 2. Extract Content
        content_parts = []
        start_node = soup.find("div", class_="article-help-heading")
        if not start_node and header_tag:
            # Fallback for pages without the specific heading class
            print(f"Fallback: Using h1 as start node for {url}")
            start_node = header_tag
        
        if start_node:
            current = start_node.next_sibling
            while current:
                if current.name: # If it's a tag
                    # Check stop classes
                    classes = current.get("class", [])
                    if any(cls in STOP_CLASSES for cls in classes):
                        break 
                    
                    # --- NEW: Preserve Links ---
                    # We iterate through all <a> tags in this element and replace them
                    # with markdown syntax [text](url) so the LLM sees the link.
                    for a_tag in current.find_all("a", href=True):
                        href = a_tag["href"]
                        # Filter out javascript: links
                        if href.lower().startswith("javascript:") or href.strip() == "#":
                            continue
                            
                        # Resolve relative links
                        full_link = urljoin(url, href)
                        link_text = a_tag.get_text(strip=True)
                        
                        # Replace <a> with string representation
                        # We don't add extra spaces here because get_text(separator=' ') will handle it
                        replacement = f"[{link_text}]({full_link})"
                        a_tag.replace_with(replacement)
                    # ---------------------------

                    # Append text (now containing markdown links)
                    # IMPORTANT: Use separator=' ' to prevent "word1word2" merging across tags
                    text = current.get_text(separator=' ', strip=True)
                    
                    # Clean up multiple spaces potentially created by separator
                    text = ' '.join(text.split())
                    
                    if text:
                        content_parts.append(text)
                
                current = current.next_sibling
        else:
            # Fallback or alternative structure if start node missing?
            # For now, just log and skip
            print(f"Warning: Start node 'div.article-help-heading' not found for {url}")
            # we might want to try to grab the body or something, but strict rules say "starts at 1 tag"
        
        full_content = "\n".join(content_parts)
        
        return {
            "header": header,
            "content": full_content,
            "success": True
        }

    except Exception as e:
        print(f"Error scraping {url}: {e}")
        return {"success": False, "error": str(e)}

def main():
    if not os.path.exists(INPUT_FILE):
        print(f"Input file {INPUT_FILE} not found. Run ingest_urls.py first.")
        return

    with open(INPUT_FILE, "r", encoding="utf-8") as f:
        url_list = json.load(f)
    
    scraped_data = []
    
    print(f"Starting scrape for {len(url_list)} URLs...")
    
    for i, item in enumerate(url_list):
        url = item["url"]
        category = item["category"]
        
        print(f"[{i+1}/{len(url_list)}] Scraping {url}...")
        result = scrape_url(url)
        
        if result["success"]:
            scraped_data.append({
                "url": url,
                "category": category,
                "header": result["header"],
                "content": result["content"]
            })
            
        # Be nice to the server
        time.sleep(0.5)

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(scraped_data, f, indent=4)
        
    print(f"Scraping complete. Saved {len(scraped_data)} records to {OUTPUT_FILE}")

if __name__ == "__main__":
    main()
