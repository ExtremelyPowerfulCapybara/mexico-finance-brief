# ─────────────────────────────────────────────
#  fetcher.py  —  News articles from NewsAPI
# ─────────────────────────────────────────────

import requests
from scraper import scrape_article
from config import (
    NEWS_API_KEY, TOPICS, LANGUAGE,
    MAX_ARTICLES_PER_TOPIC, MAX_ARTICLE_CHARS,
    NEWS_DOMAINS_STR, MAX_ARTICLES_PER_SOURCE
)


def fetch_news() -> list[dict]:
    seen_urls    = set()
    source_count = {}   # tracks how many articles we've kept per source domain
    all_articles = []

    for topic in TOPICS:
        print(f"  [fetcher] Topic: {topic}")
        url = (
            f"https://newsapi.org/v2/everything"
            f"?q={topic}&language={LANGUAGE}"
            f"&sortBy=publishedAt&pageSize={MAX_ARTICLES_PER_TOPIC}"
            f"&domains={NEWS_DOMAINS_STR}"
            f"&apiKey={NEWS_API_KEY}"
        )
        print(f"  [fetcher] Filtering to {len(NEWS_DOMAINS_STR.split(','))} whitelisted domains")
        try:
            data = requests.get(url, timeout=10).json()
        except Exception as e:
            print(f"  [fetcher] Error: {e}")
            continue

        for a in data.get("articles", []):
            article_url = a.get("url", "")
            if not article_url or article_url in seen_urls:
                continue
            if "[Removed]" in a.get("title", ""):
                continue
            seen_urls.add(article_url)

            # ── Per-source cap ────────────────────────────
            source_name = a.get("source", {}).get("name", "Unknown")
            if source_count.get(source_name, 0) >= MAX_ARTICLES_PER_SOURCE:
                continue

            full_text = scrape_article(article_url, max_chars=MAX_ARTICLE_CHARS)
            content   = full_text if full_text else a.get("description", "")
            if not content:
                continue

            source_count[source_name] = source_count.get(source_name, 0) + 1
            all_articles.append({
                "title":   a.get("title", "").strip(),
                "content": content,
                "source":  a.get("source", {}).get("name", "Unknown"),
                "url":     article_url,
            })

    print(f"  [fetcher] {len(all_articles)} articles collected")
    return all_articles
