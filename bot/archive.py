# ─────────────────────────────────────────────
#  archive.py  —  Saves pretty HTML issues and
#  rebuilds index.html with a full dashboard:
#  sentiment timeline, volatility, story count,
#  and issue cards.
#
#  CHANGE: digest is now bilingual {es, en}.
#  All reads from saved digests now go through
#  digest["es"] for display. The index page
#  is Spanish-first with English labels as
#  secondary where needed.
# ─────────────────────────────────────────────

import os
import json
from datetime import date, datetime
from pretty_renderer import build_pretty_html
from config import NEWSLETTER_NAME, AUTHOR_NAME, DIGEST_DIR, ARCHIVE_DIR

GITHUB_PAGES_URL = "https://extremelypowerfulcapybara.github.io/News-Digest"


def save_pretty_issue(
    digest:             dict,
    tickers:            list[dict],
    currency:           list[dict],
    weather:            dict,
    week_stories:       list[dict],
    issue_number:       int,
    is_friday:          bool = False,
    wordcloud_filename: str | None = None,
) -> str:
    os.makedirs(ARCHIVE_DIR, exist_ok=True)
    today    = date.today().isoformat()
    filename = f"{today}.html"
    filepath = os.path.join(ARCHIVE_DIR, filename)

    # digest is the full bilingual dict — pretty_renderer handles both
    html = build_pretty_html(
        digest             = digest,
        tickers            = tickers,
        currency           = currency,
        weather            = weather,
        week_stories       = week_stories,
        issue_number       = issue_number,
        is_friday          = is_friday,
        wordcloud_filename = wordcloud_filename,
    )

    with open(filepath, "w", encoding="utf-8") as f:
        f.write(html)

    print(f"  [archive] Saved pretty issue to {filepath}")
    rebuild_index()
    return filepath


def _load_all_digests() -> list[dict]:
    """
    Loads all saved digest JSONs from DIGEST_DIR, sorted oldest first.
    Each entry: { date, label_es, label_en, position, story_count, headline }

    CHANGE: reads from digest["es"] for bilingual digests,
    falls back to flat structure for old digests.
    """
    entries = []
    if not os.path.exists(DIGEST_DIR):
        return entries

    for filename in sorted(os.listdir(DIGEST_DIR)):
        if not filename.endswith(".json"):
            continue
        date_str = filename.replace(".json", "")
        try:
            datetime.strptime(date_str, "%Y-%m-%d")
        except ValueError:
            continue

        with open(os.path.join(DIGEST_DIR, filename), encoding="utf-8") as f:
            data = json.load(f)

        digest    = data.get("digest", {})

        # CHANGE: support both bilingual and old flat digests
        digest_es = digest.get("es", digest)

        sentiment  = digest_es.get("sentiment", {})
        stories    = digest_es.get("stories", [])
        headline   = stories[0].get("headline", "") if stories else ""

        # CHANGE: read both label variants — fall back gracefully
        label_es = sentiment.get("label_es", sentiment.get("label", "Cauteloso"))
        label_en = sentiment.get("label_en", sentiment.get("label", "Cautious"))

        entries.append({
            "date":        date_str,
            "label_es":    label_es,
            "label_en":    label_en,
            "position":    int(sentiment.get("position", 50)),
            "story_count": len(stories),
            "headline":    headline,
        })

    return entries


def rebuild_index() -> None:
    os.makedirs(ARCHIVE_DIR, exist_ok=True)

    # ── Load digest data for charts ───────────
    digest_data = _load_all_digests()

    # ── Build chart data arrays ───────────────
    chart_dates    = [d["date"]        for d in digest_data]
    chart_position = [d["position"]    for d in digest_data]
    chart_stories  = [d["story_count"] for d in digest_data]
    chart_labels   = [d["label_en"]    for d in digest_data]  # English for chart tooltips

    # CHANGE: point colors now match Spanish OR English labels
    def _sent_color(d):
        en = d.get("label_en", "")
        if en == "Risk-Off":  return "#b84a3a"
        if en == "Risk-On":   return "#4a9e6a"
        return "#e8a030"

    point_colors = [_sent_color(d) for d in digest_data]

    # ── Issue cards ───────────────────────────
    issues = sorted(
        [f for f in os.listdir(ARCHIVE_DIR) if f.endswith(".html") and f != "index.html"],
        reverse=True,
    )

    cards = ""
    for i, filename in enumerate(issues):
        issue_date_str = filename.replace(".html", "")
        try:
            dt = datetime.strptime(issue_date_str, "%Y-%m-%d")
            # CHANGE: date label in Spanish
            days_es   = ["Lunes","Martes","Miércoles","Jueves","Viernes","Sábado","Domingo"]
            months_es = ["","enero","febrero","marzo","abril","mayo","junio",
                         "julio","agosto","septiembre","octubre","noviembre","diciembre"]
            label = f"{days_es[dt.weekday()]}, {dt.day} de {months_es[dt.month]} de {dt.year}"
        except ValueError:
            label = issue_date_str

        issue_num   = len(issues) - i
        digest_path = os.path.join(DIGEST_DIR, f"{issue_date_str}.json")
        headline    = ""
        label_es    = ""
        label_en    = ""
        story_count = 0

        if os.path.exists(digest_path):
            with open(digest_path, encoding="utf-8") as f:
                data = json.load(f)

            # CHANGE: read from digest["es"] for bilingual digests
            digest_obj  = data.get("digest", {})
            digest_es   = digest_obj.get("es", digest_obj)
            stories     = digest_es.get("stories", [])
            headline    = stories[0].get("headline", "") if stories else ""
            sentiment   = digest_es.get("sentiment", {})
            label_es    = sentiment.get("label_es", sentiment.get("label", ""))
            label_en    = sentiment.get("label_en", sentiment.get("label", ""))
            story_count = len(stories)

        # CHANGE: pill shows Spanish label, color keyed off English label
        sent_color = {"Risk-Off": "#b84a3a", "Cautious": "#9a6a1a", "Risk-On": "#4a9e6a"}.get(label_en, "#aab4bc")
        sent_pill  = (
            f'<span style="font-size:9px; font-weight:700; letter-spacing:1px; text-transform:uppercase; '
            f'color:{sent_color}; padding:3px 10px; border:1px solid {sent_color}; border-radius:20px;">'
            f'{label_es}</span>'
        ) if label_es else ""
        count_html = f'<span style="font-size:9px; color:#aab4bc; margin-left:10px;">{story_count} notas</span>' if story_count else ""

        cards += f"""
    <a href="{filename}" style="display:block; text-decoration:none; background:#f0f3f5; border:1px solid #cdd4d9; padding:20px 28px; margin-bottom:10px;">
      <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:8px;">
        <span style="font-family:Arial,sans-serif; font-size:9px; font-weight:600; letter-spacing:2px; text-transform:uppercase; color:#aab4bc;">EDICIÓN #{issue_num} &middot; {label}</span>
        <span>{sent_pill}{count_html}</span>
      </div>
      <div style="font-family:Georgia,serif; font-size:17px; font-weight:700; color:#1a1a1a; line-height:1.35;">{headline or "Ver edición &rarr;"}</div>
    </a>"""

    # ── Build search index ────────────────────
    # CHANGE: search index now includes both ES and EN text
    # so users can search in either language
    search_index = []
    for d in digest_data:
        digest_path = os.path.join(DIGEST_DIR, f"{d['date']}.json")
        if not os.path.exists(digest_path):
            continue
        with open(digest_path, encoding="utf-8") as f:
            data = json.load(f)

        digest_obj = data.get("digest", {})
        digest_es  = digest_obj.get("es", digest_obj)
        digest_en  = digest_obj.get("en", {})

        stories_es = digest_es.get("stories", [])
        stories_en = digest_en.get("stories", [])

        text_parts = [
            digest_es.get("editor_note", ""),
            digest_en.get("editor_note", ""),
            d["headline"],
        ]
        for s in stories_es:
            text_parts += [s.get("headline",""), s.get("body",""), s.get("source",""), s.get("tag","")]
        for s in stories_en:
            text_parts += [s.get("headline",""), s.get("body","")]

        search_index.append({
            "date":     d["date"],
            "filename": f"{d['date']}.html",
            "text":     " ".join(text_parts).lower(),
            "label":    d["label_en"],
        })

    search_index_js = json.dumps(search_index)

    # ── Chart JS data ─────────────────────────
    dates_js    = json.dumps(chart_dates)
    position_js = json.dumps(chart_position)
    stories_js  = json.dumps(chart_stories)
    colors_js   = json.dumps(point_colors)

    charts_html = ""
    if digest_data:
        charts_html = f"""
  <div style="background:#f0f3f5; border:1px solid #cdd4d9; padding:28px 32px; margin-bottom:24px;">

    <p style="font-family:Arial,sans-serif; font-size:9px; font-weight:700; letter-spacing:2.5px; text-transform:uppercase; color:#aab4bc; margin-bottom:16px;">Línea de Sentimiento</p>
    <div style="position:relative; height:120px; margin-bottom:28px;">
      <canvas id="sentimentChart"></canvas>
    </div>

    <div style="height:1px; background:#dde3e8; margin-bottom:24px;"></div>

    <p style="font-family:Arial,sans-serif; font-size:9px; font-weight:700; letter-spacing:2.5px; text-transform:uppercase; color:#aab4bc; margin-bottom:16px;">Notas por Edición</p>
    <div style="position:relative; height:80px;">
      <canvas id="storyChart"></canvas>
    </div>

  </div>

  <script>
    const dates    = {dates_js};
    const position = {position_js};
    const stories  = {stories_js};
    const colors   = {colors_js};

    new Chart(document.getElementById('sentimentChart'), {{
      type: 'line',
      data: {{
        labels: dates,
        datasets: [{{
          data: position,
          borderColor: '#3a4a54',
          borderWidth: 1.5,
          pointBackgroundColor: colors,
          pointBorderColor: colors,
          pointRadius: 5,
          pointHoverRadius: 7,
          fill: false,
          tension: 0.3,
        }}]
      }},
      options: {{
        responsive: true,
        maintainAspectRatio: false,
        plugins: {{
          legend: {{ display: false }},
          tooltip: {{
            callbacks: {{
              label: (ctx) => {{
                const i = ctx.dataIndex;
                const labels = {json.dumps(chart_labels)};
                return labels[i] + ' (' + ctx.raw + ')';
              }}
            }}
          }}
        }},
        scales: {{
          x: {{ ticks: {{ font: {{ size: 9 }}, color: '#aab4bc', maxTicksLimit: 10 }}, grid: {{ color: '#e8edf0' }} }},
          y: {{
            min: 0, max: 100,
            ticks: {{
              font: {{ size: 9 }}, color: '#aab4bc',
              callback: (v) => v === 5 ? 'Aversión' : v === 50 ? 'Neutral' : v === 95 ? 'Apetito' : '',
              stepSize: 45,
            }},
            grid: {{ color: '#e8edf0' }}
          }}
        }}
      }}
    }});

    new Chart(document.getElementById('storyChart'), {{
      type: 'bar',
      data: {{
        labels: dates,
        datasets: [{{ data: stories, backgroundColor: '#c8d4da', borderRadius: 2 }}]
      }},
      options: {{
        responsive: true,
        maintainAspectRatio: false,
        plugins: {{ legend: {{ display: false }}, tooltip: {{ callbacks: {{ label: (ctx) => ctx.raw + ' notas' }} }} }},
        scales: {{
          x: {{ ticks: {{ font: {{ size: 9 }}, color: '#aab4bc', maxTicksLimit: 10 }}, grid: {{ display: false }} }},
          y: {{ ticks: {{ font: {{ size: 9 }}, color: '#aab4bc', stepSize: 1 }}, grid: {{ color: '#e8edf0' }} }}
        }}
      }}
    }});
  </script>"""

    index_html = f"""<!DOCTYPE html>
<html lang="es">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{NEWSLETTER_NAME} — Archivo</title>
  <link href="https://fonts.googleapis.com/css2?family=Playfair+Display:wght@700&family=DM+Sans:wght@400;500&display=swap" rel="stylesheet">
  <script src="https://cdnjs.cloudflare.com/ajax/libs/Chart.js/4.4.1/chart.umd.min.js"></script>
  <style>
    * {{ margin:0; padding:0; box-sizing:border-box; }}
    body {{ background:#dde3e8; font-family:'DM Sans',sans-serif; padding:40px 16px; }}
    .wrap {{ max-width:640px; margin:0 auto; }}
    .masthead {{ background:#1a1a1a; padding:32px 36px; margin-bottom:24px; display:flex; justify-content:space-between; align-items:flex-end; }}
    .masthead-name {{ font-family:'Playfair Display',serif; font-size:28px; color:#f5f2ed; margin-bottom:4px; }}
    .masthead-sub {{ font-size:10px; letter-spacing:2px; text-transform:uppercase; color:#555; }}
    .masthead-count {{ font-size:11px; color:#444; letter-spacing:1px; text-align:right; }}
    a {{ color:inherit; }}
    .search-wrap {{ position:relative; margin-bottom:16px; }}
    .search-input {{
      width:100%; padding:12px 40px 12px 16px;
      background:#f0f3f5; border:1px solid #cdd4d9;
      font-family:'DM Sans',sans-serif; font-size:13px; color:#1a1a1a;
      outline:none; box-sizing:border-box;
    }}
    .search-input:focus {{ border-color:#3a4a54; }}
    .search-input::placeholder {{ color:#aab4bc; }}
    .search-clear {{
      position:absolute; right:12px; top:50%; transform:translateY(-50%);
      cursor:pointer; font-size:16px; color:#aab4bc; display:none;
      background:none; border:none; padding:0;
    }}
    .search-clear:hover {{ color:#1a1a1a; }}
    .search-count {{ font-family:Arial,sans-serif; font-size:9px; font-weight:700; letter-spacing:2px; text-transform:uppercase; color:#aab4bc; margin-bottom:14px; }}
    .no-results {{ color:#aab4bc; font-size:13px; font-style:italic; padding:20px 0; }}
    @media (max-width:600px) {{
      body {{ padding:16px 0; }}
      .wrap {{ padding:0 12px; }}
      .masthead {{ padding:24px 20px; flex-direction:column; align-items:flex-start; gap:8px; }}
    }}
  </style>
</head>
<body>
<div class="wrap">

  <div class="masthead">
    <div>
      <div class="masthead-name">{NEWSLETTER_NAME}</div>
      <div class="masthead-sub">Archivo &mdash; por {AUTHOR_NAME}</div>
    </div>
    <div class="masthead-count">{len(issues)} edición{"es" if len(issues) != 1 else ""}</div>
  </div>

  {charts_html}

  <div class="search-wrap">
    <input class="search-input" id="searchInput" type="text" placeholder="Buscar ediciones — prueba 'Banxico', 'aranceles', 'peso'...">
    <button class="search-clear" id="searchClear" onclick="clearSearch()">✕</button>
  </div>
  <div class="search-count" id="searchCount"></div>

  <p style="font-family:Arial,sans-serif; font-size:9px; font-weight:700; letter-spacing:2.5px; text-transform:uppercase; color:#aab4bc; margin-bottom:14px;" id="allIssuesLabel">Todas las Ediciones</p>

  <div id="cardsContainer">
  {cards if cards else '<p style="color:#aab4bc; font-size:13px;">No hay ediciones aún.</p>'}
  </div>

  <script>
    const searchIndex = {search_index_js};
    const input     = document.getElementById('searchInput');
    const clearBtn  = document.getElementById('searchClear');
    const container = document.getElementById('cardsContainer');
    const countEl   = document.getElementById('searchCount');
    const labelEl   = document.getElementById('allIssuesLabel');
    const allCards  = Array.from(container.querySelectorAll('a'));

    input.addEventListener('input', () => {{
      const q = input.value.trim().toLowerCase();
      clearBtn.style.display = q ? 'block' : 'none';

      if (!q) {{
        allCards.forEach(c => c.style.display = 'block');
        countEl.textContent = '';
        labelEl.textContent = 'Todas las Ediciones';
        return;
      }}

      const tokens  = q.split(/\s+/).filter(Boolean);
      const matches = searchIndex.filter(item =>
        tokens.every(t => item.text.includes(t))
      );
      const matchDates = new Set(matches.map(m => m.date));

      let shown = 0;
      allCards.forEach(card => {{
        const date = card.getAttribute('href').replace('.html','');
        if (matchDates.has(date)) {{ card.style.display = 'block'; shown++; }}
        else {{ card.style.display = 'none'; }}
      }});

      labelEl.textContent = shown > 0 ? 'Resultados' : '';
      countEl.textContent = shown > 0
        ? shown + ' resultado' + (shown !== 1 ? 's' : '') + ' para "' + input.value.trim() + '"'
        : '';

      if (shown === 0) {{
        if (!document.getElementById('noResults')) {{
          const msg = document.createElement('p');
          msg.id = 'noResults'; msg.className = 'no-results';
          msg.textContent = 'No se encontraron ediciones para "' + input.value.trim() + '"';
          container.appendChild(msg);
        }}
      }} else {{
        const msg = document.getElementById('noResults');
        if (msg) msg.remove();
      }}
    }});

    function clearSearch() {{
      input.value = '';
      input.dispatchEvent(new Event('input'));
      input.focus();
    }}
  </script>

</div>
</body>
</html>"""

    index_path = os.path.join(ARCHIVE_DIR, "index.html")
    with open(index_path, "w", encoding="utf-8") as f:
        f.write(index_html)

    print(f"  [archive] Index rebuilt with {len(issues)} issue(s).")
