# ─────────────────────────────────────────────
#  fetcher.py  —  News articles from NewsAPI
# ─────────────────────────────────────────────

import requests
from urllib.parse import urlparse
from scraper import scrape_article
from config import (
    NEWS_API_KEY, TOPICS, LANGUAGE, TOPICS_EN, LANGUAGE_EN,
    MAX_ARTICLES_PER_TOPIC, MAX_ARTICLE_CHARS,
    MAX_ARTICLES_PER_SOURCE, NEWS_DOMAINS_STR, NEWS_DOMAIN_BLOCKLIST,
)


def _fetch_topic_batch(
    topics: list[str],
    language: str,
    seen_urls: set[str],
) -> list[dict]:
    """Fetch articles for a list of topics in a given language. Mutates seen_urls."""
    articles = []
    for topic in topics:
        print(f"  [fetcher] Topic ({language}): {topic}")
        url = (
            f"https://newsapi.org/v2/everything"
            f"?q={topic}&language={language}"
            f"&sortBy=publishedAt&pageSize={MAX_ARTICLES_PER_TOPIC}"
            f"&domains={NEWS_DOMAINS_STR}"
            f"&apiKey={NEWS_API_KEY}"
        )
        try:
            data = requests.get(url, timeout=10).json()
        except Exception as e:
            print(f"  [fetcher] Error: {e}")
            continue

        topic_source_count: dict[str, int] = {}

        for a in data.get("articles", []):
            article_url = a.get("url", "")
            if not article_url or article_url in seen_urls:
                continue
            if "[Removed]" in a.get("title", ""):
                continue
            article_domain = urlparse(article_url).netloc.lower().removeprefix("www.")
            if article_domain in NEWS_DOMAIN_BLOCKLIST:
                continue

            source_name = a.get("source", {}).get("name", "Unknown")
            if topic_source_count.get(source_name, 0) >= MAX_ARTICLES_PER_SOURCE:
                continue

            seen_urls.add(article_url)

            full_text = scrape_article(article_url, max_chars=MAX_ARTICLE_CHARS)
            content   = full_text if full_text else a.get("description", "")
            if not content:
                continue

            topic_source_count[source_name] = topic_source_count.get(source_name, 0) + 1
            articles.append({
                "title":       a.get("title", "").strip(),
                "content":     content,
                "source":      source_name,
                "url":         article_url,
                "publishedAt": a.get("publishedAt", ""),
            })

        topic_sources = list(topic_source_count.keys())
        print(f"  [fetcher] '{topic}': {sum(topic_source_count.values())} articles from {len(topic_sources)} sources: {topic_sources}")

    return articles


def fetch_news(prior_urls: set[str] | None = None) -> list[dict]:
    seen_urls = set(prior_urls) if prior_urls else set()

    es_articles = _fetch_topic_batch(TOPICS, LANGUAGE, seen_urls)
    en_articles = _fetch_topic_batch(TOPICS_EN, LANGUAGE_EN, seen_urls)
    all_articles = es_articles + en_articles

    print(f"  [fetcher] {len(es_articles)} ES + {len(en_articles)} EN = {len(all_articles)} articles collected total")
    return all_articles
