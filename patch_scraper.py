import requests
from bs4 import BeautifulSoup
import json
import os
from urllib.parse import urljoin

INPUT_FILE = "data/scraped_content.json"
TARGET_URL = "https://www.nestpensions.org.uk/schemeweb/memberhelpcentre/opting-out/how-to-opt-out.html"
CATEGORY = "Member"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
}

STOP_CLASSES = {
    "related_articles", 
    "table-outer-wrapper", 
    "article-help-feedback", 
    "feedback-wrapper", 
    "was-this-page-helpful"
}

def scrape_single_url(url):
    print(f"Scraping manually: {url}")
    try:
        response = requests.get(url, headers=HEADERS, timeout=15)
        response.raise_for_status()
        soup = BeautifulSoup(response.content, "html.parser")
        
        header_tag = soup.find("h1")
        header = header_tag.get_text(strip=True) if header_tag else "No Header Found"
        
        content_parts = []
        # Try both selectors
        start_node = soup.find("div", class_="article-help-heading")
        if not start_node:
             start_node = header_tag
        
        if start_node:
            current = start_node.next_sibling
            while current:
                if current.name:
                    classes = current.get("class", [])
                    if any(cls in STOP_CLASSES for cls in classes):
                        break 
                    
                    for a_tag in current.find_all("a", href=True):
                        href = a_tag["href"]
                        if href.lower().startswith("javascript:") or href.strip() == "#":
                            continue
                        full_link = urljoin(url, href)
                        link_text = a_tag.get_text(strip=True)
                        replacement = f"[{link_text}]({full_link})"
                        a_tag.replace_with(replacement)

                    text = current.get_text(separator=' ', strip=True)
                    text = ' '.join(text.split())
                    if text:
                        content_parts.append(text)
                current = current.next_sibling
        else:
            print("STILL NO START NODE FOUND")
        
        return {
            "url": url,
            "category": CATEGORY,
            "header": header,
            "content": "\n".join(content_parts)
        }

    except Exception as e:
        print(f"Error: {e}")
        return None

def main():
    # 1. Scrape the new item
    new_item = scrape_single_url(TARGET_URL)
    
    if not new_item or not new_item["content"]:
        print("Failed to scrape content.")
        return

    # 2. Load existing data
    if os.path.exists(INPUT_FILE):
        with open(INPUT_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
    else:
        data = []

    # 3. Remove if exists already (to avoid dupes)
    data = [d for d in data if d["url"] != TARGET_URL]
    
    # 4. Append
    data.append(new_item)
    print(f"Added new item. Header: {new_item['header']}")
    print(f"Content length: {len(new_item['content'])}")
    
    # 5. Save
    with open(INPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4)
    print("scraped_content.json updated.")

if __name__ == "__main__":
    main()
