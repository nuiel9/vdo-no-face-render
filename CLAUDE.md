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

## Hook taxonomy + conversion signals (as of 2026-05-10) — *SUPERSEDED — see "Distribution model (current, 5th revision)" section below for the current model. The 5/10 hook taxonomy and 5/14 rationing framing were both falsified by 5/23 McDonald's-vs-Blackberry analytics comparison. Retained for audit trail.*

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

---

## Distribution model (current, 5th revision as of 2026-05-23)

*This section is the CURRENT canonical model. The 5/10 hook taxonomy and 5/14 rationing model above are retained for audit trail but should not be used for new ship planning.*

**The primary lever is TOPIC-LEVEL American cultural touchstone.** Disclosed is currently classified by YouTube as a Thai-default channel (legacy from before the 2026-04-27 Thai→English pivot). For any individual ship to break out of that classification and scale, its topic must be recognizable enough as a universal American consumer experience that YouTube routes early impressions to the American Browse audience instead of defaulting to Thai loyalists. Packaging is a second-order discipline — it determines whether the right audience clicks, not which audience YouTube tests with.

**Empirical proof (2026-05-23):**

| Metric | McDonald's #30 (18d, scaled) | Blackberry #7 (25h, starved) |
|---|---|---|
| Subtitle/CC language | No-subs 50.1% + English 49.5% + Thai 0.4% | **Thai auto-translated 100%** |
| Top geography | United States 78.3%, Canada 3.8% | (Thailand-default) |
| Browse share | 87.0% | 20.0% |
| Impressions | 12,100 | 221 |
| CTR | 4.2% | 2.7% |
| End-screen click rate | 11.1% (9× channel average) | 0% |
| Suggested adjacencies | Random wide-curiosity (Dutton Ranch trailer, pasta factory, cast iron, ghee, water bottles) | (no data yet) |

McDonald's audience was 99.5% non-Thai. Blackberry's was 100% Thai-translated. Same channel, same template-discipline. The topic-level cultural recognition was the differentiator.

**The American Browse audience for Disclosed** (per McDonald's demographics): older American males, 65+ : 48%, 55-64 : 31%, 45-54 : 21%, watching daytime YouTube on Computer (51%) and Mobile (41%). Their cultural touchstones are universal American consumer/retail/brand experiences. NOT tech business cases or B2B SaaS histories.

### Slug selection heuristic (current, supersedes the 5/10 hook taxonomy)

**Primary gate: pass the universal-American-cultural-touchstone test.** Score every candidate slug against: "would a 55-year-old American man watching daytime YouTube instantly recognize this topic AND have wondered about it?" If no, the ship will starve regardless of how well written or packaged.

**Topics that pass (verified by 5/23 data):**
- Famous American ad campaigns (Patagonia "Don't Buy This Jacket")
- Universal grievances (McDonald's broken machines)
- American household-brand decline (Sears, Toys R Us, Tupperware, Circuit City history)
- American subscription/lifestyle fatigue (Peloton, gym memberships)
- American retail/food/consumer oddities

**Topics that fail (verified by 5/23 data):**
- Tech business cases on non-American companies (BlackBerry — RIM is Canadian, reads as foreign-tech to the algorithm)
- B2B SaaS histories (DocuSign, Cloudera, Snowflake, MongoDB, Slack-Salesforce)
- Niche financial fraud cases (MoviePass-style)
- Object-trivia framings (Bic pen — household familiar but no consumer-grievance hook)
- All SEA business cases (CP Group, Shopee, Thai Airways, LINE Thailand, Sea Limited, Forex-3D, GoTo, SCB X, Vietjet)

**Secondary gate: Patagonia script + thumbnail discipline** (only matters once topic clears the primary gate):
- Scene-first cold open with a character anchor (not argument-first analytical hook)
- Text-as-hero thumbnail (provocative phrase or quote in bold editorial serif, on textured/newsprint background, with product as small supporting silhouette)
- Counter-intuitive title with specific-moment paradox
- 7:30-8:30 runtime
- Subscribe CTA in narration close (v4.6.3 mandate, still valid)

**Cadence cap ≤3 videos/week.** Reason refined: not "impression budget" (5/14 framing, falsified) and not "tier demotion" (5/19 framing, falsified). The cap exists because each ship needs sufficient editorial attention to clear both gates. Shorts count.

### Slug ranking (re-ranked 2026-05-23 against the cultural-touchstone primary gate)

**Tier A — strong cultural-touchstone, ship next:**
- **#40 Tupperware (75-year direct-sales collapse + 2024 Chapter 11)** — household American brand, older-audience nostalgia hits exactly the McDonald's demographic, recent bankruptcy is current-event-relevant. *Next ship target: 5/26 or 5/27.*
- **#27 Ben & Jerry's / Unilever** — American activism brand, M&A drama, "they bet against the corporate parent and won" frame.
- **#26 Amazon-Whole Foods 3 meetings** — corporate-merger consumer-recognizable story.

**Tier B — passes the gate but with caveats:**
- #18 Nintendo 1983 — gaming-nostalgia adjacent; could pull a different demographic
- #29 Apple almost sold to Sun 1995 — tech business case but Apple is universally American
- #6 Aldi vs Walmart — retail business but might be regional
- #11 Zara — fast fashion is global, less specifically American

**Tier C — fails the primary gate, defer or skip:**
- #7 Blackberry (already shipped, starved as the model predicts)
- #23 Bic (already shipped, starved)
- #8 Theranos — saturated American story (covered to death by Cold Fusion / Modern MBA)
- #25 Google SEO, #17 MoviePass, #33 DocuSign — B2B / financial-fraud
- #31 Cloudera, #32 Snowflake, #34 MongoDB SSPL, #35 Slack-Salesforce — B2B SaaS
- #37 OpenSea / NFT — saturated and crypto-specific
- #39 Allbirds — DTC brand, narrower than Tupperware
- #43–54 SEA topics (Lazada PH, AirAsia, LINE Thailand, Sea Limited, Forex-3D, GoTo, SCB X, Vietjet) — will get routed to Thai legacy audience by definition

**Bic Phase 3 repackage plan from 5/21** (in `Daily/2026-05-18_23_bic-trash-pen-2-5b-company/REVIEW.md`) — **dropped.** The topic was the bottleneck, not the package. Repackaging won't change the topic.


