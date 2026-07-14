# Contributing to Microwork Hunter

First off — thank you for taking the time to contribute! 🎉

This document explains how to propose changes, add new platforms, and run tests locally.

---

## 🚀 Quick Start for Contributors

```bash
# 1. Fork & clone
git clone https://github.com/<your-username>/microwork-hunter.git
cd microwork-hunter

# 2. Create venv & install with dev extras
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -e ".[dev]"
python -m playwright install chromium

# 3. Configure env (local dev)
cp .env.example .env
# edit .env: set GEMINI_API_KEY and (optional) cookie file paths

# 4. Run tests
pytest -v

# 6. Lint
ruff check src tests
```

---

## 🧱 Architecture Overview

```
src/
├── browser/         # Browser abstraction (Obscura stealth + Playwright fallback)
│   ├── base_browser.py        # Abstract interface
│   ├── obscura_browser.py     # CDP connect to Docker container
│   └── playwright_browser.py  # Local fallback
│
├── platforms/       # Per-site adapters (one file per platform)
│   ├── base.py                # BasePlatform + MicroworkTask dataclass
│   ├── sproutgigs.py
│   ├── coinpayu.py
│   ├── timebucks.py
│   └── prizerebel.py
│
├── hunters/         # Task discovery
│   └── discover.py            # CLI: python -m src.hunters.discover
│
├── workers/         # Execution & review handling
│   ├── executor.py            # CLI: python -m src.workers.executor
│   └── review_handler.py      # CLI: python -m src.workers.review_handler
│
├── utils/           # Cross-cutting concerns
│   ├── ai_helper.py           # Gemini → Groq → Jina fallback
│   ├── cookie_validator.py
│   ├── earnings_tracker.py
│   └── review_compiler.py
│
└── config.py        # Reads env vars / GitHub Secrets
```

**Key principles:**

1. **Human-in-the-loop by default.** Every execution starts in `dry_run=true`. Submission only happens after a reviewer comments `/approve` on a GitHub Issue.
2. **Platform adapters are isolated.** A bug in `coinpayu.py` must never crash `timebucks.py`. Each adapter is a context manager that opens and closes its own browser.
3. **AI is lazy-loaded.** `ai_helper.py` imports Gemini/Groq lazily so that test environments without those packages can still import the module.
4. **Evidence is mandatory.** Every execution produces a screenshot before/after. No exceptions.

---

## ➕ Adding a New Platform

1. **Create the adapter file:** `src/platforms/<name>.py`
2. **Subclass `BasePlatform`:**
   ```python
   from .base import BasePlatform, MicroworkTask
   from src.config import CONFIG

   class MyPlatform(BasePlatform):
       def __init__(self):
           super().__init__(
               name="myplatform",
               base_url="https://myplatform.com",
               cookies=CONFIG.cookies_myplatform,
           )

       def discover_tasks(self):
           # Return List[MicroworkTask]
           ...

       def execute_task(self, task, dry_run=True):
           # Return Dict[str, Any] with status: pending|dry_run|completed|failed
           ...
   ```

3. **Add cookies property to `src/config.py`:**
   ```python
   @property
   def cookies_myplatform(self):
       return self._decode_cookies("COOKIES_MYPLATFORM")
   ```

4. **Register the adapter** in TWO places:
   - `src/hunters/discover.py` → `PLATFORM_MAP`
   - `src/workers/executor.py` → `PLATFORM_MAP`

5. **Update `src/utils/cookie_validator.py`** → add to `PLATFORMS` dict.

6. **Add tests** in `tests/test_<name>_platform.py`. At minimum test `discover_tasks()` with a mocked browser page.

7. **Update README** platform table + add the new secret to `.env.example` + `.github/workflows/hunter.yml` setup-cookies step.

---

## 🧪 Testing Conventions

- **All utility functions must have tests.** Use `pytest` + `monkeypatch` for env vars and `tmp_path` for filesystem.
- **Browser-touching code is not unit-tested** — it's integration-tested by the Hunter workflow itself. Mock the browser page in unit tests.
- **Snapshot tests for review_handler** — when adding a new command, add a test case in `tests/test_review_handler.py`.

Run tests:
```bash
pytest -v --tb=short
pytest --cov=src --cov-report=term-missing
```

---

## 🎨 Coding Standards

- **Python 3.10+** (use `from __future__ import annotations` for forward refs)
- **Type hints** are mandatory on all public functions
- **`ruff`** for linting — config in `pyproject.toml`
- **No `print()` in production code** — use the `logging` module via `src.utils.logger`
- **No bare `except:`** — always catch `Exception` at minimum, prefer specific exceptions
- **Docstrings** on every class and every non-trivial function

---

## 📝 Commit Message Convention

We use [Conventional Commits](https://www.conventionalcommits.org/):

```
feat:     new feature
fix:      bug fix
docs:     documentation only
refactor: code change that neither fixes a bug nor adds a feature
test:     adding tests
chore:    build / ci / tooling
sec:      security fix (also adds a SECURITY.md note)
```

Example: `feat: add ySense platform adapter with survey discovery`

---

## 🔀 Pull Request Process

1. **Branch name:** `<type>/<short-description>` (e.g. `feat/ysense-platform`)
2. **Open PR against `main`**
3. CI must be green (lint + tests)
4. **Squash-merge** only (configured at repo level)
5. Branch is auto-deleted on merge

For substantial changes (>200 LOC or new platform), please open an issue first to discuss the design.

---

## 🐛 Reporting Bugs

Open an issue using the **Bug Report** template. Include:
- Platform affected
- Workflow run URL (if applicable)
- Log excerpt (redact any cookies/tokens)
- Reproduction steps

---

## ❓ Questions

Open a [GitHub Discussion](https://github.com/airdropia-collection/microwork-hunter/discussions) — we monitor it actively.

Happy hacking! 🤖
