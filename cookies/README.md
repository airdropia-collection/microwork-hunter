# 🍪 Cookie Setup Guide

## Why Cookies?
Cookies allow the bot to bypass login and directly access your account.

## How to Export

### Using Cookie-Editor Extension
1. Install from Chrome Web Store: "Cookie-Editor"
2. Login to each platform
3. Click extension icon
4. Click "Export" → "Export as JSON"
5. Save with correct name

## Required Files

| Platform | File | Secret Name |
|----------|------|-------------|
| SproutGigs | `sproutgigs_cookies.json` | `COOKIES_SPROUTGIGS` |
| CoinPayu | `coinpayu_cookies.json` | `COOKIES_COINPAYU` |
| TimeBucks | `timebucks_cookies.json` | `COOKIES_TIMEBUCKS` |
| PrizeRebel | `prizerebel_cookies.json` | `COOKIES_PRIZEREBEL` |

## Base64 Encode for GitHub Secrets

### Windows PowerShell:
```powershell
$content = Get-Content "sproutgigs_cookies.json" -Raw
$bytes = [System.Text.Encoding]::UTF8.GetBytes($content)
$base64 = [Convert]::ToBase64String($bytes)
$base64 | Set-Clipboard  # Copied to clipboard!
```

### Linux/Mac:
```bash
base64 sproutgigs_cookies.json | xclip -selection clipboard
```

## ⚠️ Important
- Cookies expire! Refresh weekly
- Never commit cookies to Git (they're in .gitignore)
- If bot fails with "cookies invalid", re-export fresh cookies
