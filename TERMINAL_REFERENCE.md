# Terminal Command Reference
## The Opening Bell — VPS Operations Guide

> Quick reference for operating, debugging, and maintaining the newsletter VPS.
> All commands assume you are logged in as `adrian` on the Ubuntu VPS.

---

## 1. Navigation & File Management

```bash
# Where am I?
pwd

# Go to project root
cd /home/adrian/project

# Go to bot scripts
cd /home/adrian/project/bot

# Go to web root (nginx)
cd /var/www/newsletter

# List files (with details)
ls -la

# List only .html files
ls -la docs/*.html

# Tree view (if installed)
tree /home/adrian/project --dirsfirst -L 2

# Create a directory
mkdir -p /home/adrian/logs

# Copy a file
cp docs/index.html docs/index.html.bak

# Copy a directory (recursive)
cp -r docs/ docs_backup/

# Move or rename
mv old_name.py new_name.py

# Delete a file (careful — no undo)
rm file.txt

# Delete a directory and its contents (DANGEROUS — double-check path first)
rm -rf tmp_images/2026-04-09/
```

---

## 2. File Editing

### nano — the primary editor on this VPS

```bash
# Open a file
nano /home/adrian/project/bot/.env

# Open cloudflared config
sudo nano /etc/cloudflared/config.yml

# Open nginx site config
sudo nano /etc/nginx/sites-available/newsletter
```

**nano keyboard shortcuts:**

| Action | Shortcut |
|--------|---------|
| Save | `Ctrl + O`, then `Enter` |
| Exit | `Ctrl + X` |
| Save and exit | `Ctrl + O` → `Enter` → `Ctrl + X` |
| Search | `Ctrl + W` |
| Cut line | `Ctrl + K` |
| Paste | `Ctrl + U` |

### Viewing files (read-only)

```bash
# Print entire file
cat /home/adrian/project/bot/.env

# Scroll through a long file (q to quit)
less /var/log/nginx/access.log

# First 20 lines
head -20 /home/adrian/project/digests/2026-04-09.json

# Last 20 lines
tail -20 /home/adrian/logs/newsletter.log

# Follow a file in real time (Ctrl+C to stop)
tail -f /home/adrian/logs/newsletter.log
```

---

## 3. Searching & Inspection

```bash
# Search for a string inside files
grep "ERROR" /home/adrian/logs/newsletter.log

# Case-insensitive search
grep -i "error" /home/adrian/logs/newsletter.log

# Search recursively across all .py files
grep -r "PUBLISH_WEB_ROOT" /home/adrian/project/bot/

# Show line numbers
grep -n "hero_image" /home/adrian/project/bot/telegram_handler.py

# Find files by name
find /home/adrian/project -name "*.json"

# Find recently modified files (last 24h)
find /home/adrian/project/digests -newer /home/adrian/project/digests/2026-04-08.json

# Filter command output
ps aux | grep python

# Count matching lines
grep "200" /var/log/nginx/access.log | wc -l

# Search logs for a specific date
grep "09/Apr/2026" /var/log/nginx/access.log

# Show last N errors in nginx log
grep " 50[0-9] " /var/log/nginx/access.log | tail -20
```

---

## 4. Python Environment

### Always activate the virtual environment first

```bash
source /home/adrian/project/venv/bin/activate
```

Your prompt will change to show `(venv)`. Every `python` and `pip` command after this
uses the project's isolated environment, not the system Python.

```bash
# Confirm you're using the right Python
which python
# Should output: /home/adrian/project/venv/bin/python

# Deactivate when done (optional)
deactivate
```

### Installing packages

```bash
# Install all project dependencies
pip install -r /home/adrian/project/requirements.txt

# Install a single package
pip install requests

# Check installed packages
pip list
```

### Running scripts

```bash
# Always run from the bot/ directory so relative imports work
cd /home/adrian/project/bot

# Full pipeline run
python main.py

# Force re-run even if today's digest already exists
FORCE_RUN=true python main.py

# Dry run: no API calls, no email
MOCK=true SKIP_EMAIL=true python main.py

# Skip email only (full pipeline, no SMTP)
SKIP_EMAIL=true python main.py

# Telegram handler (manual poll)
python telegram_handler.py

# Generate image candidates for a specific date
python generate_candidates.py --date 2026-04-09

# Rebuild archive index without running the full pipeline
python -c "from archive import rebuild_index; rebuild_index()"
```

---

## 5. Logs & Debugging

### Application logs

```bash
# Follow pipeline log in real time
tail -f /home/adrian/logs/newsletter.log

# Follow Telegram handler log
tail -f /home/adrian/logs/telegram.log

# Last 50 lines of pipeline log
tail -50 /home/adrian/logs/newsletter.log

# Search pipeline log for errors
grep -i "error\|exception\|traceback" /home/adrian/logs/newsletter.log
```

### nginx logs

```bash
# All incoming requests (live)
sudo tail -f /var/log/nginx/access.log

# Errors only (live)
sudo tail -f /var/log/nginx/error.log

# Find non-200 responses
grep -v " 200 " /var/log/nginx/access.log | tail -30
```

### cloudflared logs (via systemd)

```bash
# Live log stream (Ctrl+C to stop)
sudo journalctl -u cloudflared -f

# Last 100 lines
sudo journalctl -u cloudflared -n 100

# Logs since a specific time
sudo journalctl -u cloudflared --since "2026-04-09 07:00:00"
```

### Process inspection

```bash
# Is the pipeline currently running?
ps aux | grep main.py

# Is the Telegram handler running?
ps aux | grep telegram_handler

# What's using port 80?
sudo ss -tlnp | grep :80

# All Python processes
ps aux | grep python
```

---

## 6. Cloudflared / Tunnel Commands

```bash
# Check tunnel list and status
cloudflared tunnel list

# Run the tunnel manually (foreground — useful for debugging)
# Ctrl+C to stop; use systemd service for production
cloudflared tunnel run newsletter

# Validate the ingress config at /etc/cloudflared/config.yml
cloudflared tunnel ingress validate

# Check which service handles a specific URL
cloudflared tunnel ingress rule https://newsletter.mustardhq.dev

# Create or update the DNS CNAME for the tunnel
# Always use this instead of the Cloudflare dashboard — avoids UUID mismatches
cloudflared tunnel route dns newsletter newsletter.mustardhq.dev

# Check which tunnel a hostname is routed to
cloudflared tunnel route ip show
```

**When to run manually vs via systemd:**
- Use `cloudflared tunnel run newsletter` only for debugging — it runs in the foreground.
- In production, the systemd service manages it automatically. Prefer `systemctl` commands.

---

## 7. Systemd — Service Management

```bash
# Check cloudflared service status
sudo systemctl status cloudflared

# Start the service
sudo systemctl start cloudflared

# Stop the service
sudo systemctl stop cloudflared

# Restart (applies config changes)
sudo systemctl restart cloudflared

# Enable auto-start on boot
sudo systemctl enable cloudflared

# Reload nginx after config changes (no downtime)
sudo nginx -t && sudo systemctl reload nginx

# Check nginx status
sudo systemctl status nginx
```

**Pattern for config changes:**
1. Edit the config file
2. Test it: `sudo nginx -t` or `cloudflared tunnel ingress validate`
3. Apply it: `sudo systemctl reload nginx` or `sudo systemctl restart cloudflared`

---

## 8. Networking & Testing

### Local origin test (bypass Cloudflare entirely)

```bash
# Is nginx responding on port 80?
curl -I http://localhost:80

# Fetch the index page
curl -s http://localhost:80/ | head -30

# Test a specific issue page
curl -I http://localhost:80/2026-04-09.html
```

### Public URL test (goes through Cloudflare Tunnel)

```bash
# Check HTTP headers from the public URL
curl -I https://newsletter.mustardhq.dev

# Fetch the page
curl -s https://newsletter.mustardhq.dev/ | head -30

# Verbose output (shows TLS handshake, headers)
curl -v https://newsletter.mustardhq.dev 2>&1 | head -50
```

### DNS debugging

```bash
# What does the CNAME point to?
dig newsletter.mustardhq.dev CNAME

# Full DNS resolution chain
dig newsletter.mustardhq.dev +trace

# Quick A record lookup
dig newsletter.mustardhq.dev A

# Check DNS propagation (use external resolver)
dig @8.8.8.8 newsletter.mustardhq.dev
```

**Reading `dig` output:** Look for the `ANSWER SECTION`. A healthy Cloudflare Tunnel setup
shows a CNAME pointing to `<UUID>.cfargotunnel.com`.

---

## 9. Deployment / Publishing

### Sync docs/ to nginx web root

```bash
# Dry run first — shows what WOULD be changed without touching anything
rsync -a --delete --dry-run /home/adrian/project/docs/ /var/www/newsletter/

# Apply for real
rsync -a --delete /home/adrian/project/docs/ /var/www/newsletter/

# Verbose output (shows each file transferred)
rsync -av --delete /home/adrian/project/docs/ /var/www/newsletter/
```

**What these flags mean:**
- `-a` — archive mode: preserves permissions, timestamps, symlinks, recursion
- `--delete` — removes files from the destination that no longer exist in the source
- The trailing `/` on the source path is critical: it copies the **contents** of `docs/`,
  not the `docs/` directory itself into `var/www/newsletter/docs/`

**Always run `--dry-run` first** when you're unsure what will be deleted.

---

## 10. Cron Jobs

```bash
# Open cron editor (for the current user — adrian)
crontab -e

# View current cron entries without editing
crontab -l

# Check syslog for cron execution records
grep CRON /var/log/syslog | tail -20

# Filter for your specific job
grep CRON /var/log/syslog | grep "main.py"
```

### Current cron entries (reference)

```cron
# Main pipeline — Mon-Fri at 13:30 UTC (7:30 AM CDMX CST)
30 13 * * 1-5  /home/adrian/project/venv/bin/python /home/adrian/project/bot/main.py >> /home/adrian/logs/newsletter.log 2>&1

# Telegram handler — every 5 minutes
*/5 * * * *    /home/adrian/project/venv/bin/python /home/adrian/project/bot/telegram_handler.py >> /home/adrian/logs/telegram.log 2>&1
```

**Cron time format:** `minute hour day month weekday`
- `30 13 * * 1-5` = 13:30 UTC, Monday through Friday
- `*/5 * * * *` = every 5 minutes

**Seasonal note:** Mexico City switches between UTC-6 (CST) and UTC-5 (CDT). Adjust the
pipeline cron hour accordingly: `13` in winter, `12` in summer.

---

## 11. Safety Tips

### Before running destructive commands

```bash
# ALWAYS check the path you're about to delete
ls -la /home/adrian/project/tmp_images/2026-04-09/

# Then delete
rm -rf /home/adrian/project/tmp_images/2026-04-09/

# Use --dry-run before rsync with --delete
rsync -a --delete --dry-run docs/ /var/www/newsletter/
```

### Things that cannot be undone

| Command | Risk | Safer Alternative |
|---------|------|-------------------|
| `rm -rf <dir>` | Permanent deletion | `ls` the path first, then delete |
| `rsync --delete` | Deletes unmatched files at destination | `--dry-run` first |
| `crontab -e` save | Overwrites your cron table | `crontab -l` to review before editing |
| `git reset --hard` | Discards uncommitted changes | `git status` + `git stash` first |

### Other habits

```bash
# Confirm you're in the right directory before running scripts
pwd

# Confirm the venv is active before pip installs
which python

# Check nginx config before reloading
sudo nginx -t

# Check cloudflared config before restarting
cloudflared tunnel ingress validate
```

---

## Quick Cheat Sheet

```bash
# Activate venv
source /home/adrian/project/venv/bin/activate

# Run pipeline
cd /home/adrian/project/bot && python main.py

# Force re-run
FORCE_RUN=true python main.py

# Mock dry run
MOCK=true SKIP_EMAIL=true python main.py

# Sync to nginx
rsync -a --delete /home/adrian/project/docs/ /var/www/newsletter/

# Rebuild index only
python -c "from archive import rebuild_index; rebuild_index()"

# Cloudflare tunnel status
sudo systemctl status cloudflared
cloudflared tunnel list

# nginx reload
sudo nginx -t && sudo systemctl reload nginx

# Live logs
tail -f /home/adrian/logs/newsletter.log
sudo journalctl -u cloudflared -f
sudo tail -f /var/log/nginx/access.log

# DNS check
dig newsletter.mustardhq.dev CNAME

# Local origin test
curl -I http://localhost:80
```
