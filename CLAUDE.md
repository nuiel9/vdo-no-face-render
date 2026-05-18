# CLAUDE.md — vdo-no-face-render

Project context for Claude Code. Durable, non-obvious facts that aren't already in `README.md`. Personal preferences live in `~/.claude/projects/-Users-krainats-vdo-no-face-render/memory/`.

## What this repo is

Render driver + content pipeline + Claude prompt library for **Disclosed** (`@disclosedch`), a faceless English-language YouTube channel doing business case studies / brand postmortems. Companion repo: `nuiel9/AIVDO` (the text-to-video service that does the rendering).

Day 0 of the 120-day plan to $10K/mo ad revenue = **2026-04-19**. Target = ~2026-08-17.

## Three locations — know which is canonical for what

1. **This repo** (`/Users/krainats/vdo-no-face-render`, GitHub `nuiel9/vdo-no-face-render`) — static code: `render.py`, `make_short.py`, `youtube_upload.py`, `lint_urls.py`, `propagate_correction.py`, `prompts/`, `pipeline.json` mirror.
2. **Google Drive vault** — `My Drive/vdo-no-face/` (folder id `1sAnpdfrU-tZd9FzVe6uBoo7rq5h2Zoxd`). **Canonical** mutable state: `pipeline.json` (user edits here to trigger renders), `secrets/prod.json`, `queue/`, `Daily/<slug>/`, `failed/`, `briefs/`. Not mounted to a local FS path on this Mac — access via MCP Drive tools.
3. **Orchestration docs** — `/Users/krainats/Documents/claude/Projects/VDO No Face/`: V3 blueprint (`00_Faceless_YouTube_Blueprint_V3_AIVDO.md`), routine prompt (`routine_v4.6_prompt.md`), AIVDO ship logs.

When asked to change pipeline state, edit Drive's `pipeline.json` — the routines read from Drive, not the repo mirror.

## Two scheduled routines

- **Routine A** — daily 08:00 Bangkok (weekdays). Picks the next row where `script_status == "queue_next"`, runs the 17-prompt flow, writes `Daily/<slug>/`, submits two AIVDO renders, drops `queue/row_NN_submitted.json`.
- **Routine B** — hourly. Polls `queue/`, downloads completed jobs, stitches with `pace_to_narration` + `xfade`, uploads `final.mp4` to Drive, posts Slack. Hard failures move to `failed/`.

Routine prompt source of truth: `/Users/krainats/Documents/claude/Projects/VDO No Face/routine_v4.6_prompt.md` (currently v4.6.3).

## Editorial gate is real infrastructure

The 17-prompt research routine fabricates ~4 specifics per slug at Netflix-doc fidelity. Wrong facts spoken in narration are unrecoverable post-publish.

**A slug does not render until `Daily/<slug>/.facts_verified` exists.** Per-slug flow:
```bash
python3 lint_urls.py Daily/<slug>/         # 30 sec
# read REVIEW.md, fix fabrications:
# python3 propagate_correction.py Daily/<slug>/ "wrong" "right" --apply
touch Daily/<slug>/.facts_verified
git add . && git commit -m "<slug>: facts verified" && git push
PYTHONUNBUFFERED=1 python3 -u render.py Daily/<slug>/
python3 youtube_upload.py Daily/<slug>/
```

**Human Fingerprint Checklist** — every published video must have:
1. Primary-source citation visible on screen in first 90s
2. One hand-typed correction or caveat
3. Cross-reference to a previous Disclosed video
4. Custom thumbnail (not AIVDO default poster mode)
5. Pinned comment with editorial note or source link
6. Cadence ≤ **3 videos/week per channel** (hard cap — YouTube policy trigger)

Avoid: numeric-suffix titles, identical thumbnail templates across 5+ videos, repeated exact scene compositions.

## Channel + render facts

- Channel: `@disclosedch`. Pivoted Thai → English on 2026-04-27.
- Voice: **Algieba** (Gemini TTS).
- Render mode: AIVDO Cinematic + strict_cinematic + `faceless_youtube` intent.
- Cinematic cost ≈ $1.32/video (gpt-image-2 × 16 scenes × $0.041 × 2 parts).
- Secondary channel work is **deferred to Day 60–90** — don't propose it before Disclosed hits YPP.

## Local fallback only

`render.py` standalone is the documented fallback. Default path is the scheduled routines via Drive — don't suggest local `render.py` as the primary way to ship a video.

## Hook taxonomy + conversion signals (as of 2026-05-10)

Three hook patterns now have empirical performance data on Disclosed. Use this when ranking slug candidates:

| Hook pattern | Format that works | Data point |
|---|---|---|
| consumer-grievance | long-form (needs structural payoff) | McDonald's #30 = 659 long-form views; Short version only 18 |
| bankruptcy-reversal | Short (single concrete reversal fits 60s) | Thai Airways Short = 48 views/18h, beat McDonald's Short |
| structural-truth | both, biased to long-form | 28% of Browse traffic engages here |

**v4.6.3 subscribe-CTA is the conversion structural unlock.** Pre-CTA channel state was ~541 views with ~0 subs. Post-CTA + Shorts batch: 802 views (28d), +2 subs (28d), 5 subs realtime in last 48h. The narration CTA ("subscribe to Disclosed, we ship three a week") plus the Shorts UI affordance is what flipped the conversion math. **Do not ship a long-form slug that loses the in-narration CTA.**

**Distribution model — Browse impressions are rationed per-channel (verified 2026-05-14 via Analytics API + Studio Reach tabs).**

The channel's view engine is the Browse/Home feed (~88-93% of views on videos that scale). YouTube gives each upload an initial Browse impression test batch, watches CTR + early retention, then decides whether to scale. The critical finding: **that impression ration is per-channel, and cadence dilutes it.**

Evidence from the 2026-05-05 → 2026-05-13 ships:

| Video | Impressions | CTR | Views | Avg view | Outcome |
|---|---|---|---|---|---|
| McDonald's #30 (5/05) | 12,100 | 4.2% | 673 | 2:58 | scaled |
| Peloton #38 (5/08) | 9,000 | 3.2% | 453 | 2:01 | scaled |
| MoviePass #17 (5/11) | 193 | 1.6% | 4 | 3:28 | starved |
| DocuSign #33 (5/12) | 713 | 0.7% | 10 | 0:56 | starved |

McDonald's and Peloton shipped when the channel was uploading slowly — they got 9-12K-impression test batches, cleared the bar, scaled. The 5/08-5/13 cluster (6 videos in 6 days) split one channel's Browse ration six ways: each got 200-700 impressions, a batch too small to evaluate. **MoviePass had the best retention of all four (3:28) and still died at 193 impressions** — proof the failure is allocation, not content quality.

**Wider snapshot (as of 2026-05-17, view counts only — impressions/CTR not re-pulled):**

| Video | Ship date | Views | Notes |
|---|---|---|---|
| McDonald's #30 | 5/05 | 673 | scaled |
| Peloton #38 (Churn $50B) | 5/08 | 453 | scaled |
| Patagonia (Don't Buy This Jacket) | 5/07 | 164 | mid-tier — shipped day before the 5/08 cluster started, likely got a partial test batch |
| Circuit City | 5/10 | 75 | starved (mid-cluster) |
| IKEA | 5/09 | 55 | starved (mid-cluster) |
| SVB ($42B/36h) | 5/15 | 53 | 2 days post-ship — too early to call but tracking starved |
| Lululemon (Yoga Pants $108) | 5/03 | 45 | older ship, never scaled — content/CTR failure, not allocation |
| DocuSign #33 | 5/12 | 10 | starved (cluster + weak packaging) |
| MoviePass #17 | 5/11 | 4 | starved (cluster, despite best retention) |

Reinforces the rationing thesis: every video shipped inside the 5/08-5/13 cluster sits in the 4-75 view band regardless of hook quality. Patagonia (164, shipped 5/07) is the cliff — it got most of a real test batch and landed mid-tier. Lululemon (5/03, 45 views) is the lone counterexample of an old ship that starved without a cluster — that one is a content/CTR problem, not allocation.

**The ≤3 videos/week cap is an impression-budget constraint, not just a YouTube-policy guard.** Shipping ≤3/week is what lets each video get a real (~9-12K) test batch. Flooding guarantees every video starves regardless of hook quality or packaging.

CTR still matters at the margin: McDonald's/Peloton cleared ~3-4%, DocuSign's 0.7% is genuinely weak packaging (and YouTube routed it to Suggested, not Browse, as a result). Suggested ≈ 1-7% of traffic and Search is nascent — neither is the lever. The lever is: **(1) cadence discipline so each video gets a real Browse test, (2) thumbnail/title CTR to clear ~3% on that test, (3) broad topical curiosity** ("why are McDonald's ice cream machines always broken" is universally curious; dry B2B/finance topics test worse on Browse).

When ranking unscheduled slugs: weight broad topical curiosity alongside the ≥2-hook-pattern rule. A perfect-hook slug shipped into a flooded week still gets 200 impressions.

