# ─────────────────────────────────────────────
#  scraper.py  —  Full article text extractor
# ─────────────────────────────────────────────

import requests
from bs4 import BeautifulSoup

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    )
}


def scrape_article(url: str, max_chars: int = 3000) -> str | None:
    try:
        response = requests.get(url, headers=HEADERS, timeout=8)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "lxml")
        for tag in soup(["script", "style", "nav", "footer", "aside", "header", "figure"]):
            tag.decompose()
        paragraphs = soup.find_all("p")
        text = " ".join(p.get_text(separator=" ") for p in paragraphs)
        text = " ".join(text.split())
        if len(text) < 100:
            return None
        return text[:max_chars]
    except Exception as e:
        print(f"  [scraper] Could not fetch {url}: {e}")
        return None
