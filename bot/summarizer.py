# ─────────────────────────────────────────────
#  summarizer.py  —  Claude generates digest
# ─────────────────────────────────────────────

import json
import time
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
  "editor_note": "2-3 sentences opening the day's briefing. Always open with 'Fellow Humans,' as the first two words. Voice: sharp, dry, occasionally sardonic — like a seasoned markets editor who has seen every cycle and finds the current one both alarming and faintly amusing. Reference the dominant story. First person. Do NOT include any sign-off or signature — that is added separately. No fluff, no filler, no 'it is worth noting'.",

  "sentiment": {{
    "label": "Risk-Off" | "Cautious" | "Risk-On",
    "position": <integer 5-95 where 5=extreme risk-off, 50=neutral, 95=extreme risk-on>,
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
- sentiment.position must be consistent with sentiment.label: Risk-Off should be 5-35, Cautious 36-64, Risk-On 65-95

Articles:
{news_text}
"""

    print("  [summarizer] Sending to Claude...")
    for attempt in range(4):
        try:
            message = client.messages.create(
                model="claude-sonnet-4-6",
                max_tokens=4096,
                messages=[{"role": "user", "content": prompt}]
            )
            break
        except Exception as e:
            if "overloaded" in str(e).lower() and attempt < 3:
                wait = 30 * (attempt + 1)
                print(f"  [summarizer] API overloaded, retrying in {wait}s (attempt {attempt + 1}/4)...")
                time.sleep(wait)
            else:
                raise
            
    raw = message.content[0].text.strip()

    # Strip markdown fences if present
    if raw.startswith("```"):
        raw = raw.split("\n", 1)[1]
        raw = raw.rsplit("```", 1)[0]

    return json.loads(raw)
