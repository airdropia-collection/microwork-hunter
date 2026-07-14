# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- `src/utils/logger.py` — centralized logging configuration with rich console output
- `src/utils/health.py` — startup health-check CLI (`python -m src.utils.health`)
- `src/utils/state.py` — task deduplication via `task_state.json`
- `src/utils/sanitizer.py` — secret sanitizer for safe error logging
- Tenacity-based retry decorators for all network calls
- Config validation at startup — fails fast with clear errors if required secrets missing
- SECURITY.md, CONTRIBUTING.md, CODE_OF_CONDUCT.md, CODEOWNERS
- Issue templates: bug report, feature request, platform support
- Pull request template
- GitHub Actions: 4-hourly Hunter + Review Response Bot + CI on every PR
- Branch protection on `main` (CI must pass, no force push)
- Dependabot + automated security fixes enabled

### Changed
- Replaced all `print()` calls with `logging` module throughout `src/`
- `src/utils/ai_helper.py` now lazy-imports Gemini/Groq (graceful degradation when optional deps missing)
- `src/workers/executor.py` now accepts both single-task dict and list of tasks
- `src/workers/review_handler.py` rewritten: parses commands, looks up tasks in `review_package.json`, returns actionable payloads
- `src/browser/__init__.py` resolved circular import — `get_browser()` now defined inside `__init__.py`
- README rewritten with TOC, structure diagram, local-dev guide, mobile-control walkthrough
- `.gitignore` expanded to block all secret patterns (`*.pem`, `*.key`, `*pat*`, `*token*`, `.secrets/`)

### Fixed
- 10 broken Python files where `"""` was escaped to `\"\"\"` (SyntaxError on import)
- f-string nested-quote bug in `review_handler.py` (`f'... {", ".join(...)} ...'` — invalid pre-3.12)
- `executor.py` could not handle `tasks_found.json` (which is a list, not a dict)
- Circular import in `src/browser/__init__.py` that broke `from src.utils.review_compiler import ...`
- Lazy imports in `ai_helper.py` so test environments without `google-generativeai` can still import the module

## [0.1.0] — 2026-07-14

### Added
- Initial release: 4-platform microwork hunter (SproutGigs, CoinPayu, TimeBucks, PrizeRebel)
- Obscura + Playwright browser abstraction
- Gemini → Groq → Jina AI fallback chain
- Cookie validator, earnings tracker, review compiler
- 19-test pytest suite (all passing)
- 3 GitHub Actions workflows
- MIT License
