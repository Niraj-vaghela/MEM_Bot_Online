import requests
from bs4 import BeautifulSoup

url = "https://www.nestpensions.org.uk/schemeweb/memberhelpcentre/retirement-pot/how-to-take-money-out.html"
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
}

try:
    response = requests.get(url, headers=headers, timeout=10)
    response.raise_for_status()
    soup = BeautifulSoup(response.content, "html.parser")
    
    print(f"Title: {soup.title.string if soup.title else 'No Title'}")
    
    h1s = soup.find_all("h1")
    print(f"H1 tags found: {len(h1s)}")
    for h in h1s:
        print(f" - {h.get_text(strip=True)}")
        
    h2s = soup.find_all("h2")
    print(f"H2 tags found: {len(h2s)}")
    for h in h2s:
        print(f" - {h.get_text(strip=True)}")

    heading_divs = soup.find_all("div", class_="article-help-heading")
    print(f"Div.article-help-heading found: {len(heading_divs)}")

except Exception as e:
    print(f"Error: {e}")
