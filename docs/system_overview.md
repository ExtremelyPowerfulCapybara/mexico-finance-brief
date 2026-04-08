# System Overview — The Periphery / Mexico Finance Brief

> **Audience:** Technical collaborators new to this system.
> **Updated:** 2026-04-07

---

## Section 1 — What the System Does

The Periphery is a fully automated newsletter pipeline that runs every weekday morning on a VPS (Virtual Private Server). It requires no manual input to produce and deliver the newsletter — but it does ask for one human decision each day: **which hero image to use**.

Every morning the system:

1. Fetches and reads the day's financial news (in Spanish, from ~14 curated outlets)
2. Sends the articles to Claude (Anthropic's AI) to write a bilingual digest — headlines, summaries, editor note, market sentiment, and a quote
3. Pulls live market data: currencies, equity indices, commodities, crypto
4. Builds two outputs: a **Gmail-compatible HTML email** sent to subscribers, and a **web archive page** added to GitHub Pages
5. Generates three candidate hero images using OpenAI's image API
6. Sends those image candidates to a **Telegram chat** for editorial selection
7. Once an image is selected via Telegram, rerenders the archive page with the image and publishes the updated site

The only required human action is **reviewing and selecting the hero image** in Telegram. Everything else is automatic.

---

## Section 2 — End-to-End Pipeline

### Step 1: `main.py` runs at 7:00 AM (cron, Mon–Fri)

This is the main pipeline. It runs as a single Python process and completes in ~3–5 minutes.

| Sub-step | What happens |
|---|---|
| Fetch market data | Yahoo Finance prices pulled in parallel: DXY, 10Y UST, VIX, MSCI EM, S&P 500, Brent, Bitcoin, and FX cross-rates |
| Fetch news | NewsAPI queried across 7 Spanish topics, filtered to allowed domains, deduplicated against the last 5 days |
| Score articles | Each article scored for freshness, source authority, and topic relevance; top 12 go to Claude |
| Summarize | Claude returns a structured bilingual JSON: stories, editor note, narrative thread, sentiment score, quote |
| Generate visual metadata | `image_gen.py` reads the lead story tag and mood, produces 3 image prompts (no actual images yet) |
| Save digest | Full JSON saved to `digests/YYYY-MM-DD.json` |
| Send email | Gmail SMTP delivers the HTML email to all subscribers (unless `SKIP_EMAIL=true`) |
| Build archive | `docs/YYYY-MM-DD.html` written; `docs/index.html` fully rebuilt |
| Telegram notification | Lightweight message sent with today's lead headline and archive link |

### Step 2: `generate_candidates.py` runs at 7:06 AM (cron, Mon–Fri)

Six minutes after `main.py`, this script picks up today's digest and generates actual images.

| Sub-step | What happens |
|---|---|
| Read digest | Loads `digests/YYYY-MM-DD.json` to retrieve the 3 prepared image prompts |
| Guard check | Exits early if hero image is already locked, or if candidates already exist on disk |
| Generate images | Calls OpenAI Images API 3 times (one per variant), saves to `tmp_images/YYYY-MM-DD/r1_opt1.png`, etc. |
| Update digest | Writes candidate paths and metadata back into the digest JSON |
| Send to Telegram | Posts a context message, then each candidate photo with a "Select N" button, then a control row with "Regenerate" and "Skip" |

### Step 3: Human interaction via Telegram

You open Telegram and see:
- A brief context card (date, lead headline, image category)
- Three candidate images, each with a **Select** button
- A final row with **Regenerate** and **Skip** buttons

Your options:
- **Select** — picks that image; the pipeline immediately copies, rerenders, and publishes
- **Regenerate** — generates a fresh set of 3 candidates (limited to 2 regenerations per issue)
- **Skip** — no image for today's issue; archive page publishes without a hero

### Step 4: `telegram_handler.py` polls every 2 minutes (cron)

This script runs on a 2-minute loop. Each time it runs, it:

1. Asks Telegram for any new button presses since the last check
2. Routes each action:

**On Select:**
- Copies the selected image file from `tmp_images/` to `docs/images/YYYY-MM-DD.png`
- Verifies the copy succeeded
- Updates the digest JSON with `hero_image = "/images/YYYY-MM-DD.png"` and `hero_selected = "optN"`
- Calls `rerender.py` to rebuild the archive page with the image embedded
- Calls `publish_site.py` to rsync `docs/` to the web root
- Deletes the non-selected tmp candidates

**On Regenerate:**
- Increments the round counter in the digest
- Generates 3 new images (new round, e.g. `r2_opt1.png`)
- Deletes previous-round tmp files
- Sends the new candidates to Telegram

**On Skip:**
- Records the skip; no image; no rerender

---

## Section 3 — Folder Structure

```
mexico-finance-brief/
├── bot/                    All Python source code
├── digests/                One JSON file per issue (YYYY-MM-DD.json)
├── docs/                   Published web archive (GitHub Pages root)
│   ├── images/             Selected hero images (YYYY-MM-DD.png) — source of truth
│   ├── index.html          Archive landing page — rebuilt every run
│   └── YYYY-MM-DD.html     One page per issue
├── tmp_images/             Candidate images awaiting selection
│   └── YYYY-MM-DD/         r1_opt1.png, r1_opt2.png, r1_opt3.png (and r2_, r3_ if regenerated)
└── logs/                   Cron output logs
    ├── main.log
    ├── candidates.log
    └── telegram_handler.log
```

**Write timing:**

| Folder | When written |
|---|---|
| `digests/` | During `main.py` (step 4) and updated by `generate_candidates.py` and `telegram_handler.py` |
| `docs/` | During `main.py` (step 6) and rerendered after image selection |
| `docs/images/` | Only after a Telegram "Select" action |
| `tmp_images/` | During `generate_candidates.py`; cleaned up after selection or regeneration |
| `logs/` | Continuously by cron |

---

## Section 4 — Key Files and Their Responsibilities

### `bot/main.py`
- **Purpose:** Entry point. Orchestrates the entire morning pipeline in sequence.
- **When it runs:** Cron job at 7:00 AM Monday–Friday.
- **Reads:** Environment variables, NewsAPI, Yahoo Finance, Anthropic Claude API.
- **Writes:** `digests/YYYY-MM-DD.json`, `docs/YYYY-MM-DD.html`, `docs/index.html`.

### `bot/generate_candidates.py`
- **Purpose:** Reads today's digest and generates 3 hero image candidates using OpenAI. Sends them to Telegram for review.
- **When it runs:** Cron job at 7:06 AM Monday–Friday (6 minutes after `main.py` to ensure the digest exists).
- **Reads:** `digests/YYYY-MM-DD.json` (specifically the `visual.hero_options` prompts).
- **Writes:** `tmp_images/YYYY-MM-DD/r1_opt*.png`, updates `digests/YYYY-MM-DD.json` with candidate paths.
- **Idempotent:** Exits cleanly if hero image already locked or candidates already exist on disk.

### `bot/telegram_handler.py`
- **Purpose:** Polls Telegram for callback actions (select / regenerate / skip) and executes the correct pipeline response.
- **When it runs:** Cron job every 2 minutes, all day.
- **Reads:** Telegram getUpdates API; `digests/YYYY-MM-DD.json`; `tmp_images/`.
- **Writes:** `docs/images/YYYY-MM-DD.png`, updates digest JSON, rerenders archive, publishes site.

### `bot/image_candidates.py`
- **Purpose:** Low-level image generation. Calls the OpenAI Images API once per prompt and saves the PNG.
- **When it runs:** Called by `generate_candidates.py` and by `telegram_handler.py` on regeneration.
- **Reads:** `OPENAI_API_KEY`, `OPENAI_IMAGE_MODEL`, `OPENAI_IMAGE_SIZE`, `OPENAI_IMAGE_QUALITY` from environment.
- **Writes:** PNG files to `tmp_images/YYYY-MM-DD/`.

### `bot/image_gen.py`
- **Purpose:** Generates the image *prompts* (not the images themselves). Reads the lead story tag and mood from the digest and builds 3 compositional variant prompts using `prompt_map.py`.
- **When it runs:** Called inside `main.py` before the digest is saved. No API calls — pure computation.
- **Reads:** Digest dict (in memory).
- **Writes:** Nothing to disk — returns a `visual` metadata dict that gets saved inside the digest JSON.

### `bot/rerender.py`
- **Purpose:** Re-renders a single archive page from its saved digest JSON. Used after image selection to embed the hero image.
- **When it runs:** Called by `telegram_handler.py` after a successful selection. Can also be run manually.
- **Reads:** `digests/YYYY-MM-DD.json`.
- **Writes:** `docs/YYYY-MM-DD.html` (overwrites).

### `bot/publish_site.py`
- **Purpose:** Syncs `docs/` to the live web root using `rsync`.
- **When it runs:** Called by `telegram_handler.py` after a successful selection and rerender.
- **Reads:** `PUBLISH_WEB_ROOT` env var, `docs/` directory.
- **Writes:** Destination directory specified by `PUBLISH_WEB_ROOT`. Skips silently if variable not set.

---

## Section 5 — Environment Variables

All secrets live in `bot/.env` on the VPS. Never commit this file.

| Variable | Required | What it does | What breaks if missing |
|---|---|---|---|
| `NEWS_API_KEY` | Yes | Authenticates to NewsAPI for article fetching | No articles fetched; run fails at step 2 |
| `ANTHROPIC_API_KEY` | Yes | Authenticates to Claude for summarization | No digest produced; run fails at step 3 |
| `EMAIL_SENDER` | Yes | Gmail address used to send the newsletter | Email delivery fails |
| `EMAIL_PASSWORD` | Yes | Gmail App Password (not your login password) | Email delivery fails |
| `SUBSCRIBERS` | Yes | Comma-separated recipient emails | No one receives the newsletter |
| `TELEGRAM_TOKEN` | Yes (for image flow) | Authenticates the Telegram bot | No Telegram messages; image flow disabled |
| `TELEGRAM_CHAT_ID` | Yes (for image flow) | Target chat/group for Telegram messages | No Telegram messages; image flow disabled |
| `OPENAI_API_KEY` | Yes (for images) | Authenticates to OpenAI Images API | Image generation fails; `generate_candidates.py` errors |
| `PUBLIC_ARCHIVE_BASE_URL` | Recommended | Base URL used to build archive links in Telegram messages | Telegram notification omits archive link |
| `PUBLISH_WEB_ROOT` | Recommended | Destination directory for rsync publish | Site not updated after image selection |
| `SKIP_EMAIL` | No | `true` skips SMTP; archive still generated | — |
| `MOCK` | No | `true` loads saved digest instead of calling NewsAPI + Claude | — |
| `FORCE_FRIDAY` | No | `true` simulates Friday mode (word cloud, week review) | — |
| `OPENAI_IMAGE_MODEL` | No | Override image model (default: `gpt-image-1`) | — |
| `OPENAI_IMAGE_SIZE` | No | Override image size (default: `1024x1024`) | — |
| `OPENAI_IMAGE_QUALITY` | No | Override image quality (default: `medium`) | — |

---

## Section 6 — Cron Jobs

Add these to `crontab -e` on the VPS. All times are Mexico City (CST/CDT).

```cron
CRON_TZ=America/Mexico_City

# Morning pipeline — runs the full newsletter and saves the digest
0 7 * * 1-5 cd /home/adrian/project/bot && /home/adrian/project/venv/bin/python main.py >> /home/adrian/project/logs/main.log 2>&1

# Image candidate generation — runs 6 minutes after main.py to ensure the digest exists
6 7 * * 1-5 cd /home/adrian/project/bot && /home/adrian/project/venv/bin/python generate_candidates.py >> /home/adrian/project/logs/candidates.log 2>&1

# Telegram handler — polls for button presses continuously throughout the day
*/2 * * * * cd /home/adrian/project/bot && /home/adrian/project/venv/bin/python telegram_handler.py >> /home/adrian/project/logs/telegram_handler.log 2>&1
```

**Why ordering matters:**

- `generate_candidates.py` must run *after* `main.py` because it reads the digest that `main.py` writes. The 6-minute gap is a conservative buffer for `main.py` to complete.
- `telegram_handler.py` runs every 2 minutes around the clock. It is stateless between runs (it persists its Telegram offset to `bot/.telegram_offset`). The handler is safe to run before images exist — it will simply find no pending updates.

**What happens if one fails:**

| Failure | Effect | Recovery |
|---|---|---|
| `main.py` fails | No digest, no email, no candidates | Check `logs/main.log`; fix the issue; re-run manually |
| `generate_candidates.py` fails | No images sent to Telegram today | Re-run manually after fixing; it's idempotent — safe to re-run |
| `telegram_handler.py` fails one cycle | Missed one 2-minute window | Next cycle picks up pending updates via offset; usually self-healing |

---

## Section 7 — Daily Operation Guide

### What to do every morning

1. **Check Telegram** around 7:15 AM. You should see:
   - A context card with the date, lead headline, and image category
   - Three candidate images with "Select 1", "Select 2", "Select 3" buttons
   - A row with "Regenerate" and "Skip" buttons

2. **Review the images.** Read the lead headline. Pick the image that best matches the story's tone.

3. **Tap the Select button** under your preferred image. You should see a confirmation toast ("Saved: opt1" or similar). The site will update within seconds.

That's it. The newsletter was already sent to subscribers at 7:00 AM.

### When to use Regenerate

Use Regenerate when:
- None of the three images feel right for the story
- The images are too generic or miss the tone entirely
- You want a different compositional approach

You have up to **2 regenerations** per issue. After that, the Regenerate button stops working and you must either select from the current batch or Skip.

### When to use Skip

Use Skip when:
- You don't have time to review today
- None of the images are acceptable and you're out of regenerations
- The story topic doesn't suit a hero image

Skipping means the archive page publishes without a hero image. That's fine — the page still looks correct.

---

## Section 8 — Debugging Guide

### No Telegram message received

**Where to look:** `logs/candidates.log`

**Likely causes:**
- `main.py` failed before saving the digest (check `logs/main.log`)
- `TELEGRAM_TOKEN` or `TELEGRAM_CHAT_ID` not set in `bot/.env`
- OpenAI API call failed during image generation

**Quick fix:** Check the log, fix the issue, then re-run:
```bash
cd /home/adrian/project/bot && python generate_candidates.py
```

### Images not generated (no photos in Telegram)

**Where to look:** `logs/candidates.log`

**Likely causes:**
- `OPENAI_API_KEY` missing or invalid
- OpenAI rate limit hit
- No `hero_options` in today's digest (means `main.py` failed or produced a malformed digest)

**Quick fix:**
1. Check `logs/candidates.log` for the specific error
2. Verify the digest exists: `ls digests/$(date +%F).json`
3. Check that `hero_options` are present: `python -c "import json; d=json.load(open('digests/$(date +%F).json')); print(d.get('visual',{}).get('hero_options'))"`

### Selection not updating (nothing happens after tapping Select)

**Where to look:** `logs/telegram_handler.log`

**Likely causes:**
- `telegram_handler.py` cron not running (check with `crontab -l`)
- `PUBLISH_WEB_ROOT` not set (rsync skipped silently)
- Candidate file missing from `tmp_images/` (was deleted prematurely)

**Quick fix:**
1. Confirm cron is active: `crontab -l | grep telegram`
2. Run the handler manually to see live output: `cd /home/adrian/project/bot && python telegram_handler.py`

### Image not visible on the published site

**Where to look:** `docs/images/`, then the rendered HTML

**Likely causes:**
- Selection succeeded but `publish_site.py` failed (rsync error)
- `PUBLISH_WEB_ROOT` not configured
- `docs/images/YYYY-MM-DD.png` exists but the HTML path is wrong

**Quick fix:**
1. Check `docs/images/` for the PNG: `ls docs/images/`
2. Check the digest for `hero_image` value: `python -c "import json; d=json.load(open('digests/$(date +%F).json')); print(d.get('visual',{}).get('hero_image'))"`
3. Manually publish: `cd /home/adrian/project/bot && python publish_site.py`
4. Manually rerender if needed: `cd /home/adrian/project/bot && python rerender.py $(date +%F)`

---

## Section 9 — Design Decisions

**Why are images generated separately from `main.py`?**
Image generation takes ~30–60 seconds per image (3 per run = 90–180 seconds). Blocking the morning pipeline on this would delay email delivery. Separating it into `generate_candidates.py` keeps the main run fast and the image step independently retriable.

**Why Telegram for image selection?**
It's the lowest-friction editorial interface for a small team. No web dashboard to build or maintain. Button callbacks work on mobile. The bot token + chat ID are the only infrastructure required.

**Why `tmp_images/` vs `docs/images/`?**
Candidates are temporary — most will be discarded. Only the selected image earns a permanent home in `docs/images/`. This keeps the published directory clean and avoids serving rejected images over the web.

**Why rsync for publishing?**
The VPS serves the site directly from `PUBLISH_WEB_ROOT`. rsync with `--delete` ensures the destination exactly mirrors `docs/` — new files are added, removed files are deleted, unchanged files are skipped. It's atomic enough for a low-traffic newsletter and requires no web framework.

---

## Section 10 — Safety and Invariants

| Rule | Reason |
|---|---|
| `hero_image` in the digest is a lock | Once set, `generate_candidates.py` and `telegram_handler.py` exit immediately without changes. Do not clear it manually unless you intend to re-run the image flow. |
| Do not edit digest JSON while `telegram_handler.py` is polling | The handler reads and writes the same file. Concurrent edits can corrupt the JSON. Stop cron or wait until the handler is idle. |
| `tmp_images/` can be safely deleted | These are intermediate files only. If deleted after selection, nothing breaks (the selected image is already in `docs/images/`). If deleted before selection, you will need to re-run `generate_candidates.py`. |
| `docs/images/` is the source of truth for published images | The archive HTML references `/images/YYYY-MM-DD.png`. Do not rename or move files here without also updating the digest and rerendering the archive page. |
| Do not delete files from `digests/` | The archive index (`docs/index.html`) is rebuilt from all digest files on every run. Deleting a digest removes it from the historical record permanently. |
| `docs/index.html` is auto-generated | It is overwritten on every run. Any manual edits will be lost at the next run. |
