# ─────────────────────────────────────────────
#  summarizer.py  —  Claude generates digest
# ─────────────────────────────────────────────

import json
import anthropic
from config import ANTHROPIC_API_KEY, AUTHOR_NAME

client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)


def summarize_news(articles: list[dict]) -> dict:
    """
    Sends articles to Claude and returns a structured digest dict with:
    - editor_note: str
    - sentiment: {label, context}
    - stories: [{source, headline, body, url, tag}]
    - quote: {text, attribution}
    """
    news_text = ""
    for i, a in enumerate(articles, 1):
        news_text += f"{i}. [{a['source']}] {a['title']}\nURL: {a['url']}\n{a['content']}\n\n"

    prompt = f"""You are a sharp financial news editor producing a daily morning briefing. Address the reader as "Fellow Humans" at most once in the editor note. Voice is sharp, dry, and editorial. No fluff.

Analyze the articles below and return a JSON object with EXACTLY this structure:

{{
  "editor_note": "2-3 sentence conversational opening in the voice of a sharp, concise financial editor. Reference the dominant theme of the day. First person, signed off naturally. No fluff.",

  "sentiment": {{
    "label": "Risk-Off" | "Cautious" | "Risk-On",
    "context": "One sentence explaining today's sentiment based on the stories."
  }},

  "stories": [
    {{
      "source": "Source name",
      "headline": "Concise, specific headline",
      "body": "2-3 sentences. Include specific figures, names, and why it matters. End naturally.",
      "url": "original article URL",
      "tag": "One of: Macro | FX | Mexico | Trade | Rates | Markets | Energy | Politics"
    }}
  ],

  "quote": {{
    "text": "A relevant financial or economic quote that connects thematically to today's news. Must be a real, verifiable quote.",
    "attribution": "Full name, source, year"
  }}
}}

Rules:
- Select 5-7 stories, ordered by importance
- Skip duplicates covering the same event
- stories must include the original URL from the article list
- Respond ONLY with the JSON object, no preamble, no markdown fences

Articles:
{news_text}
"""

    print("  [summarizer] Sending to Claude...")
    message = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=2500,
        messages=[{"role": "user", "content": prompt}]
    )

    raw = message.content[0].text.strip()

    # Strip markdown fences if present
    if raw.startswith("```"):
        raw = raw.split("\n", 1)[1]
        raw = raw.rsplit("```", 1)[0]

    return json.loads(raw)
