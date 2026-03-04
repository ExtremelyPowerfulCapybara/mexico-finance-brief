# ─────────────────────────────────────────────
#  pretty_renderer.py  —  Full-featured HTML
#  for the web archive. Uses Google Fonts,
#  flexbox, CSS classes, and the gauge.
#  Not used for email — only for web hosting.
#
#  CHANGE: Spanish-first with EN/ES toggle.
#  digest is now the full bilingual dict with
#  digest["es"] and digest["en"]. Both are
#  rendered into the page simultaneously.
#  A toggle button at the top switches between
#  them using CSS display show/hide — no reload.
# ─────────────────────────────────────────────

from datetime import date, timedelta
from config import NEWSLETTER_NAME, NEWSLETTER_TAGLINE, AUTHOR_NAME

CSS = """
  * { margin: 0; padding: 0; box-sizing: border-box; }
  body { background: #dde3e8; font-family: 'DM Sans', sans-serif; padding: 40px 16px; }
  .wrap { max-width: 640px; margin: 0 auto; background: #f0f3f5; border: 1px solid #cdd4d9; }

  /* ── Language toggle bar ── */
  /* Sits above the header. Shows current language and a button to switch. */
  .lang-bar {
    display: flex; justify-content: flex-end; align-items: center;
    padding: 8px 48px; background: #f0f3f5; border-bottom: 1px solid #e0e5e8;
    gap: 10px;
  }
  .lang-bar span {
    font-size: 9px; font-weight: 500; letter-spacing: 1.5px;
    text-transform: uppercase; color: #aab4bc;
  }
  .lang-toggle {
    font-size: 9px; font-weight: 700; letter-spacing: 1.5px;
    text-transform: uppercase; color: #1a1a1a;
    background: transparent; border: 1px solid #1a1a1a;
    padding: 4px 10px; cursor: pointer;
    font-family: 'DM Sans', sans-serif;
    transition: background 0.15s, color 0.15s;
  }
  .lang-toggle:hover { background: #1a1a1a; color: #f0f3f5; }

  /* ── lang-es shown by default, lang-en hidden ── */
  /* JavaScript flips these on toggle click */
  .lang-en { display: none; }
  .lang-es { display: block; }
  /* inline variants for spans/links */
  .lang-en-inline { display: none; }
  .lang-es-inline { display: inline; }

  /* Header */
  .header { padding: 40px 48px 28px; border-bottom: 2px solid #1a1a1a; }
  .pub-label { font-size: 9px; font-weight: 500; letter-spacing: 3px; text-transform: uppercase; color: #999; margin-bottom: 10px; }
  .pub-name { font-family: 'Playfair Display', serif; font-size: 36px; font-weight: 700; color: #1a1a1a; line-height: 1.1; margin-bottom: 14px; }
  .pub-meta { display: flex; justify-content: space-between; font-size: 10px; color: #888; letter-spacing: 1px; }

  /* Ticker */
  .ticker { background: #1a1a1a; padding: 10px 48px; border-bottom: 3px solid #f0f3f5; }
  .ticker-inner { display: flex; justify-content: space-between; }
  .tick-item { text-align: center; flex: 1; padding: 6px 8px; border-left: 1px solid #2e2e2e; }
  .tick-item:first-child { border-left: none; }
  .tick-label { display: block; font-size: 8px; font-weight: 500; letter-spacing: 2px; text-transform: uppercase; color: #555; margin-bottom: 4px; }
  .tick-val { font-size: 12px; color: #d4cfc8; }
  .tick-up { color: #6abf7b; font-size: 10px; margin-left: 4px; }
  .tick-down { color: #d4695a; font-size: 10px; margin-left: 4px; }

  /* Weather */
  .weather { background: #1a1a1a; padding: 9px 48px; display: flex; gap: 20px; align-items: center; margin-top: 3px; }
  .weather-city { font-size: 11px; font-weight: 500; color: #f5f2ed; }
  .weather-temp { font-size: 11px; color: #ccc; }
  .weather-humidity { font-size: 11px; color: #ccc; }
  .weather-desc { font-size: 10px; color: #666; font-style: italic; margin-left: auto; }

  /* Editor note */
  .editor-note { padding: 28px 48px; }
  .editor-note p { font-family: 'Playfair Display', serif; font-style: italic; font-size: 15px; color: #444; line-height: 1.8; }
  .editor-sig { margin-top: 12px; font-size: 10px; color: #999; letter-spacing: 1px; text-transform: uppercase; }

  /* Divider */
  .divider { display: flex; align-items: center; gap: 12px; padding: 0 48px; }
  .divider .line { flex: 1; height: 1px; background: #cdd4d9; }

  /* Sentiment gauge */
  .sentiment { padding: 24px 48px; }
  .sentiment-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px; }
  .sentiment-label { font-size: 9px; font-weight: 500; letter-spacing: 2px; text-transform: uppercase; color: #aab4bc; }
  .sentiment-reading { font-size: 11px; font-weight: 500; letter-spacing: 1px; text-transform: uppercase; }
  .sentiment-reading.risk-off { color: #b84a3a; }
  .sentiment-reading.cautious { color: #9a6a1a; }
  .sentiment-reading.risk-on  { color: #4a9e6a; }
  .gauge-track { height: 6px; border-radius: 3px; background: linear-gradient(90deg, #b84a3a, #e8a030, #4a9e6a); position: relative; margin: 0 7px; }
  .gauge-marker { position: absolute; top: 50%; transform: translate(-50%, -50%); width: 14px; height: 14px; border-radius: 50%; background: #f0f3f5; box-shadow: 0 1px 5px rgba(0,0,0,0.2); }
  .gauge-marker.risk-off { border: 2px solid #b84a3a; }
  .gauge-marker.cautious  { border: 2px solid #9a6a1a; }
  .gauge-marker.risk-on   { border: 2px solid #4a9e6a; }
  .gauge-ticks { display: flex; justify-content: space-between; margin-top: 7px; font-size: 8px; font-weight: 500; letter-spacing: 1px; text-transform: uppercase; color: #aab4bc; }
  .sentiment-context { margin-top: 12px; font-family: 'Playfair Display', serif; font-style: italic; font-size: 13.5px; color: #555; line-height: 1.7; }

  /* Stories */
  .story { padding: 24px 48px; }
  .story-meta { display: flex; align-items: center; gap: 8px; margin-bottom: 6px; }
  .story-source { font-size: 9px; font-weight: 500; letter-spacing: 2px; text-transform: uppercase; color: #999; }
  .story-tag { font-size: 8px; font-weight: 500; letter-spacing: 1.5px; text-transform: uppercase; color: #aab4bc; border: 1px solid #cdd4d9; padding: 2px 6px; }
  .story-headline { font-family: 'Playfair Display', serif; font-size: 20px; font-weight: 700; color: #1a1a1a; line-height: 1.3; margin-bottom: 10px; }
  .story-body { font-size: 13.5px; color: #555; line-height: 1.75; margin-bottom: 10px; }
  .read-more { font-size: 10px; font-weight: 500; letter-spacing: 1.5px; text-transform: uppercase; color: #1a1a1a; text-decoration: none; border-bottom: 1px solid #1a1a1a; padding-bottom: 1px; }
  .read-more:hover { color: #555; border-color: #555; }

  /* Currency table */
  .currency { padding: 24px 48px; }
  .section-title { font-size: 9px; font-weight: 500; letter-spacing: 2.5px; text-transform: uppercase; color: #aab4bc; margin-bottom: 14px; }
  .currency-table { width: 100%; border-collapse: collapse; }
  .currency-table th { font-size: 9px; font-weight: 500; letter-spacing: 1.5px; text-transform: uppercase; color: #aab4bc; text-align: left; padding: 0 0 8px; border-bottom: 1px solid #cdd4d9; }
  .currency-table th:not(:first-child) { text-align: right; }
  .currency-table td { font-size: 12.5px; color: #3a4a54; padding: 9px 0; border-bottom: 1px solid #e4e9ec; }
  .currency-table td:not(:first-child) { text-align: right; }
  .currency-table tr:last-child td { border-bottom: none; }
  .currency-table .pair { font-weight: 600; color: #1a1a1a; }
  .up   { color: #4a9e6a; font-size: 11px; }
  .down { color: #b84a3a; font-size: 11px; }
  .flat { color: #aab4bc; font-size: 11px; }

  /* Quote */
  .quote { padding: 28px 48px; background: #e8edf0; }
  .quote-mark { font-family: 'Playfair Display', serif; font-size: 52px; line-height: 0.5; color: #c8d0d6; display: block; margin-bottom: 8px; }
  .quote-text { font-family: 'Playfair Display', serif; font-style: italic; font-size: 15px; color: #3a4a54; line-height: 1.75; margin-bottom: 12px; }
  .quote-attr { font-size: 9px; font-weight: 500; letter-spacing: 1.5px; text-transform: uppercase; color: #8a9aa4; }

  /* Week in review */
  .week { padding: 24px 48px; }
  .timeline { display: flex; flex-direction: column; }
  .tl-row { display: flex; gap: 16px; }
  .tl-left { display: flex; flex-direction: column; align-items: center; width: 44px; flex-shrink: 0; }
  .tl-day { font-size: 8px; font-weight: 500; letter-spacing: 1px; text-transform: uppercase; color: #aab4bc; margin-bottom: 5px; }
  .tl-dot { width: 10px; height: 10px; border-radius: 50%; background: #c8d0d6; border: 2px solid #f0f3f5; outline: 1px solid #c8d0d6; }
  .tl-dot.active { background: #3a4a54; outline-color: #3a4a54; }
  .tl-line { width: 1px; flex: 1; background: #dde3e8; min-height: 16px; margin: 3px 0; }
  .tl-row:last-child .tl-line { display: none; }
  .tl-content { padding-bottom: 20px; flex: 1; }
  .tl-row:last-child .tl-content { padding-bottom: 0; }
  .tl-tag { font-size: 8px; font-weight: 500; letter-spacing: 1.5px; text-transform: uppercase; color: #aab4bc; border: 1px solid #cdd4d9; padding: 2px 6px; display: inline-block; margin-bottom: 5px; }
  .tl-headline { font-family: 'Playfair Display', serif; font-size: 14px; font-weight: 700; color: #1a1a1a; line-height: 1.35; margin-bottom: 4px; }
  .tl-body { font-size: 12px; color: #777; line-height: 1.65; }

  /* Footer */
  .footer { background: #1a1a1a; padding: 22px 48px; display: flex; justify-content: space-between; align-items: center; }
  .footer-name { font-family: 'Playfair Display', serif; font-size: 14px; color: #f5f2ed; }
  .footer-by { font-size: 10px; color: #666; letter-spacing: 1px; }

  /* ── Mobile ── */
  @media (max-width: 600px) {
    body { padding: 0; }
    .wrap { border: none; }
    .header { padding: 28px 20px 20px; }
    .pub-name { font-size: 26px; }
    .ticker { padding: 6px 8px; }
    .ticker-inner { flex-wrap: wrap; }
    .tick-item { flex: 1 1 45%; padding: 8px 4px; }
    .weather { padding: 9px 20px; flex-wrap: wrap; gap: 8px; }
    .weather-desc { margin-left: 0; width: 100%; }
    .editor-note, .sentiment, .story, .currency, .quote, .week { padding: 20px 20px; }
    .story-headline { font-size: 17px; }
    .currency-table { font-size: 11px; }
    .footer { padding: 18px 20px; flex-direction: column; align-items: flex-start; gap: 6px; }
    .lang-bar { padding: 8px 20px; }
  }
"""

DIVIDER = """
<div class="divider">
  <div class="line"></div>
  <svg width="14" height="14" viewBox="0 0 18 18" fill="none">
    <rect x="7" y="0" width="4" height="4" fill="#b0bec8"/>
    <rect x="0" y="7" width="4" height="4" fill="#b0bec8"/>
    <rect x="14" y="7" width="4" height="4" fill="#b0bec8"/>
    <rect x="7" y="14" width="4" height="4" fill="#b0bec8"/>
  </svg>
  <div class="line"></div>
</div>"""

# JavaScript that powers the toggle.
# It flips .lang-es / .lang-en display on button click,
# and updates the button label to show the current language.
TOGGLE_JS = """
<script>
  var currentLang = 'es';

  function setLang(lang) {
    var showCls = 'lang-' + lang;
    var hideCls = 'lang-' + (lang === 'es' ? 'en' : 'es');
    var showInline = 'lang-' + lang + '-inline';
    var hideInline = 'lang-' + (lang === 'es' ? 'en' : 'es') + '-inline';

    // Block elements (divs, paragraphs)
    document.querySelectorAll('.' + showCls).forEach(function(el) { el.style.display = 'block'; });
    document.querySelectorAll('.' + hideCls).forEach(function(el) { el.style.display = 'none'; });

    // Inline elements (spans, links)
    document.querySelectorAll('.' + showInline).forEach(function(el) { el.style.display = 'inline'; });
    document.querySelectorAll('.' + hideInline).forEach(function(el) { el.style.display = 'none'; });

    currentLang = lang;

    // Update button label and the "reading in" text
    document.getElementById('lang-btn').textContent = lang === 'es' ? 'Read in English' : 'Leer en español';
    document.getElementById('lang-reading').textContent = lang === 'es' ? 'ES' : 'EN';
  }

  document.getElementById('lang-btn').addEventListener('click', function() {
    setLang(currentLang === 'es' ? 'en' : 'es');
  });
</script>
"""


def build_pretty_html(
    digest:             dict,
    tickers:            list[dict],
    currency:           list[dict],
    weather:            dict,
    week_stories:       list[dict],
    issue_number:       int = 1,
    is_friday:          bool = False,
    wordcloud_filename: str | None = None,
) -> str:
    # CHANGE: digest is now the full bilingual dict.
    # We split it here for clarity.
    digest_es = digest.get("es", digest)  # fallback to flat dict for old digests
    digest_en = digest.get("en", digest)

    # ── Date formatted in both languages ──────────
    today      = date.today()
    days_es    = ["LUNES","MARTES","MIÉRCOLES","JUEVES","VIERNES","SÁBADO","DOMINGO"]
    months_es  = ["","ENERO","FEBRERO","MARZO","ABRIL","MAYO","JUNIO",
                  "JULIO","AGOSTO","SEPTIEMBRE","OCTUBRE","NOVIEMBRE","DICIEMBRE"]
    months_en  = ["","JANUARY","FEBRUARY","MARCH","APRIL","MAY","JUNE",
                  "JULY","AUGUST","SEPTEMBER","OCTOBER","NOVEMBER","DECEMBER"]
    days_en    = ["MONDAY","TUESDAY","WEDNESDAY","THURSDAY","FRIDAY","SATURDAY","SUNDAY"]

    today_es   = f"{days_es[today.weekday()]}, {today.day:02d} DE {months_es[today.month]} DE {today.year}"
    today_en   = f"{days_en[today.weekday()]}, {months_en[today.month]} {today.day:02d}, {today.year}"
    issue_date = f"{months_en[today.month]} {today.day}, {today.year}"

    # ── Ticker (language-neutral — numbers don't change) ──
    tick_items = ""
    for t in tickers:
        chg_cls = "tick-up" if t["direction"] == "up" else ("tick-down" if t["direction"] == "down" else "")
        tick_items += f"""
      <div class="tick-item">
        <span class="tick-label">{t['label']}</span>
        <span class="tick-val">{t['value']}</span>
        <span class="{chg_cls}">{t['change']}</span>
      </div>"""

    # ── Sentiment gauge ──────────────────────────
    # CHANGE: reads label_es/label_en and context_es/context_en
    # The gauge position is language-neutral (same number either way)
    s         = digest_es.get("sentiment", {})
    label_es  = s.get("label_es", "Cauteloso")
    label_en  = s.get("label_en", "Cautious")
    context_es= s.get("context_es", "")
    context_en= s.get("context_en", "")
    position  = max(5, min(95, int(s.get("position", 50))))
    cls_map   = {"Cautious": "cautious", "Risk-Off": "risk-off", "Risk-On": "risk-on"}
    sent_cls  = cls_map.get(label_en, "cautious")

    # ── Stories — rendered twice (ES + EN) ───────
    # Each story block has a lang-es div and a lang-en div.
    # The toggle JS shows/hides them. The URL and source
    # are language-neutral so they're outside both divs.
    stories_html = ""
    es_stories = digest_es.get("stories", [])
    en_stories = digest_en.get("stories", [])

    for i in range(max(len(es_stories), len(en_stories))):
        s_es = es_stories[i] if i < len(es_stories) else {}
        s_en = en_stories[i] if i < len(en_stories) else s_es  # fallback to ES

        stories_html += f"""
{DIVIDER}
<div class="story">
  <div class="story-meta">
    <span class="story-source">{s_es.get('source','')}</span>
    <span class="story-tag">{s_es.get('tag','')}</span>
  </div>

  <div class="lang-es">
    <div class="story-headline">{s_es.get('headline','')}</div>
    <div class="story-body">{s_es.get('body','')}</div>
    <a href="{s_es.get('url','#')}" class="read-more">Leer m&aacute;s &rarr;</a>
  </div>
  <div class="lang-en">
    <div class="story-headline">{s_en.get('headline','')}</div>
    <div class="story-body">{s_en.get('body','')}</div>
    <a href="{s_en.get('url','#')}" class="read-more">Read more &rarr;</a>
  </div>
</div>"""

    # ── Currency table (language-neutral numbers) ─
    tbody = ""
    for r in currency:
        c1 = "up" if r['chg_1d']['cls'] == 'chg-up' else ("down" if r['chg_1d']['cls'] == 'chg-down' else "flat")
        c7 = "up" if r['chg_1w']['cls'] == 'chg-up' else ("down" if r['chg_1w']['cls'] == 'chg-down' else "flat")
        tbody += f"""
      <tr>
        <td class="pair">{r['pair']}</td>
        <td>{r['rate']}</td>
        <td class="{c1}">{r['chg_1d']['text']}</td>
        <td class="{c7}">{r['chg_1w']['text']}</td>
      </tr>"""

    # ── Quote (same in both — quotes aren't translated) ──
    q = digest_es.get("quote", {})

    # ── Week in review — also bilingual ──────────
    week_html = ""
    if is_friday and week_stories:
        monday = today - timedelta(days=today.weekday())
        friday_dt = monday + timedelta(days=4)

        months_short_es = ["","ene","feb","mar","abr","may","jun",
                           "jul","ago","sep","oct","nov","dic"]
        months_short_en = ["","Jan","Feb","Mar","Apr","May","Jun",
                           "Jul","Aug","Sep","Oct","Nov","Dec"]

        wlabel_es = f"{monday.day} {months_short_es[monday.month]}–{friday_dt.day} {months_short_es[friday_dt.month]}, {friday_dt.year}"
        wlabel_en = f"{months_short_en[monday.month]} {monday.day}–{friday_dt.day}, {friday_dt.year}"

        tl_items = ""
        for ws in week_stories:
            dot_cls = "active" if ws.get("active") else ""
            tl_items += f"""
      <div class="tl-row">
        <div class="tl-left">
          <div class="tl-day">{ws['day']}</div>
          <div class="tl-dot {dot_cls}"></div>
          <div class="tl-line"></div>
        </div>
        <div class="tl-content">
          <span class="tl-tag">{ws['tag']}</span>
          <div class="tl-headline">{ws['headline']}</div>
          <div class="tl-body">{ws['body']}</div>
        </div>
      </div>"""

        week_html = f"""
{DIVIDER}
<div class="week">
  <div class="lang-es"><div class="section-title">Resumen Semanal &middot; {wlabel_es}</div></div>
  <div class="lang-en"><div class="section-title">Week in Review &middot; {wlabel_en}</div></div>
  <div class="timeline">{tl_items}
  </div>
</div>"""

    # ── Word cloud ────────────────────────────────
    wordcloud_html = ""
    if is_friday and wordcloud_filename:
        wordcloud_html = f"""
{DIVIDER}
<div style="padding:24px 48px 8px;">
  <div class="lang-es"><div class="section-title">La Semana en Palabras</div></div>
  <div class="lang-en"><div class="section-title">Week in Words</div></div>
  <img src="{wordcloud_filename}" style="width:100%; display:block; border:1px solid #cdd4d9;" alt="Nube de palabras"/>
</div>"""

    return f"""<!DOCTYPE html>
<html lang="es">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{NEWSLETTER_NAME} &mdash; {issue_date}</title>
  <link href="https://fonts.googleapis.com/css2?family=Playfair+Display:ital,wght@0,400;0,700;1,400&family=DM+Sans:wght@300;400;500&display=swap" rel="stylesheet">
  <style>{CSS}</style>
</head>
<body>
<div class="wrap">

  <!-- Language toggle bar -->
  <!-- "reading in ES" shows current language. Button switches to the other. -->
  <div class="lang-bar">
    <span>Leyendo en <span id="lang-reading">ES</span></span>
    <button class="lang-toggle" id="lang-btn">Read in English</button>
  </div>

  <div class="header">
    <div class="pub-label">{NEWSLETTER_TAGLINE}</div>
    <div class="pub-name">{NEWSLETTER_NAME}</div>
    <div class="pub-meta">
      <span>
        <span class="lang-es-inline">{today_es}</span>
        <span class="lang-en-inline">{today_en}</span>
      </span>
      <span>
        <span class="lang-es-inline">EDICIÓN NO. {issue_number}</span>
        <span class="lang-en-inline">ISSUE NO. {issue_number}</span>
      </span>
    </div>
  </div>

  <div class="ticker">
    <div class="ticker-inner">{tick_items}
    </div>
  </div>

  <div class="weather">
    <span class="weather-city">{weather['city']}</span>
    <span class="weather-temp">{weather['high_low']}</span>
    <span class="weather-humidity">{weather['humidity']}</span>
    <span class="weather-desc">{weather['desc']}</span>
  </div>

  <!-- Editor note — two versions, toggle switches between them -->
  <div class="editor-note">
    <div class="lang-es">
      <p>{digest_es.get('editor_note','')}</p>
    </div>
    <div class="lang-en">
      <p>{digest_en.get('editor_note','')}</p>
    </div>
    <div class="editor-sig">&mdash; {AUTHOR_NAME}</div>
  </div>

  {DIVIDER}

  <!-- Sentiment gauge — position is universal, labels switch -->
  <div class="sentiment">
    <div class="sentiment-header">
      <span class="sentiment-label">
        <span class="lang-es-inline">Sentimiento del D&iacute;a</span>
        <span class="lang-en-inline">Market Sentiment</span>
      </span>
      <span class="sentiment-reading {sent_cls}">
        <span class="lang-es-inline">{label_es}</span>
        <span class="lang-en-inline">{label_en}</span>
      </span>
    </div>
    <div class="gauge-track">
      <div class="gauge-marker {sent_cls}" style="left:{position}%;"></div>
    </div>
    <div class="gauge-ticks">
      <span>
        <span class="lang-es-inline">Aversi&oacute;n al Riesgo</span>
        <span class="lang-en-inline">Risk-Off</span>
      </span>
      <span>Neutral</span>
      <span>
        <span class="lang-es-inline">Apetito por Riesgo</span>
        <span class="lang-en-inline">Risk-On</span>
      </span>
    </div>
    <div class="sentiment-context">
      <div class="lang-es">{context_es}</div>
      <div class="lang-en">{context_en}</div>
    </div>
  </div>

  <!-- Stories -->
  {stories_html}

  {DIVIDER}

  <!-- Currency table — numbers are universal, headers switch -->
  <div class="currency">
    <div class="lang-es"><div class="section-title">Tipo de Cambio</div></div>
    <div class="lang-en"><div class="section-title">Currency Table</div></div>
    <table class="currency-table">
      <thead>
        <tr>
          <th>
            <span class="lang-es-inline">Par</span>
            <span class="lang-en-inline">Pair</span>
          </th>
          <th>
            <span class="lang-es-inline">Tipo</span>
            <span class="lang-en-inline">Rate</span>
          </th>
          <th>1D</th>
          <th>
            <span class="lang-es-inline">1S</span>
            <span class="lang-en-inline">1W</span>
          </th>
        </tr>
      </thead>
      <tbody>{tbody}
      </tbody>
    </table>
  </div>

  {DIVIDER}

  <!-- Quote — same in both languages -->
  <div class="quote">
    <span class="quote-mark">&ldquo;</span>
    <div class="quote-text">{q.get('text','')}</div>
    <div class="quote-attr">{q.get('attribution','')}</div>
  </div>

  <!-- Week in review -->
  {week_html}

  <!-- Word cloud -->
  {wordcloud_html}

  <div class="footer">
    <span class="footer-name">{NEWSLETTER_NAME}</span>
    <span class="footer-by">
      <span class="lang-es-inline">por {AUTHOR_NAME}</span>
      <span class="lang-en-inline">by {AUTHOR_NAME}</span>
    </span>
  </div>

</div>

{TOGGLE_JS}
</body>
</html>"""
