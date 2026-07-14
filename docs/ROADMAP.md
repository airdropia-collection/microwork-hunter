# 🎯 Microwork Hunter — Roadmap & Targets

> **Honest expectations, realistic milestones, sustainable growth.**
>
> This document defines what success looks like for Day 1, Week 1,
> Month 1, and Year 1. Numbers are **conservative estimates** based
> on real microwork platform payouts — not promises.

---

## ⚠️ Honest Reality Check (Read This First)

**Microwork is NOT a get-rich-quick scheme.** Here's what you need to understand before we start:

### What this bot CAN do:
- ✅ Automate repetitive tasks (PTC ads, video watching, daily claims)
- ✅ Run 24/7 without your active involvement
- ✅ Aggregate small earnings across multiple platforms
- ✅ Filter out tasks that need manual work

### What this bot CANNOT do:
- ❌ Earn $100/day (realistic max is $1-5/day even with full automation)
- ❌ Replace a full-time job
- ❌ Bypass platform anti-bot systems forever (accounts get banned)
- ❌ Complete surveys that require genuine human opinions (AI is good but not perfect)

### Realistic per-platform daily earnings (with automation):

| Platform    | Task Type          | Realistic Daily Earnings      |
|-------------|--------------------|-------------------------------|
| SproutGigs  | Microjobs, surveys | $0.10 - $1.00                 |
| RewardJoy   | PTC ads            | 50-200 satoshi (~$0.005-0.02) |
| TimeBucks   | Videos, content    | $0.02 - $0.20                 |
| PrizeRebel  | Surveys            | $0.20 - $1.50                 |
| Cointiply   | PTC + faucet       | 50-200 coins (~$0.005-0.02)   |
| **Total**   | **All combined**   | **$0.40 - $2.75/day**         |

> These are **good-day** numbers. Bad days (cookie expired, no tasks available, platform down) will be $0.

---

## 📅 Phase 0: Pre-Launch (TODAY — before first run)

### Goals:
- ✅ Code is deployed and CI is green
- ✅ All platform adapters are ready
- ✅ Task filter is blocking manual-intervention tasks
- ✅ Social media tasks are blocked by default

### What YOU need to do:
1. **Add GitHub Secrets** (https://github.com/airdropia-collection/microwork-hunter/settings/secrets/actions):
   - ✅ `GEMINI_API_KEY` (you added this — good)
   - ❌ `GROQ_API_KEY` (you mentioned having this but didn't add it — please add)
   - ✅ `COOKIES_rewardjoy` (you added this)
   - ✅ `COOKIES_SPROUTGIGS` (you added this)
   - ✅ `COOKIES_TIMEBUCKS` (you added this)
   - ❌ `COOKIES_PRIZEREBEL` (not added — add when you have an account)
   - ❌ `COOKIES_COINTIPLY` (not added — add when you have an account)
   - ❌ `LTC_ADDRESS` (optional — for crypto withdrawals)

2. **Revoke the leaked PAT** (https://github.com/settings/tokens — the one you shared in chat)

3. **Wait for me to push the RewardJoy rename** (this commit)

### Success criteria for Phase 0:
- [ ] All secrets you want to use are added
- [ ] CI workflow passes
- [ ] Health check shows ✅ for at least 3 platforms

---

## 📅 Day 1: First Run & Validation

### Goals:
- Verify the bot actually works end-to-end
- Confirm cookies are valid
- Get first successful dry-run task completion
- Get first REAL task submission (after your `/approve`)

### Targets:
| Metric                          | Target  |
|---------------------------------|---------|
| Platforms with valid cookies    | 3+      |
| Tasks discovered                | 5-15    |
| Tasks passing filter            | 3-10    |
| Tasks dry-run completed         | 3-10    |
| Tasks you approve               | 1-3     |
| Tasks actually submitted        | 1-3     |
| **Estimated earnings**          | **$0.01 - $0.10** |

### What we're really testing:
- Does Obscura browser start correctly in GitHub Actions?
- Do cookies authenticate successfully?
- Does the task filter correctly reject manual tasks?
- Does the review Issue get created?
- Does `/approve` trigger actual submission?

### Your role on Day 1:
1. I trigger the first Hunter run (dry_run=true)
2. You get a GitHub Issue notification on your phone
3. You review the pending tasks table
4. You comment `/approve <task-id>` for 1-2 safe-looking tasks
5. The review-bot submits them
6. We check the results together

---

## 📅 Week 1: Stabilization

### Goals:
- Run the bot on the 4-hour schedule without crashes
- Identify and fix platform-specific issues
- Establish a cookie-refresh routine
- Tune the task filter based on what tasks appear

### Targets:
| Metric                          | Target     |
|---------------------------------|------------|
| Successful scheduled runs       | 30+ (out of 42) |
| Tasks discovered (cumulative)   | 100-300    |
| Tasks submitted (cumulative)    | 20-60      |
| Cookie refresh cycles           | 1          |
| **Estimated earnings**          | **$0.50 - $3.00** |

### What we'll be doing:
- **Day 2-3:** Monitor for cookie expiry, fix any selector breakages
- **Day 4-5:** Add PrizeRebel + Cointiply accounts if you create them
- **Day 6-7:** First cookie refresh cycle, tune reward thresholds

### Success criteria for Week 1:
- [ ] Bot runs 4-hourly without manual intervention
- [ ] At least 20 tasks successfully submitted
- [ ] No account bans (if banned, we debug why)
- [ ] Earnings tracker shows > $0.50 total

---

## 📅 Month 1: Optimization

### Goals:
- Maximize earnings per run
- Add 1-2 more crypto platforms (Picoworkers, adBTC)
- Implement earnings dashboard (GitHub Pages)
- Tune AI prompts for better survey completion

### Targets:
| Metric                          | Target       |
|---------------------------------|--------------|
| Tasks submitted (cumulative)    | 200-500      |
| Platforms active                | 4-5          |
| Average tasks per run           | 5-10         |
| Cookie refresh cycles           | 4            |
| **Estimated earnings**          | **$5 - $20** |

### What we'll add:
- **Picoworkers adapter** (LTC/BTC payouts, microjobs)
- **adBTC adapter** (BTC direct, PTC ads)
- **Earnings dashboard** — a GitHub Pages site showing daily/weekly/monthly earnings charts
- **Telegram notification bot** (optional — you'd need to create a bot via @BotFather)
- **OCR verification** — screenshot analysis to confirm task completion

### Success criteria for Month 1:
- [ ] 5+ platforms all producing tasks
- [ ] Earnings dashboard is live and updating
- [ ] Monthly earnings > $5
- [ ] Bot runs are stable (95%+ success rate)

---

## 📅 Year 1: Scale & Sustain

### Goals:
- Maximize passive income from microwork
- Explore multi-account strategies (if TOS allows)
- Reinvest earnings into better infrastructure if needed
- Document everything for reproducibility

### Targets:
| Metric                          | Target         |
|---------------------------------|----------------|
| Total tasks submitted           | 5,000-15,000   |
| Platforms active                | 6-8            |
| Average monthly earnings        | $10 - $50      |
| **Estimated yearly earnings**   | **$120 - $600**|

### Reality check on Year 1:
Even with perfect automation across 8 platforms, microwork earnings have a hard ceiling. The platforms themselves limit how many tasks one account can do per day. To exceed $50/month, you'd need:

1. **Multiple accounts on each platform** (risky — TOS violation)
2. **Higher-value task types** (surveys, offers — but these need more AI sophistication)
3. **Referral income** (invite others — but that's a separate business model)

### What we'll do in Year 1:
- Q1: Stabilize, optimize, add platforms
- Q2: Build dashboard, add Telegram alerts, explore OCR
- Q3: Evaluate multi-account feasibility (carefully)
- Q4: Year-end review, plan Year 2

---

## 🚨 Risk Management

### Account Ban Risk:
- **High risk platforms:** SproutGigs, RewardJoy (aggressive anti-bot)
- **Medium risk:** TimeBucks, Cointiply
- **Low risk:** PrizeRebel (mostly survey-focused)

**Mitigation:**
- Human-like delays (2-8 seconds between actions) — already implemented
- Obscura stealth browser — already implemented
- Limit to 5 tasks per platform per run — already implemented
- Never run social media tasks (account ban almost guaranteed)

### Cookie Expiry Risk:
- Cookies typically expire in 7-14 days
- The health check will warn you
- **Your job:** refresh cookies weekly (set a phone reminder)

### Earnings Volatility:
- Some days = $0 (no tasks, platform down, cookies expired)
- Some days = $2+ (lots of tasks, everything works)
- **Don't panic on bad days** — weekly average is what matters

---

## 📊 How to Track Progress

The bot automatically generates these artifacts each run:
- `earnings.json` — running total of earnings per platform
- `task_state.json` — dedup state (which tasks already done)
- `discovery_log.json` — what was found each run
- `review_package.json` — what's pending your approval

After each run, check:
1. **GitHub Actions tab** — did the run succeed?
2. **GitHub Issues** — any review-required issues?
3. **Actions artifacts** — download `evidence-<run_id>` to see screenshots

---

## 🤝 Our Division of Labor

| Task | Who |
|------|-----|
| Code, architecture, bug fixes, new platforms | **Me (AI assistant)** |
| Adding secrets, refreshing cookies | **You** |
| Reviewing pending tasks (mobile) | **You** |
| `/approve` or `/reject` decisions | **You** |
| Monitoring earnings | **Both** |
| Strategic decisions (add platform X? enable social?) | **You decide, I implement** |

---

## 🎯 Immediate Next Steps (in order)

1. **[You]** Add `GROQ_API_KEY` to GitHub Secrets (you said you have it)
2. **[Me]** Push the RewardJoy rename commit (this session)
3. **[Me]** Trigger first Hunter run (dry_run=true)
4. **[You]** Watch for GitHub Issue notification
5. **[You]** Review pending tasks, comment `/approve <task-id>`
6. **[Me]** Monitor submission results, fix any issues
7. **[Both]** Review Day 1 results, plan Week 1 adjustments

---

*Last updated: 2026-07-14*
*This document is a living roadmap — it will be updated as we learn what works and what doesn't.*
