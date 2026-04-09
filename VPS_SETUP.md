# VPS Setup & Operations Guide
## The Opening Bell — Mexico Finance Brief

> **Audience:** Developers and operators who need to recreate, maintain, or debug the newsletter
> system running on a VPS with Cloudflare Tunnel.

---

## 1. System Overview

### Architecture

```
┌──────────────┐    ┌─────────────────────────────────────────────┐
│   Internet   │    │                 VPS (Ubuntu)                 │
│              │    │                                              │
│  Readers  ───┼────┼── Cloudflare Tunnel ── nginx ── docs/       │
│  Browser     │    │         (cloudflared)    :80                 │
│              │    │                                              │
│  Telegram ───┼────┼── telegram_handler.py                        │
│  Editor      │    │   (polled every 5 min via cron)              │
│              │    │                                              │
│  NewsAPI     │    │  ┌──────────────────────────────────────┐   │
│  Anthropic ──┼────┼──│ main.py (cron Mon-Fri ~7 AM CDMX)   │   │
│  Yahoo Fin.  │    │  │  1. Fetch market data                │   │
│  Gmail SMTP  │    │  │  2. Fetch news (NewsAPI)             │   │
│              │    │  │  3. Summarize (Claude API)           │   │
│              │    │  │  4. Render email + archive HTML      │   │
│              │    │  │  5. Send email (Gmail SMTP)          │   │
│              │    │  │  6. Publish docs/ → nginx root       │   │
│              │    │  │  7. Generate image candidates        │   │
│              │    │  └──────────────────────────────────────┘   │
└──────────────┘    └─────────────────────────────────────────────┘
```

### Key Components

| Component | Responsibility |
|-----------|---------------|
| `main.py` | Orchestrates the full daily pipeline |
| `generate_candidates.py` | Generates AI hero image candidates, sends to Telegram |
| `telegram_handler.py` | Polls Telegram for editorial callbacks (select/regenerate/skip) |
| `publish_site.py` | Syncs `docs/` → nginx web root via `rsync` |
| `nginx` | Serves static HTML at port 80 |
| `cloudflared` | Exposes nginx to the internet via Cloudflare Tunnel |
| `cron` | Schedules pipeline + polling |

### Directory Structure (VPS)

```
/home/adrian/project/           # Git repo root
├── bot/                        # Python source
│   ├── main.py
│   ├── generate_candidates.py
│   ├── telegram_handler.py
│   ├── publish_site.py
│   └── .env                    # Secrets (never committed)
├── docs/                       # Static HTML (GitHub source of truth)
│   ├── index.html              # Archive index (auto-rebuilt)
│   ├── YYYY-MM-DD.html         # One page per issue
│   └── images/                 # Hero images (selected from candidates)
├── digests/                    # Raw JSON per run
│   └── YYYY-MM-DD.json
└── tmp_images/                 # Temporary candidate images (pre-selection)
    └── YYYY-MM-DD/
        ├── r1_opt1.png
        ├── r1_opt2.png
        └── r1_opt3.png

/var/www/newsletter/            # nginx document root (rsync target)
└── (mirror of docs/)

/etc/cloudflared/
└── config.yml                  # Cloudflare Tunnel config (system-wide)
```

---

## 2. Pipeline Flow

### `main.py` — Daily Newsletter (runs ~7 AM CDMX)

```
start
  │
  ├─ [guard] digest already exists today? → SKIP (unless FORCE_RUN=true)
  │
  ├─ [1/5] Fetch market data (tickers, currency, weather) — parallel threads
  ├─ [2/5] Fetch news articles (NewsAPI, domain allowlist, dedup last 5 days)
  ├─ [2.5] Score and rank articles (SOURCE_TIERS, recency, length)
  ├─ [3/5] Summarize via Claude API → structured bilingual JSON
  ├─ [4/5] Render email HTML + plain text; render archive HTML
  ├─ [5/5] Send email via Gmail SMTP
  │
  ├─ Save digest JSON → digests/YYYY-MM-DD.json
  ├─ Save archive HTML → docs/YYYY-MM-DD.html
  ├─ Rebuild docs/index.html
  ├─ rsync docs/ → /var/www/newsletter/   (via publish_site.py)
  │
  └─ Kick off generate_candidates.py (hero image generation)
```

**Duplicate-run guard:**

```python
# main.py
if os.path.exists(_digest_path) and not _force_run:
    print(f"[SKIP] Digest already exists for {today_str}")
    return
```

Override with `FORCE_RUN=true` env var.

---

### `generate_candidates.py` — Image Candidates

Reads today's digest, calls the OpenAI Images API 3 times (opt1/opt2/opt3), saves PNGs to
`tmp_images/YYYY-MM-DD/r{round}_{opt}.png`, then sends photos + inline keyboard to Telegram.

**Idempotent:** exits cleanly if candidates already exist on disk for the current round.

---

### `telegram_handler.py` — Editorial Callbacks

Polls `getUpdates` once per cron tick. Handles three callback types:

| Callback data | Action |
|---------------|--------|
| `select\|YYYY-MM-DD\|optN` | Copy selected PNG → `docs/images/`, update digest, rerender, rsync |
| `regenerate\|YYYY-MM-DD` | Generate new round of candidates (max 2 regenerations) |
| `skip\|YYYY-MM-DD` | No-op acknowledgement |

Offset is persisted to `bot/.telegram_offset` so updates are never reprocessed.

**Conflict protection:** Uses `fcntl.flock` to prevent overlapping cron invocations.

---

### `publish_site.py` — Site Sync

```python
rsync -a --delete docs/ $PUBLISH_WEB_ROOT
```

Called automatically after hero selection and after the main pipeline run.
Skips silently if `PUBLISH_WEB_ROOT` is not set.

---

## 3. Environment Setup

### VPS Specs

- **OS:** Ubuntu (22.04 LTS recommended)
- **Project path:** `/home/adrian/project/`
- **Python:** 3.11+
- **nginx:** serves from `/var/www/newsletter/`

### Python Virtual Environment

```bash
# Create (one-time)
cd /home/adrian/project
python3 -m venv venv

# Activate (required before running any bot script)
source /home/adrian/project/venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

> **Always activate the venv before running any script.** Cron entries must use the
> absolute venv Python path (see §4).

### `.env` File (`bot/.env`)

Never committed. Contains all runtime secrets:

```ini
# NewsAPI
NEWS_API_KEY=your_newsapi_key

# Anthropic Claude
ANTHROPIC_API_KEY=sk-ant-...

# Email delivery
EMAIL_SENDER=your@gmail.com
EMAIL_PASSWORD=your_app_password   # Gmail App Password, not account password
SUBSCRIBERS=you@gmail.com,friend@example.com

# Telegram editorial bot
TELEGRAM_TOKEN=bot123456:ABC...
TELEGRAM_CHAT_ID=-100123456789     # Group or channel chat ID

# VPS publishing
PUBLISH_WEB_ROOT=/var/www/newsletter
PUBLIC_ARCHIVE_BASE_URL=https://newsletter.mustardhq.dev

# Pipeline flags
SKIP_EMAIL=false          # true = skip SMTP, render only
FORCE_RUN=false           # true = override duplicate-run guard
MOCK=false                # true = skip NewsAPI + Anthropic, use saved digest

# OpenAI (image generation)
OPENAI_API_KEY=sk-...
```

---

## 4. Cron Configuration

All times below are **UTC**. Mexico City (CDMX) is UTC-6 (CST) or UTC-5 (CDT, summer).

```cron
# Edit with: crontab -e
# Verify current entries: crontab -l

# ── Main pipeline — Mon-Fri at 13:30 UTC (7:30 AM CDMX CST) ──
30 13 * * 1-5  /home/adrian/project/venv/bin/python /home/adrian/project/bot/main.py >> /home/adrian/logs/newsletter.log 2>&1

# ── Telegram handler — every 5 minutes ──
*/5 * * * *    /home/adrian/project/venv/bin/python /home/adrian/project/bot/telegram_handler.py >> /home/adrian/logs/telegram.log 2>&1
```

**Key cron rules:**
- Always use the **absolute path** to the venv Python binary.
- Always redirect stdout + stderr to a log file for debugging.
- Adjust UTC offset seasonally (CDT = UTC-5, so `30 12 * * 1-5` in summer).

```bash
# Create logs directory
mkdir -p /home/adrian/logs
```

---

## 5. Cloudflare Tunnel Setup

### One-Time Setup

```bash
# 1. Install cloudflared
curl -L --output cloudflared.deb \
  https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64.deb
sudo dpkg -i cloudflared.deb

# 2. Authenticate (opens browser)
cloudflared tunnel login

# 3. Create the tunnel (generates a UUID)
cloudflared tunnel create newsletter

# Output: Tunnel credentials written to ~/.cloudflared/<UUID>.json
# Note the UUID — you'll need it everywhere.

# 4. Route DNS (creates the CNAME in Cloudflare dashboard automatically)
cloudflared tunnel route dns newsletter newsletter.mustardhq.dev
```

### `/etc/cloudflared/config.yml`

```yaml
tunnel: <UUID-from-step-3>
credentials-file: /home/adrian/.cloudflared/<UUID-from-step-3>.json

ingress:
  - hostname: newsletter.mustardhq.dev
    service: http://127.0.0.1:80
    originRequest:
      httpHostHeader: newsletter.mustardhq.dev
  - service: http_status:404
```

> **`httpHostHeader`** must match nginx's `server_name`. Without it, nginx may return 404
> because the `Host` header cloudflared sends won't match any virtual host.

### Install as systemd Service

```bash
# Install using the config above
sudo cloudflared service install

# Start and verify
sudo systemctl start cloudflared
sudo systemctl enable cloudflared
sudo systemctl status cloudflared
```

### Validate Config

```bash
cloudflared tunnel ingress validate
cloudflared tunnel ingress rule https://newsletter.mustardhq.dev
```

---

## 6. DNS Configuration

### Correct Setup

The DNS record for `newsletter.mustardhq.dev` **must** be:

| Type | Name | Value |
|------|------|-------|
| CNAME | `newsletter` | `<UUID>.cfargotunnel.com` |

> **Always create this record via CLI**, not the Cloudflare dashboard:
> ```bash
> cloudflared tunnel route dns newsletter newsletter.mustardhq.dev
> ```
> Manual dashboard entries risk pointing to the wrong UUID.

### Bug Encountered: UUID Mismatch

During setup we hit two distinct Cloudflare errors caused by DNS/tunnel mismatches:

| Error | Meaning | Root Cause |
|-------|---------|------------|
| **502 Bad Gateway** | Tunnel reached, but origin refused connection | nginx not listening or wrong port in `config.yml` |
| **530** | Cloudflare can't reach the origin | DNS CNAME pointing to wrong/nonexistent tunnel UUID |
| **1033** | Argo Tunnel error | Hostname not linked to an active tunnel — CNAME UUID doesn't match running tunnel |

**Key insight:** A tunnel showing **"Healthy"** in the Cloudflare dashboard only proves the
**outbound control channel** is alive. It does NOT prove that traffic is being proxied to nginx.
If no logs appear in `cloudflared` when you make a request → the request is not reaching the
tunnel at all → this is a **DNS problem**, not a tunnel problem.

**Diagnostic flow:**

```bash
# 1. Verify nginx is up and responsive locally
curl -I http://localhost:80

# 2. Check DNS is pointing to the right tunnel UUID
dig newsletter.mustardhq.dev CNAME

# 3. Check cloudflared can route the hostname
cloudflared tunnel ingress rule https://newsletter.mustardhq.dev

# 4. Quick end-to-end test (bypasses Cloudflare entirely)
curl -I https://newsletter.mustardhq.dev

# 5. Watch cloudflared logs in real time while making a request
sudo journalctl -u cloudflared -f
```

---

## 7. nginx Configuration

```nginx
# /etc/nginx/sites-available/newsletter
server {
    listen 80;
    server_name newsletter.mustardhq.dev;

    root /var/www/newsletter;
    index index.html;

    location / {
        try_files $uri $uri/ =404;
    }
}
```

```bash
# Enable and reload
sudo ln -s /etc/nginx/sites-available/newsletter /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

> SSL is handled by **Cloudflare** (Full or Flexible mode). nginx only needs to serve HTTP
> on port 80; Cloudflare terminates HTTPS.

---

## 8. Execution & Testing

### Run Pipeline Manually

```bash
source /home/adrian/project/venv/bin/activate
cd /home/adrian/project/bot
python main.py
```

### Force a Re-run (skip duplicate guard)

```bash
FORCE_RUN=true python main.py
```

### Dry Run (no email, no API calls)

```bash
MOCK=true SKIP_EMAIL=true python main.py
```

### Test Telegram Handler Manually

```bash
python telegram_handler.py
```

### Regenerate Archive Index Only

```bash
python -c "from archive import rebuild_index; rebuild_index()"
```

### Sync docs/ to nginx Manually

```bash
rsync -a --delete /home/adrian/project/docs/ /var/www/newsletter/
```

### Check Logs

```bash
# Main pipeline
tail -f /home/adrian/logs/newsletter.log

# Telegram handler
tail -f /home/adrian/logs/telegram.log

# cloudflared (systemd)
sudo journalctl -u cloudflared -f

# nginx access
sudo tail -f /var/log/nginx/access.log

# nginx errors
sudo tail -f /var/log/nginx/error.log
```

---

## 9. Debugging Lessons

### Cloudflare Tunnel — Control Plane vs Data Plane

> **"Tunnel Healthy" ≠ "Traffic is reaching nginx"**

The Cloudflare dashboard shows the **control plane** status (the persistent WebSocket connection
cloudflared maintains to Cloudflare's edge). This can be healthy while the **data plane** (actual
HTTP proxying to `localhost:80`) is completely broken.

**How to distinguish:**
1. Make a real request to your public URL
2. Watch `sudo journalctl -u cloudflared -f` in real time
3. If **no log lines appear** → request never reached the tunnel → DNS problem
4. If log lines appear but nginx returns an error → nginx problem

### Duplicate-Run Guard

If the pipeline ran but produced bad output, delete the digest and re-run:

```bash
# Remove today's digest
rm /home/adrian/project/digests/$(date +%Y-%m-%d).json

# Re-run
FORCE_RUN=true python main.py
```

Or just use `FORCE_RUN=true` without deleting (the guard is bypassed either way).

### Telegram Polling Conflicts

`telegram_handler.py` uses `fcntl.flock` for exclusive locking. If you see:

```
[SKIP] telegram_handler already running.
```

Either a previous invocation is genuinely still running, or a stale lock exists. Check:

```bash
ps aux | grep telegram_handler
```

The lock file is `/tmp/telegram_handler.lock` — it's automatically released when the process exits.

### Python SyntaxWarning in f-strings

JavaScript regex patterns inside Python f-strings require double-escaping backslashes:

```python
# Wrong — produces SyntaxWarning: invalid escape sequence '\s'
f"q.split(/\s+/);"

# Correct — renders as /\s+/ in the output HTML
f"q.split(/\\s+/);"
```

---

## 10. Known Improvements / TODO

| Area | Improvement |
|------|------------|
| **Testing** | `TEST_MODE` flag: sandbox both email (preview only) and Telegram (dry-run) |
| **Subscribers** | PostgreSQL subscriber database with unsubscribe tokens |
| **Monitoring** | Healthchecks.io ping after successful pipeline run; alert on silence |
| **Logging** | Structured JSON logs; ship to a log aggregator |
| **Images** | Improve hero image prompt quality; add style consistency guardrails |
| **SSL** | Upgrade Cloudflare to "Full (Strict)" mode once origin cert is configured |
| **Email deliverability** | Migrate from Gmail SMTP to Resend or Mailgun at scale |
| **Substack** | Freemium launch integration (~12-month horizon) |
| **VPS hardening** | UFW firewall rules; fail2ban; non-root service user |
| **Cron observability** | Log rotation (`logrotate`) for `/home/adrian/logs/` |

---

## 11. Quick Reference

```bash
# Activate venv
source /home/adrian/project/venv/bin/activate

# Full manual run
cd /home/adrian/project/bot && python main.py

# Force re-run
FORCE_RUN=true python main.py

# Telegram handler (manual)
python telegram_handler.py

# Sync to nginx
rsync -a --delete /home/adrian/project/docs/ /var/www/newsletter/

# Rebuild archive index only
python -c "from archive import rebuild_index; rebuild_index()"

# Cloudflare tunnel status
sudo systemctl status cloudflared
cloudflared tunnel list
cloudflared tunnel ingress validate

# nginx reload
sudo nginx -t && sudo systemctl reload nginx

# Live cloudflared logs
sudo journalctl -u cloudflared -f
```
