# Security Policy

## 🔐 Reporting a Vulnerability

This project handles **authentication cookies** for microwork platforms and **API keys** for AI providers. A security vulnerability could leak these credentials and compromise user accounts.

**If you discover a vulnerability, please DO NOT open a public issue.** Instead:

1. Email: open a private security advisory via GitHub
   👉 https://github.com/airdropia-collection/microwork-hunter/security/advisories/new
2. Include:
   - Description of the issue
   - Steps to reproduce
   - Affected files/versions
   - Suggested fix (if any)

We will respond within 72 hours and credit responsible disclosure.

---

## 🛡️ Threat Model

| Threat | Mitigation in this repo |
|--------|--------------------------|
| Cookies committed to Git | `.gitignore` blocks `cookies/*.json` + `*.key` + `*.pem` + `*pat*` + `*token*` |
| Secrets in CI logs | All sensitive env vars are mapped via `${{ secrets.* }}`, never `echo`d |
| Token leakage in errors | Errors are stringified via `str(exc)` only — never raw cookie payloads |
| PAT in chat history | PAT is stored at `/home/z/.secrets/.gh_pat` (chmod 600), never in source |
| Supply-chain attacks | Dependabot + automated security fixes enabled; deps pinned in `requirements.txt` |
| Workflow injection | All workflow `inputs` are passed as quoted args; no shell interpolation of user input |

---

## 🚨 If You Leak a Secret

### Cookies leaked (any platform)
1. **Log out all sessions** on that platform immediately (usually under Settings → Security → Active Sessions)
2. Log back in, export fresh cookies, update GitHub Secret
3. Old cookies are now useless

### Gemini / Groq API key leaked
1. Go to https://aistudio.google.com/app/apikey → delete the key
2. Generate a new key, update GitHub Secret

### GitHub PAT leaked
1. https://github.com/settings/tokens → delete the token
2. Generate a new token, give it **only** the scopes needed
3. Update any local env files

---

## 🔍 Secret Scanning

The following files/patterns are forbidden in commits (enforced by `.gitignore`):

```
cookies/*.json        # Real cookie exports
.env                  # Local env file with real keys
.secrets/             # Any directory named .secrets
*.pem, *.key          # Private keys
*pat*, *token*        # Anything matching "pat" or "token" pattern
```

If you must commit a test fixture containing fake secrets, prefix it with `example_` or `fake_` and ensure values are obviously synthetic (e.g. `FAKE_TOKEN_12345`).

---

## 📜 Responsible Use

This project automates interaction with third-party microwork platforms. Users are responsible for:

- Reading and respecting each platform's Terms of Service
- Not using the bot for fraud, multi-accounting, or survey manipulation beyond what the platform allows
- Refreshing cookies on a regular schedule (recommended: weekly)
- Monitoring their accounts for unusual activity

The maintainers are not liable for account suspensions, fund freezes, or any other consequences of misuse.
