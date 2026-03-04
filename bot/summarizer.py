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
 Sends articles to Claude and returns a BILINGUAL digest:

    {
      "es": {
        "editor_note": str,
        "sentiment":   {label, position, context},
        "stories":     [{source, headline, body, url, tag}],
        "quote":       {text, attribution}
      },
      "en": {
        ... same structure, English translation ...
      }
    }

    The "es" block is the primary version — written natively
    in Spanish with full personality and voice.
    The "en" block is a faithful English translation of the
    same content, same stories, same data.

    Callers that previously expected a flat dict (editor_note,
    stories, etc.) should now read digest["es"] for Spanish
    and digest["en"] for English.
    """

  # ── Build the articles text block ──────────

    news_text = ""
    for i, a in enumerate(articles, 1):
        news_text += f"{i}. [{a['source']}] {a['title']}\nURL: {a['url']}\n{a['content']}\n\n"

    # ── The prompt ─────────────────────────────
    # KEY CHANGE: We now ask Claude to return a JSON with two
    # top-level keys: "es" and "en". Each contains the full
    # digest structure. Spanish is written natively — not
    # translated from English. English is translated from Spanish.
    #
    # We also updated the voice/identity: the newsletter now
    # speaks from inside emerging markets (MX, ES, AR) rather
    # than as a generic English-language finance publication.
    #
    # The sentiment labels are bilingual too — the "label" field
    # returns both so the renderer can display the right one
    # without needing to translate on the fly.



    prompt = f"""Eres el editor de un newsletter financiero diario para una audiencia hispanohablante sofisticada. Escribes con autoridad desde adentro de los mercados emergentes — Ciudad de México, Madrid, Buenos Aires. Tu voz es aguda, seca y editorial. Sin relleno

Analyze the articles below and return a JSON object with EXACTLY this structure:

{{
  "es": {{
    "editor_note": "2-3 oraciones abriendo el briefing del día. Siempre abre con 'Estimados humanos,' como las primeras dos palabras. Voz: aguda, seca, ocasionalmente sardónica — como un editor de mercados veterano que ha visto cada ciclo y encuentra el actual tanto alarmante como levemente divertido. Referencia la historia dominante. Primera persona. NO incluyas despedida ni firma — se agrega por separado. Sin relleno, sin 'cabe destacar'.",

    "sentiment": {{
      "label_es": "Aversión al Riesgo" | "Cauteloso" | "Apetito por Riesgo",
      "label_en": "Risk-Off" | "Cautious" | "Risk-On",
      "position": "<integer 5-95 donde 5=máxima aversión al riesgo, 50=neutral, 95=máximo apetito por riesgo>",
      "context_es": "Una oración explicando el sentimiento de hoy basado en las historias. En español.",
      "context_en": "One sentence explaining today's sentiment based on the stories. In English."
    }},

    "stories": [
      {{
        "source": "Nombre de la fuente",
        "headline": "Titular conciso y específico en español",
        "body": "2-3 oraciones. Incluye cifras específicas, nombres y por qué importa. Termina naturalmente. En español.",
        "url": "URL original del artículo",
        "tag": "Uno de: Macro | FX | México | Comercio | Tasas | Mercados | Energía | Política"
      }}
    ],

    "quote": {{
      "text": "Una cita financiera o económica relevante que conecte temáticamente con las noticias de hoy. Debe ser una cita real y verificable. Puede estar en español o inglés según el autor original.",
      "attribution": "Nombre completo, fuente, año"
    }}
  }},

  "en": {{
    "editor_note": "Faithful English translation of the Spanish editor note. Same voice, same content. Always opens with 'Fellow Humans,' as the first two words.",

    "sentiment": {{
      "label_es": "<same as es block>",
      "label_en": "<same as es block>",
      "position": "<same integer as es block>",
      "context_es": "<same as es block>",
      "context_en": "<English translation of context>"
    }},

    "stories": [
      {{
        "source": "Source name",
        "headline": "Faithful English translation of the Spanish headline",
        "body": "Faithful English translation of the Spanish body. Same figures, same facts.",
        "url": "same original article URL",
        "tag": "One of: Macro | FX | Mexico | Trade | Rates | Markets | Energy | Politics"
      }}
    ],

    "quote": {{
      "text": "Same quote as Spanish block — quotes are not translated unless originally in Spanish",
      "attribution": "Same attribution as Spanish block"
    }}
  }}
}}

Reglas:
- Selecciona 5-7 historias, ordenadas por importancia
- Omite duplicados que cubran el mismo evento
- stories debe incluir la URL original de la lista de artículos
- El bloque "en" debe ser una traducción fiel del bloque "es" — mismas historias, mismos datos
- Responde ÚNICAMENTE con el objeto JSON, sin preámbulo, sin markdown
- sentiment.position debe ser consistente con los labels: Aversión al Riesgo = 5-35, Cauteloso = 36-64, Apetito por Riesgo = 65-95

Artículos:
{news_text}
"""

    # ── API call (unchanged logic) ──────────────
    # Same retry logic as before — 4 attempts with
    # increasing wait times if the API is overloaded.
    print("  [summarizer] Sending to Claude (bilingual)...")
    for attempt in range(4):
        try:
            message = client.messages.create(
                model="claude-sonnet-4-6",
                max_tokens=6000,   # CHANGE: increased from 4096 to fit two full digests
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

    # ── Strip markdown fences if present ────────
    # Claude sometimes wraps JSON in ```json ... ```
    # even when told not to. This strips that safely.
    if raw.startswith("```"):
        raw = raw.split("\n", 1)[1]
        raw = raw.rsplit("```", 1)[0]

    # ── Parse and validate ───────────────────────
    # We parse the JSON and do a basic check that
    # both "es" and "en" keys are present. If not,
    # we raise a clear error rather than silently
    # sending a broken digest.
    digest = json.loads(raw)

    if "es" not in digest or "en" not in digest:
        raise ValueError(
            f"[summarizer] Claude returned JSON missing 'es' or 'en' key.\n"
            f"Got keys: {list(digest.keys())}"
        )

    print(f"  [summarizer] Got {len(digest['es']['stories'])} stories (ES+EN)")
    return digest
