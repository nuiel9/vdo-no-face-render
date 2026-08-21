# CLAUDE.md — vdo-no-face-render

Project context for Claude Code. Durable, non-obvious facts that aren't already in `README.md`. Personal preferences live in `~/.claude/projects/-Users-krainats-vdo-no-face-render/memory/`.

## What this repo is

Render driver + content pipeline + Claude prompt library for **Disclosed** (`@disclosedch`), a faceless YouTube channel. Companion repo: `nuiel9/AIVDO` (the text-to-video service that does the rendering).

**The channel is Thai, not English — approved 2026-08-20** (`docs/superpowers/specs/2026-08-20-thai-pivot-design.md`, hereafter "the Thai spec"). The 120-day English-language plan below is **closed history**, not the current strategy; see "Thai pivot (current)" further down for what replaced it.

*Historical: the original 120-day plan to $10K/mo ad revenue ran **2026-04-19 → ~2026-08-17**. It closed at 8 subscribers and ~$0. Every cheap-to-medium lever (topic, packaging, archetype, cadence, `defaultAudioLanguage=en`, channel country=US, even a fresh US-classified channel) was tried and falsified. Full audit trail: Thai spec §1 and the memory files marked SUPERSEDED below.*

## Three locations — know which is canonical for what

1. **This repo** (`/Users/krainats/vdo-no-face-render`, GitHub `nuiel9/vdo-no-face-render`) — static code: `render.py`, `make_short.py`, `youtube_upload.py`, `lint_urls.py`, `propagate_correction.py`, `prompts/`, `pipeline.json` mirror.
2. **Google Drive vault** — `My Drive/vdo-no-face/` (folder id `1sAnpdfrU-tZd9FzVe6uBoo7rq5h2Zoxd`). Still holds `secrets/prod.json` and is the intended home for `pipeline.json`, `queue/`, `failed/`, `briefs/`. **`Daily/<slug>/` is NOT canonical here — verified false 2026-08-21.** The vault's `Daily/` contains only two empty folders left over from the 2026-04-24 dry run; the last ~16 ships (including both scripts that still exist) were fired manually in-session and wrote to **local disk only**. Don't look in Drive for a slug's `SCRIPT.txt` or build artifacts — look in this repo's local `Daily/<slug>/`. Not mounted to a local FS path on this Mac — access via MCP Drive tools.
3. **Orchestration docs** — `/Users/krainats/Documents/claude/Projects/VDO No Face/`: V3 blueprint (`00_Faceless_YouTube_Blueprint_V3_AIVDO.md`), routine prompt (`routine_v4.6_prompt.md`), AIVDO ship logs.

When asked to change pipeline state, the *intent* is still to edit Drive's `pipeline.json` (routines are designed to read from Drive, not the repo mirror) — but confirm the actual artifact you need lives where you expect before trusting Drive, per the `Daily/<slug>/` correction above.

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
6. ~~Cadence ≤ 3 videos/week per channel (hard cap — YouTube policy trigger)~~ **Retired by the Thai spec §8.** Replaced by the four-mode editorial gate (News/fast, Remake, Research/verifiable, Research/attribution) plus a machine first pass — see "Thai pivot (current)" below. The gate's *editorial-attention* rationale survives; the *impression-rationing* rationale that originally justified the cap did not (falsified by later English-run data, retained as history below).

Avoid: identical thumbnail templates across 5+ videos, repeated exact scene compositions. **Do NOT avoid numeric-suffix titles — reversed by Thai spec §5.2.** Disclosed now runs a persistent `EP01`, `EP02`... counter as a franchise signal, matching the Thai benchmark channel's structure.

## Channel + render facts

- Channel: `@disclosedch`. Pivoted Thai → English on 2026-04-27; **the Thai spec (approved 2026-08-20) reverts this — @disclosedch becomes the Thai channel again**, with `Business Postmortems` (`UCTJDWGKcUKee7iXW2eXeUnA`) taking over as the English archive/AIVDO-showcase channel. See "Thai pivot (current)" below for what ships next.
- Voice: ~~Algieba~~ **`Erinome`, female, `normal` style — LOCKED (Thai spec §5.4).** `Algieba` is **male** (`config.py:209`, gender=male, particle=ครับ) — the channel's narrator was male for the entire English run. Chosen by listening against nine other candidates on 2026-08-20. Gemini TTS stays primary (style control matters for documentary narration); Chirp3-HD stays the fallback it already was — this was never a two-voice question.
- Render mode: `render_mode="fast"` (AIVDO's Gemini-only Google image lane), `video_intent="faceless_youtube"` still applies (server-enforces no-faces per scene). ~~AIVDO Cinematic + strict_cinematic~~ and gpt-image-2 are retired for this channel per Thai spec §6.1 — default image model is `gemini-3.1-flash-image` ($0.067/img), chosen on a same-prompt quality sweep, not price.
- ~~Cinematic cost ≈ $1.32/video (gpt-image-2 × 16 scenes × $0.041 × 2 parts)~~ — that was the 2-part, 8-minute English format. Current: Lane B (15–20 min) runs 4–5 parts, Lane A (8–10 min) stays closer to the old 2-part scale; **all-in ≈ $170–230/month** blended across both lanes (Thai spec §6, §11), not a fixed per-video figure.
- Secondary channel work is **no longer deferred** — `Business Postmortems` is now an active second channel per the Thai spec (§4), not something waiting for Disclosed to hit YPP.

## Local fallback only

`render.py` standalone is the documented fallback. Default path is the scheduled routines via Drive — don't suggest local `render.py` as the primary way to ship a video.

## Thai pivot (current)

**Approved 2026-08-20.** Full reasoning and evidence: `docs/superpowers/specs/2026-08-20-thai-pivot-design.md`. This section is the short version; the spec wins on any conflict.

- **The English run is closed, not paused.** 8 subs, ~$0, over ~4 months. Every cheap lever was tried and falsified (spec §1). Do not re-propose "try a different American topic/thumbnail/cadence" — that space is exhausted.
- **@disclosedch becomes the Thai channel again.** English long-form gets unlisted before Thai EP01 ships. `Business Postmortems` (`UCTJDWGKcUKee7iXW2eXeUnA`) becomes the English archive + AIVDO showcase (spec §4).
- **Goal is $10K/mo mixed** (AdSense + sponsorship + AIVDO conversions), not AdSense-only. **Primary KPI is `aivdo_trials_attributed` per video**, not views (spec §2).
- **Scope widens to tech + business + curiosity, weighted toward tech** — not business-case-studies-only. Format stays faceless documentary (spec §5.3).
- **Two lanes, both from week one:** Lane A "Disclosed Daily" (current AI/tech news, 8–10 min, ~4/wk, fast-path gate) and Lane B "Disclosed Story" (postmortems/curiosity, 15–20 min, ~3/wk). Lane A leads — it's a level playing field against a 2,600-video Thai incumbent, and it's where the owner has real authority (spec §7.1–7.2).
- **Back-catalogue is filler, not the engine, and the pool is currently empty.** Only 2 of 18 local `Daily/` dirs have a `SCRIPT.txt` (#56 Ticketmaster, #57 TurboTax), and both fail the Thai-relevance filter — zero slugs are both remake-able and Thai-relevant as of 2026-08-21 (spec §7.4).
- **Numeric-suffix EP titles are the format now** (`... | Disclosed EP01`), reversing the old "avoid numeric-suffix titles" rule (spec §5.2).
- **Voice: Gemini TTS, `Erinome`, female, `normal` style, locked** (spec §5.4). Thai particles auto-agree to voice gender — every episode closes in ค่ะ.
- **Images: Gemini-only, no OpenAI.** Default `gemini-3.1-flash-image`. Thai on-screen text is always renderer-burned, never image-model-generated (spec §6.1–6.2).
- **The ≤3/week cadence cap is retired**, replaced by a four-mode editorial gate (News/fast, Remake, Research/verifiable, Research/attribution) plus a machine first pass ahead of the human gate (spec §8). `.facts_verified` still blocks render — that discipline is unchanged.
- **Infra is currently blocking:** all three YouTube OAuth tokens are dead, and the fix is to move the OAuth app to Production, not just re-auth (spec §9).
- **Hard gate: day-14 routing checkpoint.** If Thai ships also starve at English-run impression levels, the channel is poisoned for any language, not just English — the move then is to Business Postmortems or a fresh Thai channel (spec §10).

## Hook taxonomy + conversion signals (as of 2026-05-10) — *SUPERSEDED — see "Thai pivot (current)" above for the current model (the "Distribution model, 5th revision" section below is ALSO superseded — it was the intermediate English-run model, not the current one). The 5/10 hook taxonomy and 5/14 rationing framing were both falsified by 5/23 McDonald's-vs-Blackberry analytics comparison. Retained for audit trail.*

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

## Distribution model (5th revision, 2026-05-23) — *SUPERSEDED 2026-08-21 by the Thai spec's §7 slug-selection heuristic. See "Thai pivot (current)" above for what replaced it. Retained for audit trail — this is the model whose Tier A/B/C ranking (below) actively **mis-ranks** slugs for a Thai audience: e.g. Blackberry was scored Tier C here for reading "foreign-tech" to a US viewer, but that reasoning doesn't hold for Thailand, where BBM was widespread — the Tier C *label* is wrong for the wrong reason. (Blackberry is independently cut for Thai anyway, per the Thai spec's own saturation audit, §7.7: covered twice already by incumbent ด.ดล Blog, EP537 and Geek Monday EP264.) Do not use these tiers for Thai slug selection.*

*This section was the CURRENT canonical model for the English run. The 5/10 hook taxonomy and 5/14 rationing model above are retained for audit trail but should not be used for new ship planning — and neither should this section, now that the channel is Thai again.*

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

### Slug selection heuristic (superseded — was current for the English run, supersedes the 5/10 hook taxonomy)

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


