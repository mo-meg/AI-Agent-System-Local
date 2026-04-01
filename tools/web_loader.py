import requests
from bs4 import BeautifulSoup

def extract_text_from_url(url: str) -> str:
    try:
        res = requests.get(url, timeout=10)
        soup = BeautifulSoup(res.text, "html.parser")

        paragraphs = [p.get_text() for p in soup.find_all("p")]
        return "\n".join(paragraphs[:20])  # limit content
    except Exception as e:
        return f"Error loading URL: {e}"