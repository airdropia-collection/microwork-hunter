## 📋 Summary

<!-- What does this PR do? Link any relevant issues with "Fixes #123" or "Closes #123". -->

## 🔧 Type of change

- [ ] 🐛 Bug fix (non-breaking)
- [ ] ✨ New feature (non-breaking)
- [ ] 💥 Breaking change (fix or feature that would cause existing functionality to not work as expected)
- [ ] 📚 Documentation update
- [ ] 🧪 Test improvement
- [ ] 🔒 Security fix
- [ ] 🏗️ Refactor (no functional change)

## 🧪 Testing

- [ ] Ran `pytest -v` locally — all tests pass
- [ ] Ran `ruff check src tests` — no new lint errors
- [ ] If new platform: added tests in `tests/test_<platform>_platform.py`
- [ ] If new feature: updated `CHANGELOG.md` under `[Unreleased]`

## 🔐 Security checklist

- [ ] No real cookies, API keys, or PATs in this PR
- [ ] No new env vars added without updating `.env.example` and `src/config.py`
- [ ] No `print()` of sensitive values (use `src/utils/sanitizer.py` if logging errors that may contain secrets)

## 📸 Screenshots / logs (if applicable)

<!-- For UI changes or new platform adapters, paste a screenshot of the dashboard/task page (redact personal info). -->

## ✅ Reviewer checklist

- [ ] CI is green
- [ ] Tests cover the new behavior
- [ ] Documentation updated (README, CHANGELOG, CONTRIBUTING as needed)
- [ ] No secrets leaked
- [ ] If touching `.github/workflows/`, tested manually via `workflow_dispatch`
