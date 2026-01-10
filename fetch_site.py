import requests
import os

url = "https://www.nestpensions.org.uk/schemeweb/memberhelpcentre.html"
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
}

try:
    response = requests.get(url, headers=headers)
    response.raise_for_status()
    
    html_content = response.text
    
    # Inject <base> tag to make relative links work
    base_tag = '<base href="https://www.nestpensions.org.uk/schemeweb/">'
    if "<head>" in html_content:
        html_content = html_content.replace("<head>", f"<head>\n{base_tag}")
    else:
        # Fallback if no head tag (unlikely)
        html_content = base_tag + html_content

    # Save to file
    output_path = os.path.join("local_site", "index.html")
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(html_content)
        
    print(f"Successfully saved page to {output_path}")

except Exception as e:
    print(f"Error fetching page: {e}")
