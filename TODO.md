# Mexico Finance Brief — To-Do List

Track of features to build, roughly in order of priority.

---

## In Progress
- [ ] Nothing currently in progress

---

## Quick Wins

- [ ] **Sentiment timeline chart** — line chart on the archive index showing daily sentiment score over time, built from saved digest JSONs. Pure JavaScript, no server needed.
- [ ] **Full-text search** — search box on the archive index powered by a pre-built JSON index. Client-side with Lunr.js. Type "Banxico" and get every issue that mentioned it.
- [ ] **Health monitoring** — free Healthchecks.io ping at the end of each run. If the bot doesn't check in, you get an email alert. Catches silent failures.

---

## Medium Effort

- [ ] **Word cloud** — generated from that week's headlines every Friday, saved alongside the issue on the archive page.
- [ ] **Subscriber CSV** — replace the hardcoded `SUBSCRIBERS` env var with a `subscribers.csv` file. Add/remove people without touching code or GitHub secrets.

---

## Bigger Lift

- [ ] **VPS migration** — move off GitHub Actions to a dedicated server (e.g. Hetzner, DigitalOcean) for more control, faster runs, and no GitHub dependency.
- [ ] **PWA + swipe navigation** — mobile reading experience on the archive site. Add to home screen, offline support, swipe between issues.
- [ ] **Unsubscribe links** — each subscriber gets a unique token. Unsubscribe link removes them from the list automatically.
- [ ] **Resend/Mailgun migration** — replace Gmail SMTP with a proper email service for better deliverability and open/click tracking. Needed if subscriber list grows beyond ~20.

---

## Ideas / Someday

- [ ] Sentiment timeline chart exported as image and embedded in Friday's email
- [ ] Economic calendar block (upcoming Banxico meetings, CPI release dates)
- [ ] Regulation watch section (DOF/SAT publications)
- [ ] "This week in markets" summary stat block
- [ ] Telegram or WhatsApp delivery option alongside email

---

## Done

- [x] Core bot — fetch, summarize, send email
- [x] Gmail-safe email renderer (tables, inline styles)
- [x] Market ticker strip (USD/MXN, S&P 500, CETES, IPC BMV)
- [x] Weather block via Open-Meteo
- [x] Sentiment pills
- [x] Currency table (MXN vs USD, EUR, CAD, CNY)
- [x] Quote of the day
- [x] Friday week-in-review timeline
- [x] Pretty HTML archive renderer (Google Fonts, gauge)
- [x] GitHub Actions automatic daily runs
- [x] GitHub Pages archive site
- [x] Auto-commit archive after each run
- [x] Secrets via environment variables (never committed)
