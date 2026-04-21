# The Opening Bell — To-Do List

Track of features to build, roughly in order of priority.

---

## In Progress

- [ ] Sentiment chart in Friday email
- [ ] **Landing page → production** — finalize newsletter name/branding, choose palette variant (warm ivory vs. archive blue-gray), add link from `docs/index.html`, wire up subscribe form to actual backend

---

## Quick Wins

- [x] **Wire image generation into main.py** — `generate_hero_image()` in `bot/image_gen.py` calls `lib/image_generator.py`, saves PNG to `docs/images/`, sets `visual["hero_image"]` for the archive renderer.
- [ ] **RSS/Atom feed** — generate `docs/feed.xml` after each run from the digest JSON. One more distribution channel; enables RSS readers and feed aggregators.
- [ ] **Sector tags per story** — have Claude classify each story by sector (energy, banking, FX, macro, politics) as part of the summarizer JSON response. Enables archive filtering and sets up personalization later. *(do after image gen + RSS)*
- [ ] **Health monitoring** — free Healthchecks.io ping at the end of each run. If the bot doesn't check in, you get an email alert. Catches silent failures.
- [ ] **Merge Dev-Nigg → main** — all features built since March 2026 are still on Dev-Nigg. Production runs old code.
- [ ] **Global content expansion** — expand `NEWS_DOMAINS` and `TOPICS` in `config.py` beyond Spanish LatAm press to include English-language European and Asian sources, in line with the global scope pivot.

---

## Bigger Lift

- [ ] **Market sections** — wire the focus selector on the landing page to a subscription backend; route per-section digest content to subscribers based on their preferences. Foundation UI already built in `docs/landing*.html`.
- [ ] **Unsubscribe links** — each subscriber gets a unique token. Unsubscribe link removes them from the list automatically.
- [ ] **Resend/Mailgun migration** — replace Gmail SMTP with a proper email service for better deliverability and open/click tracking. Needed if subscriber list grows beyond ~20.
- [ ] **PWA + swipe navigation** — mobile reading experience on the archive site. Add to home screen, offline support, swipe between issues.

---

## Ideas / Someday

- [ ] Regulation watch section (DOF/SAT publications)
- [ ] Telegram or WhatsApp delivery option alongside email
- [ ] Subscriber growth / Substack integration
- [ ] Multi-language expansion beyond ES/EN (PT for Brazil coverage)

---

## Done

- [x] Image generation deduplication subsystem — `lib/` + `scripts/generate_editorial_image.py`; phash two-phase rejection, concept tagging, 0–3 escalation, SQLite attempt tracking, full CLI
- [x] Image prompt registry + anti-repetition system — `config/image_prompt_registry.yaml` + `lib/image_registry.py`; history-aware (concept_tag x subject_family x composition_preset) combo scoring, excluded_combos retry rotation, auto-novelty directives, `--subject-family` / `--composition-preset` / `--list-registry-options` CLI flags
- [x] Core bot — fetch, summarize, send email
- [x] Gmail-safe email renderer (tables, inline styles)
- [x] Global macro ticker bar (DXY, 10Y UST, VIX, MSCI EM)
- [x] Secondary market data strips (Global Equities, Commodities, Crypto)
- [x] Weather block removed (replaced by secondary market data)
- [x] Sentiment pills + gauge
- [x] Currency table with base toggle (MXN, USD, BRL, EUR, CNY)
- [x] Quote of the day
- [x] Friday week-in-review timeline
- [x] "This week in markets" stat block (Fridays — weekly % moves for macro indicators)
- [x] Economic calendar block (Banxico, Fed, INEGI CPI, BLS CPI through Dec 2026)
- [x] Word cloud (Fridays — generated from week's headlines)
- [x] Pretty HTML archive renderer (Google Fonts, gauge, bilingual toggle)
- [x] Archive index with sentiment timeline chart and full-text search
- [x] Sentiment timeline + stories-per-issue charts on archive index
- [x] Full-text search on archive index (client-side, no Lunr.js needed)
- [x] GitHub Actions automatic daily runs
- [x] GitHub Pages archive site
- [x] Auto-commit archive after each run
- [x] Secrets via environment variables (never committed)
- [x] Domain allowlist (NewsAPI) + domain blocklist (fetcher)
- [x] Cross-day URL deduplication (skips stories already covered in last 5 issues)
- [x] Scraper domain selectors (per-outlet CSS selectors to target article body)
- [x] Parallel market data fetching (ThreadPoolExecutor)
- [x] Code audit — bugs, efficiency, and quality pass across all bot/ files
- [x] VPS migration — pipeline runs on VPS cron; GitHub Actions retained for dev/test only
- [x] SMTP migration — replaced SMTP_SSL (port 465) with SMTP + STARTTLS (port 587); VPS port 465 was blocked
- [x] Delivery logging — normalized `[delivery]` log prefixes with connection phase visibility (connecting → authenticated → sent)
- [x] DEV/PROD environment separation — `ENVIRONMENT=dev` overrides recipients to `DEV_RECIPIENT`; Telegram notifications prefixed `[DEV]`
- [x] Newsletter landing page — `docs/landing-v1-warm.html` (warm ivory/amber) and `docs/landing-v2-archive.html` (cool blue-gray matching archive palette); both feature scrolling global ticker, interactive market focus selector (6 regions), sample issue frame, branding config object for easy renaming
