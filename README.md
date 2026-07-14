# 🤖 Microwork Hunter

> Zero-budget, 24/7 cloud automation for microwork platforms — runs on GitHub Actions free tier, controlled from your phone via GitHub Issues.

[![CI](https://github.com/your-username/microwork-hunter/actions/workflows/ci.yml/badge.svg)](https://github.com/your-username/microwork-hunter/actions/workflows/ci.yml)
[![Hunter](https://github.com/your-username/microwork-hunter/actions/workflows/hunter.yml/badge.svg)](https://github.com/your-username/microwork-hunter/actions/workflows/hunter.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)

---

## 📑 Table of Contents
1. [What This Does](#-what-this-does)
2. [How It Works](#-how-it-works)
3. [Supported Platforms](#-supported-platforms)
4. [Setup](#-setup)
5. [Cookie Preparation](#-how-to-prepare-cookies)
6. [Mobile Control](#-mobile-control)
7. [Free Resources Used](#-free-resources-used)
8. [Anti-Detection](#-anti-detection)
9. [Local Development](#-local-development)
10. [Project Structure](#-project-structure)
11. [Important Notes](#-important-notes)

---

## 🚀 What This Does

**Microwork Hunter** is an automated bot that hunts, executes, and reports microwork tasks across four popular platforms. It is designed to run **completely free** on GitHub Actions, scheduled every 4 hours, with **human-in-the-loop review** built in.

The bot:
- 🔍 **Discovers** new tasks from 4 platforms every 4 hours
- 🤖 **Executes** tasks in dry-run mode by default (safe)
- 📸 **Captures evidence** (screenshots, logs) for every action
- 📱 **Opens a GitHub Issue** for your review — you get a push notification
- ✅ **Submits** approved tasks automatically after your `/approve` comment
- 💰 **Tracks** earnings across all platforms and currencies

---

## 🔁 How It Works

```
Every 4 hours (GitHub Actions cron):
┌─────────────────────────────────────┐
│ 1. Start Obscura Browser (Docker)  │
│ 2. Decode cookies from secrets     │
│ 3. Validate cookies (non-blocking) │
│ 4. Discover tasks from 4 sites     │
│ 5. Rank by reward/time ratio       │
│ 6. Execute top N tasks (dry-run)   │
│ 7. Save evidence + result files    │
│ 8. Compile review package          │
│ 9. Create GitHub Issue for review  │
│ 10. Stop browser (free resources)  │
└─────────────────────────────────────┘
              ↓
       Mobile notification
              ↓
   Comment: /approve all
              ↓
   Review-bot workflow:
   1. Parse your comment
   2. Find approved tasks in package
   3. Re-execute (dry_run=false)
   4. Reply with submission status
   5. Close the issue
```

---

## 🎯 Supported Platforms

| Platform    | Task Types                          | Currency   | URL                          |
|-------------|-------------------------------------|------------|------------------------------|
| SproutGigs  | Micro Jobs, Surveys, Offers         | USD        | https://sproutgigs.com       |
| CoinPayu    | PTC Ads, Offers, Surveys            | Satoshi    | https://www.coinpayu.com     |
| TimeBucks   | Videos, Surveys, Content engagement | USD        | https://timebucks.com        |
| PrizeRebel  | Surveys, Offers, Daily Challenges   | Points     | https://www.prizerebel.com   |

---

## 🛠 Setup

### 1. Fork or clone this repo

```bash
git clone https://github.com/your-username/microwork-hunter.git
cd microwork-hunter
```

### 2. Add Required Secrets

Go to **Repo → Settings → Secrets and variables → Actions → New repository secret**:

| Secret                | Required | How to Get                                           |
|-----------------------|----------|------------------------------------------------------|
| `GEMINI_API_KEY`      | ✅ Yes   | https://aistudio.google.com/app/apikey (1M tok/day) |
| `GROQ_API_KEY`        | ❌ Optional | https://console.groq.com/ (1M tok/day fallback)  |
| `LTC_ADDRESS`         | ❌ Optional | Your Binance LTC deposit address                 |
| `COOKIES_SPROUTGIGS`  | ✅ Yes   | Base64-encoded cookies JSON (see below)            |
| `COOKIES_COINPAYU`    | ✅ Yes   | Base64-encoded cookies JSON                         |
| `COOKIES_TIMEBUCKS`   | ✅ Yes   | Base64-encoded cookies JSON                         |
| `COOKIES_PRIZEREBEL`  | ✅ Yes   | Base64-encoded cookies JSON                         |

### 3. Enable Actions

- Go to **Actions** tab → click "I understand my workflows, go ahead and enable them"
- The first scheduled run will fire at the next 4-hour mark (UTC)
- Or trigger manually: **Actions → Microwork Hunter → Run workflow**

---

## 🍪 How to Prepare Cookies

### Step 1 — Export from Browser
1. Install the **Cookie-Editor** extension (Chrome / Firefox / Edge)
2. Log in to each microwork platform in your browser
3. Click the extension icon → **Export** → **Export as JSON**
4. Save the file as e.g. `sproutgigs_cookies.json`

### Step 2 — Base64-encode

**Linux / macOS:**
```bash
base64 sproutgigs_cookies.json | tr -d '\n'
```

**Windows (PowerShell):**
```powershell
$content = Get-Content "sproutgigs_cookies.json" -Raw
$bytes   = [System.Text.Encoding]::UTF8.GetBytes($content)
[Convert]::ToBase64String($bytes) | Set-Clipboard
```

### Step 3 — Add as GitHub Secret
- Create a new repository secret
- Name: `COOKIES_SPROUTGIGS` (etc.)
- Value: paste the base64 string

> Cookies expire. Refresh them weekly — stale cookies are the #1 cause of failed runs.

---

## 📱 Mobile Control

1. Install the **GitHub mobile app** (iOS / Android)
2. Enable push notifications for the repo
3. When the bot creates a review Issue, you get a notification
4. Open the issue, review the pending tasks table
5. Comment one of:
   - `/approve all` — submit every pending task
   - `/approve <task-id> [<task-id>...]` — submit specific tasks
   - `/reject <task-id> <reason>` — reject a task
   - `/modify <task-id> <instructions>` — request re-execution with notes
6. The review-bot workflow runs, submits tasks, replies with the result, and closes the issue

---

## 🆓 Free Resources Used

| Service          | Free Tier              | Used For                       |
|------------------|------------------------|--------------------------------|
| GitHub Actions   | 2,000 min/month (free) | Automation hosting             |
| Google Gemini    | 1M tokens/day          | AI task understanding          |
| Groq             | 1M tokens/day          | AI fallback                    |
| Obscura Browser  | Open source            | Stealth browsing via Docker    |
| GitHub Issues    | Unlimited (public repo)| Human-in-the-loop review       |

> A 4-hourly run that takes ~3 minutes uses ~540 min/month — well within the free tier.

---

## 🛡 Anti-Detection

Obscura browser provides:
- Per-session fingerprint randomization
- Hidden `navigator.webdriver`
- 3,520 tracker domains blocked
- Realistic Chrome user agent
- Native function masking

The bot also uses human-like delays (2–8s) between actions to avoid triggering bot-detection heuristics.

---

## 💻 Local Development

```bash
# 1. Clone
git clone https://github.com/your-username/microwork-hunter.git
cd microwork-hunter

# 2. Create venv & install
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -e ".[dev]"
python -m playwright install chromium

# 3. Configure env
cp .env.example .env
# edit .env with your GEMINI_API_KEY and (for local dev) cookie file paths

# 4. Put cookies locally (alternative to secrets)
mkdir -p cookies
# place sproutgigs_cookies.json, coinpayu_cookies.json, etc. here

# 5. Run tests
pytest -v

# 6. Try discovery locally (Playwright fallback — no Docker needed)
BROWSER_TYPE=playwright python -m src.hunters.discover --platform sproutgigs --max-tasks 3
```

### Project Structure

```
microwork-hunter/
├── .github/workflows/
│   ├── hunter.yml          # Main 4-hourly scheduled discovery+execution
│   ├── review-bot.yml      # Responds to /approve /reject /modify comments
│   └── ci.yml              # Lint + tests on every PR
├── cookies/                # Local cookie files (gitignored)
├── src/
│   ├── browser/            # Browser abstraction (Obscura + Playwright)
│   ├── platforms/          # Per-site adapters
│   ├── hunters/            # Discovery orchestrator
│   ├── workers/            # Executor + review handler
│   └── utils/              # AI, cookies, earnings, review compiler
├── tests/                  # pytest suite
├── .env.example
├── .gitignore
├── pyproject.toml
├── requirements.txt
├── LICENSE
└── README.md
```

---

## ⚠️ Important Notes

- **Always start with `dry_run=true`** (default). The bot will not submit anything until you explicitly `/approve`.
- **Review before approving** — the human gate is mandatory by design.
- **Cookies expire** — refresh weekly. The validator step warns but does not block.
- **Respect each platform's ToS** — use at your own risk. The authors take no responsibility for account bans.
- **Start small** — set `max_tasks=2` for the first few runs to verify behavior.
- **Rotate your secrets** if you ever accidentally leak a PAT, API key, or cookie file.

---

## 🤝 Contributing

PRs welcome! Please:
1. Run `ruff check src tests` and `pytest` before submitting
2. Keep `dry_run=true` as the default for any new executor logic
3. Add tests for new utility functions

---

**Budget: $0 · Runs 24/7 · Mobile Control · Built with ❤️**
