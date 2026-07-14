# 🍪 Cookie Setup Guide

## Required Format: **JSON only**

This bot uses **Playwright** under the hood, and Playwright's `context.add_cookies()` method expects cookies as a **JSON list** — one entry per cookie, with `name`, `value`, `domain`, `path`, etc.

Other formats (Netscape `.txt`, header strings) **will not work** without conversion.

---

## Why JSON?

| Format | Works? | Why |
|--------|--------|-----|
| **JSON** (Cookie-Editor default) | ✅ Yes | Native format for Playwright; structure preserved |
| Netscape `.txt` | ❌ No | Designed for `curl`/`wget`; lacks domain/path metadata |
| Header string (`k=v; k=v`) | ❌ No | No domain/path/expiry info; Playwright rejects |

---

## Step-by-step: Export → Encode → Add as Secret

### Step 1 — Install Cookie-Editor extension

- **Chrome / Edge:** https://chrome.google.com/webstore/detail/cookie-editor/hlkenndednhfkekhgcdicdfddnkalmdm
- **Firefox:** https://addons.mozilla.org/en-US/firefox/addon/cookie-editor/

### Step 2 — Log in to each platform

Open the platform site in your browser and log in normally.
Verify you can see your dashboard.

### Step 3 — Export as JSON

1. Click the Cookie-Editor icon in your browser toolbar
2. Click **Export** → **Export as JSON**
3. The JSON will be copied to your clipboard (or downloaded as a file)

The exported content will look like:

```json
[
  {
    "name": "session_id",
    "value": "abc123def456...",
    "domain": ".sproutgigs.com",
    "path": "/",
    "expirationDate": 1735689600,
    "httpOnly": true,
    "secure": true,
    "sameSite": "Lax"
  },
  {
    "name": "auth_token",
    "value": "xyz789...",
    ...
  }
]
```

### Step 4 — Save the file

Save the JSON content to a file named exactly:

| Platform | Filename |
|----------|----------|
| SproutGigs | `sproutgigs_cookies.json` |
| CoinPayu | `coinpayu_cookies.json` |
| TimeBucks | `timebucks_cookies.json` |
| PrizeRebel | `prizerebel_cookies.json` |

### Step 5 — Base64-encode the file

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

### Step 6 — Add as GitHub Secret

1. Go to: https://github.com/airdropia-collection/microwork-hunter/settings/secrets/actions
2. Click **New repository secret**
3. Name: `COOKIES_SPROUTGIGS` (exactly — uppercase)
4. Value: paste the base64 string
5. Click **Add secret**

Repeat for each platform.

---

## Local Development (alternative to secrets)

For local development, you can skip the base64 encoding and just place the JSON files directly in the `cookies/` folder:

```
microwork-hunter/
└── cookies/
    ├── sproutgigs_cookies.json
    ├── coinpayu_cookies.json
    ├── timebucks_cookies.json
    └── prizerebel_cookies.json
```

The `config.py` will automatically read from these files if the corresponding environment variable is not set.

> ⚠️ The `cookies/` folder is in `.gitignore` — your local cookie files will never be committed.

---

## Verifying Cookies Work

After adding cookies, run the cookie validator locally:

```bash
BROWSER_TYPE=playwright python -m src.utils.cookie_validator --platform sproutgigs
```

Or trigger the Hunter workflow on GitHub Actions and check the "Validate Cookies" step output.

---

## Common Issues

| Issue | Fix |
|-------|-----|
| Bot reports "not logged in" | Cookie expired — re-export and re-add |
| `base64 -d` fails on GitHub Actions | Make sure you used `tr -d '\n'` to strip newlines |
| Cookie-Editor exports Netscape by default | Click the format dropdown — switch to JSON |
| `domain` field missing in JSON | Make sure you exported while ON the platform's site |
| Cookies work locally but not on Actions | Double-check secret name matches exactly (case-sensitive) |

---

## Refresh Schedule

Cookies expire. Recommended refresh cadence:

- **SproutGigs:** every 7 days
- **CoinPayu:** every 7 days
- **TimeBucks:** every 10 days
- **PrizeRebel:** every 14 days

The Hunter workflow's "Validate Cookies" step will warn you (but not block) if any platform's cookies have expired.
