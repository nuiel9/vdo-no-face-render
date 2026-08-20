# Design: Thai pivot — @disclosedch relaunch

**Date:** 2026-08-20
**Status:** Draft — awaiting review. All decision items closed; implementation plan pending approval.
**Supersedes:** the entire "Distribution model (current, 5th revision)" section of `CLAUDE.md`, and the slug-selection heuristic within it.

---

## 1. Why

The 120-day plan (Day 0 = 2026-04-19, target ~2026-08-17) closed three days ago at **8 subscribers and ~$0**. The English experiment is over, and it ended with a clean answer rather than an open question.

Every cheap-to-medium lever was tested in sequence and falsified: topic → packaging → archetype → cadence → `defaultAudioLanguage=en` → channel country=US. Three grievance ships under near-ideal conditions drew **19 / 11 / 13 impressions**.

The clean-channel test was decisive. A fresh US-country channel (Business Postmortems) running the *same three proven videos*:

- **Escaped the starve** — 313 and 815 impression bursts, so the wall was `@disclosedch`-specific, not account- or IP-level.
- **Removed the Thai signal** — subtitle language 0% Thai on both videos.
- **And still did not scale** — ~85% Suggested routing (not Browse), 1.2–2.7% CTR, mixed-language clusters, 54% TV-autoplay, plateau after a single burst.

**Reclassification was achieved and changed nothing.** The ceiling was not Thai-default classification. It was a zero-authority faceless English channel in a niche owned by Modern MBA, Cold Fusion, and Company Man. A restart alone does not fix that.

Meanwhile the same 8 weeks produced **592 commits on AIVDO**, now live at `aivdo.ai` as a Thai-first product (Free / นักเล่าเรื่อง ฿199 / ครีเอเตอร์ ฿499 / ธุรกิจ ฿1,490; Max Card + PromptPay). As of v1.57–v1.58 it is buying paid traffic, and the funnel is thin: **79 accounts, 42 video jobs in 30 days, 1 slide deck, 0 voice clips.** The stated problem is *"many users are arriving and still nobody uses it."*

So the channel's job has changed. It is no longer a standalone media bet. It is **the organic top-of-funnel for a Thai product that currently has none**, built with an engine that is already Thai-native.

---

## 2. Goal

**$10,000/month, mixed** — not $10K of AdSense.

The AdSense-only version is above the ceiling of the category. Benchmark (pulled 2026-08-20): ด.ดล Blog, the leading Thai channel in this exact niche, runs ~1.5–3M views/month at 84.9K subs after 845 episodes.

| Thai RPM (weakly sourced — see §11) | Views/mo for $10K | vs. ด.ดล Blog |
|---|---|---|
| $0.50 | 20M | ~8× |
| $1.00 | 10M | ~4× |
| $1.50 | 6.7M | ~2.7× |

The incumbent is probably earning **$750–$4,500/mo** from ads. Reaching $10K on ads alone would mean substantially out-performing them, starting from 8 subs.

Composition instead:

| Source | Role |
|---|---|
| AdSense | Lagging metric. Realistically $1–3K/mo at scale. |
| Sponsorship / brand deals | How Thai business channels actually monetise. Requires audience + authority. |
| **AIVDO conversions** | The lever with the shortest path. Attribution already instrumented (v1.57). |

**Primary KPI is `aivdo_trials_attributed` per video, not views.**

---

## 3. Benchmark

Reference channel: **ด.ดล Blog** (`@mrtharadhol`, brand "Geek Forever") — 84.9K subs, 2.6K videos, channel membership enabled. Pulled 2026-08-20:

| Episode | Length | Views | Age |
|---|---|---|---|
| ทำไมแว่นตาถึงแพง (why glasses are expensive) — Geek Story EP843 | 31:11 | 62K | 1d |
| De Beers diamonds — Geek Talk EP249 | 22:35 | 39K | 3d |
| Why Plasma TV died / Panasonic — Geek Monday EP337 | 15:47 | 22K | 3d |
| iPhone quietly killing Android — Geek Story EP844 | 15:28 | 15K | 1d |
| Companies cutting AI budgets, rehiring humans — Geek Story EP842 | 17:02 | 5.8K | 2d |
| ตำนาน John Titor — Geek Story EP845 | 14:14 | 4.5K | 22h |

**Three findings drive this design:**

1. **Cadence is ~2 videos/day.** Six uploads in three days.
2. **The category is curiosity, not business.** Urban legend, tech market shift, consumer pricing, labour, tech postmortem, consumer pricing. A pure business-postmortem well runs dry; a curiosity well sustains 845 episodes.
3. **Runtime is 14–31 minutes**, and the top performers are the longest ones.

Their best two (62K, 39K) are consumer-grievance / *"why is X expensive"* — the same archetype as Disclosed's only real hit (McDonald's, 679 views). **The archetype was never the problem. The market was.**

---

## 4. Positioning

**@disclosedch becomes the Thai channel.** Its Thai-default classification — the thing that poisoned the English run — is now aligned rather than fighting.

| Channel | Job |
|---|---|
| **@disclosedch** | The Thai channel. English long-form gets unlisted so the channel reads unambiguously Thai. |
| **Business Postmortems** (`UCTJDWGKcUKee7iXW2eXeUnA`) | English archive + AIVDO showcase. Correctly US-classified; McDonald's and Patagonia already public, Peloton unlisted and ready. |

No third channel.

This retires the stalled clean-channel test honestly — it answered its question, and gives Business Postmortems a second-order use instead of abandonment.

**Sequencing: unlist the English catalogue BEFORE the first Thai episode ships.** The first Thai upload is the strongest classification signal the channel will send, and it should land on a channel that reads unambiguously Thai rather than one still showing 30 English business videos. Ordering:

1. Unlist the 30 English long-form videos on `@disclosedch`
2. Rewrite channel display name + description in Thai (§5.3)
3. Ship Thai EP01

⚠️ **This is a prerequisite with a dependency:** bulk-unlisting needs a working YouTube token, and all three are dead (§9.1). Either the OAuth publishing-status fix lands first, or the unlisting is done by hand in Studio. It cannot be scripted until §9.1 is resolved.

**Follow-up:** AIVDO's README names `@disclosedch` as its showcase (McDonald's, BIC). Some of those videos were already unlisted during the June test. Showcase links repoint to Business Postmortems.

---

## 5. Format

### 5.1 Series identity

**Series tag: `Disclosed`** — Latin script, appended to Thai titles, with a persistent EP counter.

```
ทำไม TurboTax ฟรีถึงจ่าย 3,000 บาท? | Disclosed EP01
```

This is exactly the benchmark's structure: **Thai title + Latin series tag** (`... | Geek Story EP845`). `Disclosed` names a *stance* — what was hidden, revealed — not a subject, so it covers a Panasonic postmortem, an iPhone market shift, and a time-traveller hoax equally.

**Growth structure:** ด.ดล Blog runs multiple series under one channel (Geek Story EP845 / Geek Talk EP249 / Geek Monday EP337), each with its own counter. Start with one counter. Split into `Disclosed Story` (curiosity/mystery) and `Disclosed Case` (business postmortems) once volume justifies it.

### 5.2 Explicit rule reversal

`CLAUDE.md` currently says **avoid numeric-suffix titles.** That rule is hereby **reversed for this channel.**

It was written to prevent spammy template-farming. But a persistent EP number is a franchise signal, not a spam signal, and it is what the channel that wins this niche in Thai actually does. Reversed deliberately and in writing rather than quietly contradicted.

### 5.3 Scope

**Tech + business + curiosity.** Explicitly wider than business case studies. Matching the benchmark's range is what makes daily cadence survivable — twenty back-catalog slugs and a business-only research lane runs dry by week six.

It also moves the audience closer to AIVDO's buyer: a Thai tech-curious viewer is a plausible customer; a pure business-history viewer is less so.

**Channel identity is rewritten to match** — the old *"business case studies built on what's actually in the filings"* is now too narrow.

| Field | Value |
|---|---|
| Display name | `Disclosed — เรื่องที่ไม่มีใครบอก` |
| Description | `เล่าเรื่องธุรกิจ เทคโนโลยี และเรื่องที่คุณสงสัยมาตลอด — จากเอกสารและแหล่งข้อมูลต้นทางจริง คลิปใหม่ทุกวัน` |

Bilingual by design, mirroring §5.1: the **channel** carries Thai, the **series tag** stays Latin — the ด.ดล Blog structure. The Thai half ("the story nobody tells") is broad enough to cover tech, business and mystery without naming a category, and it is the one place Thai keywords can be placed for free.

The description does three jobs: states the widened scope, keeps the primary-source differentiator the editorial gate exists to defend, and promises the cadence.

Changed by hand in Studio — it is a channel setting, not an API operation in the pipeline.

### 5.4 Production constants

| Constant | Value | Note |
|---|---|---|
| Runtime | 15–20 min | up from 8 |
| Title formula | `ทำไม X ถึง Y?` question-paradox | Ports 1:1 from existing English titles; matches benchmark's top performers |
| Voice | **`th-TH-Chirp3-HD-Achernar` (female) — locked, permanent** | AIVDO defaults to `th-TH` and auto-agrees Thai particles to voice gender (`e2775e9`), so narration uses **ค่ะ**, never ครับ. Voice consistency is a franchise asset across hundreds of episodes; do not change it once episodes ship. **Algieba is retired.** |
| Subscribe CTA in narration | Retained | The one conversion unlock that empirically held (v4.6.3) |
| Thumbnail | Text-as-hero, Thai, **burned in by the renderer** | Never by the image model — see §6 |
| Cadence | ~1/day, 7 days | Routine A currently runs weekdays only |

### 5.5 Voice and register

Narration is **Thai TTS** via AIVDO's native path. Already in place:

- `language_code` defaults to `th-TH`
- **Voice locked: `th-TH-Chirp3-HD-Achernar` (female)**
- Thai particles auto-agree to voice gender (`e2775e9` — *"a woman no longer says ครับ"*), so every episode closes in **ค่ะ**. Script review checks this rather than assuming it.
- Thai speaking rate corrected (`2382bea` — the prior guess was +72% wrong)

**The register rule — the biggest quality risk in this design.**

The benchmark channel is narrated by a real person. We are TTS. The audible tell, however, will not be the voice — Chirp3-HD is good — it will be the **script register**.

Thai splits hard between written and spoken register. A literal translation of English documentary prose yields stiff, formal, written-register Thai that sounds synthetic through even a perfect voice. This risk lands hardest on Phase 1, whose episodes *are* translations.

**Rule: Thai scripts are written in spoken register, not translated from English.**

Practically, a remake takes the English script as a *source of verified facts and structure*, then is written fresh in spoken Thai — not rendered sentence-by-sentence. Register review is part of the Remake gate (§8), alongside translation fidelity.

Precedent: the channel has been caught on AI-detection twice in English (a narration complaint, then a complaint that the *reply* to it was also AI-written). Thai raises the stakes because the audience is native and the owner can hear the problem directly — which also makes it fixable in a way it never was in English.

---

## 6. Pipeline changes

| Change | Where | Size |
|---|---|---|
| **2 parts → 4–5 parts** for 15–20 min | `render.py:257` `main()` hardcodes `p1`/`p2` and `stitch([p1, p2], ...)`. Glob `REQUEST_PART_*.json` instead. `stitch()` and `render_part()` are **already N-generic**. | Small |
| **Gemini-only image routing** | `render.py:136` `cinematic_engines` is an OpenAI-only allowlist. AIVDO's `aivdo/modules/google_image.py` chain and Gemini-3 prices in `image_cost_table.py` already exist. | Small — routing, not new engineering |
| **Thai text burned by renderer** | Needs a Thai font in the burn-in path. AIVDO solved the analogous case with Noto CJK for JP/CN/KR subtitles (`f389b40`). | Medium |
| **`prompts/` ported to Thai** | The 17-prompt library is English-tuned throughout. | **Largest single item** |
| **Veo hook on Shorts only** + prompt guard | `make_short.py` + AIVDO's existing Veo lane | Medium |
| **Routine A: weekdays → 7 days** | Daily means Saturday and Sunday | Trivial |

### 6.1 Image generation — Gemini only, no OpenAI

**Default: `gemini-3.1-flash-image`** (stable, $0.067/image).

Chosen on evidence, not price. A same-prompt sweep across the whole available chain on a faceless cinematic documentary scene (2026-08-20; harness in `assets/imgcmp.py` + `assets/imgcmp_lite.py`, output below):

![scene comparison](assets/2026-08-20-compare_scene.jpg)


| Model | $/img | Scene verdict |
|---|---|---|
| **`gemini-3.1-flash-image`** | 0.067 | **Best.** Richest storytelling density — period CRT, stacked file boxes, corkboard, street through window, warm lamp against cold glass. |
| `gemini-3-pro-image` | 0.134 | Cleanest light modelling but sparser and emptier. More designed, less documentary. Not 2× better. |
| `gemini-3.1-flash-lite-image` | 0.0336 | Genuinely usable. Flatter light, less drama, correct period detail. |
| `gemini-2.5-flash-image` | 0.039 | **Worst.** Muddy, teal-crushed, no period specificity — and it is AIVDO's *current* chain head. |

Rationale for spending above lite: every video is also an AIVDO demo. Image quality is marketing, not only retention.

**Pin stable names, not `-preview`.** `gemini-3.1-flash-image`, `gemini-3-pro-image` and `gemini-3.1-flash-lite-image` all now exist without the suffix. Previews get deprecated.

**Replacement fallback chain** (see §6.5): `gemini-3.1-flash-image` → `gemini-3.1-flash-lite-image` → `gemini-3-pro-image`.

**Aspect ratio must be set by config, not prompt.** `gemini-3.1-flash-lite-image` ignored a 16:9 instruction in the prompt text and returned a letterboxed square.

### 6.2 Thai text is never generated by an image model

All Thai on-screen text — titles, callouts, thumbnails, subtitles — is burned in by the renderer with a proper Thai font.

**The rule stands, but its original rationale is obsolete.** `aivdo/config.py:153` (2026-06-27) records that *`gemini-3-pro-image-preview` renders Thai/CJK reliably, flash-image garbled it*, and commit `32ad47b` fixed `/omni` by banning Thai text in generated images outright.

A direct test on 2026-08-20 (headline required to read `ทำไมแว่นตาถึงแพง`) shows that comparison no longer holds:

![Thai text comparison](assets/2026-08-20-compare_thai.jpg)


| Model | Result |
|---|---|
| `gemini-2.5-flash-image` | **Garbled** — *ค่มหัศและเส้งเยก / ทำเพกักตากั้งฟยง* is nonsense. Rendered the English subtitle correctly and mangled the Thai. Matches the June comment exactly. |
| `gemini-3.1-flash-lite-image` | **Correct**, headline and body copy — from the cheapest model in the chain. |
| `gemini-3.1-flash-image` | **Correct**, headline plus three lines of body Thai. |
| `gemini-3-pro-image` | Headline correct, but **duplicated the line**, printing a malformed second copy beneath it. |

The June comment compared 2.5-flash against 3-pro. The entire 3.1 generation spells Thai, and pro was the only model with an artifact.

**So the rule is now justified by control, not capability:** franchise typography must be identical across hundreds of episodes, must use a chosen Thai typeface, and must not vary with model version or sampling luck. Generated Thai text is unrepeatable; renderer-burned Thai text is deterministic.

### 6.3 Motion: Veo for hooks, not bodies

| Element | Backend | Cost |
|---|---|---|
| Shorts hook, first 3–5s | Veo 3.1 | $1.20–2.00 |
| Identity-held motion (recurring subject) | Omni (`gemini-omni-flash-preview`) | per AIVDO preset |
| Body scenes | `zoom_pan` stills | image cost only |

A full 60s Short on Veo 3.1 is ~$24 ($9 on Fast) — not viable daily.

This pattern is already shipped and **measured** in AIVDO v1.58: hook inter-frame motion **2.944 across 0–3s** against **0.694 / 0.398 / 0.189** behind it.

**Two guards, both from prior findings:**

- **Veo prompt guard — no brand names, no named people, environment only.** The May Veo POC found brand-name prompts produced in-scene watermarks and unreliable faceless compliance. Both are fatal for a faceless channel doing brand postmortems.
- **Tail-drift caveat.** At 0.189, late scenes read noticeably more static than the opening. Acceptable across 60s; needs watching across 15–20 min.

### 6.4 The Thai speaking-rate trap

AIVDO commit `2382bea`: *"the Thai speaking rate was a GUESS and it was wrong by +72%."*

Script length must be scoped against the **corrected Thai rate**, never English words-per-minute. Getting this wrong lands every 15-minute target at ~25 minutes — a systematic error across every episode, discoverable only after rendering.

---

### 6.5 AIVDO's fallback chain is broken (pre-existing production bug)

Found while running the §6.1 sweep, on 2026-08-20:

```
imagen-4.0-fast-generate-001 → 404 NOT_FOUND
imagen-4.0-generate-001      → 404 NOT_FOUND
```

Neither Imagen model is available on the production API key. `DEFAULT_GOOGLE_CHAIN` in `aivdo/modules/google_image.py` is `gemini-2.5-flash-image` → `imagen-4.0-generate-001` → `imagen-4.0-fast-generate-001`, so **positions 2 and 3 are dead and the chain has no working fallback**. Any render whose head model fails, fails outright.

This is independent of the pivot — it affects AIVDO in production today. Fix scheduled in the implementation plan, not applied here: replace the chain with `gemini-3.1-flash-image` → `gemini-3.1-flash-lite-image` → `gemini-3-pro-image`, and update `image_cost_table.py`, which likewise knows only the `-preview` names.

## 7. Content plan

### 7.1 Phase 1 — Thai remakes of the proven catalog, daily

**Up to twenty published videos already have verified scripts, propagated corrections, and source checks.** A Thai remake needs a *translation-fidelity + register* check, not a fresh 17-prompt research cycle.

This is what resolves the tension between daily cadence and a real editorial gate.

⚠️ **The supply figure is unverified and load-bearing.** `pipeline.json` shows 20 published rows, but the disk holds 18 `Daily/` directories and only 2 `.facts_verified` markers — the earliest ships likely predate the `Daily/` convention and may have no local script to remake from. **First task of the implementation plan: inventory which published slugs are actually remake-able.** If the real number is 12 rather than 20, Phase 2 has to start sooner.

Ordering: grievance / *"why is X expensive"* first — double-validated as the benchmark's top performer **and** Disclosed's only hit. TurboTax, Ticketmaster, McDonald's, Costco gold bars, Amazon–Whole Foods lead.

Supply: ~20 episodes ≈ 3 weeks of daily shipping, **subject to the inventory above**.

### 7.2 Phase 2 — fresh Thai research lane, 2–3/week

Ramps behind Phase 1 as the catalog depletes. Draws on the widened scope (tech + business + curiosity), not business alone.

### 7.3 Shorts

**Daily**, cut from the prior day's long-form via `make_short.py`, with a Veo hook on the first 3–5s (§6.3) and the character-anchored injustice angle the existing Shorts pattern already uses. No pinned comment.

This means **two uploads per day** — one long-form, one Short. Both count toward the editorial-attention budget (§8), and the Short's ~10 minutes of work is additive to the long-form gate, not included in it.

The §11 Veo line (~30/month) assumes exactly this cadence.

### 7.4 Saturation audit — new target list

The audit previously ran against Modern MBA / Cold Fusion / Company Man. In Thai it runs against:

- ลงทุนแมน (Longtunman) — 824K subs, 2.5K videos
- The Secret Sauce
- Mission to the Moon
- **ด.ดล Blog's own 845+ episodes** — they have likely covered several candidate slugs already

Check happens **before** each ship.

---

## 8. Editorial gate v2 — three modes

A single gate cannot survive daily cadence plus the widened scope. It splits by slug type.

| Mode | Applies to | Discipline | Budget |
|---|---|---|---|
| **Remake** | Thai versions of the 20 verified English slugs | Translation fidelity (do numbers, names, dates survive intact) **+ spoken-register review** (§5.5) | ~15 min |
| **Research / verifiable** | New business + tech slugs with primary sources | Full `lint_urls.py` → REVIEW.md → `propagate_correction.py` | ~30–45 min |
| **Research / attribution** | Legends, hoaxes, unresolved claims (John Titor-type) | **Never assert — attribute.** Report accurately what was claimed and by whom. | ~20 min |

**Machine first pass.** AIVDO already carries `video_verifier_model: gemini-3-flash-preview`, a narration-grounding pass. Wiring it ahead of the human gate is the single highest-leverage change for making daily cadence survivable. It filters what reaches the human gate; it does not replace it.

**Unchanged:**

- `.facts_verified` still blocks render.
- **Comment replies stay hand-typed by the channel owner.** This came from a real incident where the audience caught an AI-written reply to an AI-detection complaint. Easier in Thai, not harder.

**Retired:** the `≤3 videos/week` cap. Its impression-rationing rationale was falsified by the project's own later data; its *editorial-attention* rationale was real, and the three-mode gate plus the machine first pass is what retires it. The cap is replaced by the gate, not simply dropped.

---

## 9. Infrastructure prerequisites (blocking)

1. **All three YouTube OAuth tokens are dead** (`invalid_grant` on `token.json`, `token_newchannel.json`, `token_disclosed.json`). More important than re-authing: **check the OAuth app's publishing status.** Testing-mode apps expire refresh tokens every 7 days, which matches the recurring `invalid_grant` pattern. At ≤3/week that was an annoyance; at daily cadence a weekly token death stops the channel. **Move the app to Production — do not just re-auth.**
2. **Analytics token** (`token_analytics.json`) likewise — without it the §10 day-14 checkpoint cannot be measured, and that checkpoint is the whole test.
3. **Thai font** available to the renderer burn-in path.

---

## 9.4 Critical path

§4 gives the ship ordering and §9 gives the blockers; combined they are one chain, not parallel chores:

```
OAuth app → Production   (unblocks every token)
        ↓
re-auth upload + analytics tokens
        ↓
unlist 30 English videos ──┐
        ↓                  │  fallback: unlist by hand in Studio,
rewrite channel identity ──┘  which decouples shipping from the OAuth fix
        ↓
ship Thai EP01
        ↓
day-14 routing checkpoint  (needs the analytics token)
```

**The fallback matters.** Hand-unlisting in Studio is tedious but unblocking — it means EP01 is not held hostage to a Google Cloud console task. The OAuth fix is still required before daily automated uploads, and before the day-14 checkpoint can be measured.

---

## 10. Measurement

Every episode ships with its own `utm_campaign`, flowing into the AIVDO attribution admin panel that landed in v1.57.

`pipeline.json` already carries the needed columns, unused since April: `utm_campaign`, `thumbnail_ctr_pct`, `views_7d`, `views_30d`, `aivdo_trials_attributed`.

### Day-14 routing checkpoint — hard gate

There is **no pre-pivot Thai performance data** — `Daily/` begins 2026-04-29, after the Thai→English flip. So the claim that @disclosedch's Thai classification is an *asset* rather than merely not-a-liability is **untested**. This checkpoint tests it.

| Result at day 14 | Action |
|---|---|
| Thai ships draw real Browse impression batches | Thai classification is an asset. Continue; ramp Phase 2. |
| Thai ships starve at 11–19 impressions, as the English ships did | The channel is poisoned for **any** language. Move to Business Postmortems or a fresh Thai channel. |

Pre-committed action, not a hope. Requires the analytics token (§9.2) and Studio screenshots (impressions are Studio-only).

---

## 11. Costs

At 15–20 min the scene count is ~64–80 images per video (up from 32 at the 8-minute format).

| Image model | $/img | Per video | Daily (30/mo) |
|---|---|---|---|
| `gemini-3.1-flash-lite-image` | 0.0336 | $2.15–2.69 | $65–81 |
| `gemini-2.5-flash-image` | 0.039 | $2.50–3.12 | $75–94 |
| **`gemini-3.1-flash-image` (chosen)** | **0.067** | **$4.29–5.36** | **$129–161** |
| `gemini-3-pro-image` | 0.134 | $8.58–10.72 | $257–322 |

Imagen 4 is absent from this table because it is **not available on the production key at all** (§6.5).

**Batch API halves every figure above** (a 1K image drops to ~$0.034 at the flash tier). Episodes are produced a day ahead of publication, so batch is compatible with the cadence — worth evaluating in the implementation plan, and it would bring the chosen tier to roughly **$65–80/mo**.

Plus Veo hooks on Shorts (~$1.20–2.00 each, ~$36–60/mo) and TTS.

**All-in ≈ $170–230/month** at the chosen tier.

### Sourcing caveats

- **Thai RPM figures in §2 are weakly sourced.** Searches returned thin and mutually inconsistent Thailand data; one result (฿216 per 1,000 views) is implausible and was discarded. The §2 conclusion holds across the entire plausible range, but no single RPM figure here should be treated as reliable.
- **Benchmark numbers in §3 were pulled 2026-08-20** and are a single-day snapshot of six videos, several still accruing views.
- **Gemini and Veo prices** are from public 2026 pricing pages, cross-checked against AIVDO's own `image_cost_table.py`. Veo pricing conflicts with the May 2026 POC note (~$2.80 for 56s); verify against live billing before committing to Shorts volume.

---

## 12. Decisions locked

| Decision | Value |
|---|---|
| Channel | Revive `@disclosedch` in Thai; Business Postmortems becomes English archive + showcase |
| Goal | $10K/mo **mixed** (ads + sponsorship + AIVDO), not AdSense-only |
| Primary KPI | `aivdo_trials_attributed` per video |
| Cadence | ~1/day long-form + 1/day Short, 7 days/week |
| Runtime | 15–20 min |
| Series tag | `Disclosed` + EP counter; lanes split later |
| Channel identity | `Disclosed — เรื่องที่ไม่มีใครบอก`, Thai description (§5.3) |
| Scope | Tech + business + curiosity |
| Images | Gemini only, default `gemini-3.1-flash-image` (stable) — chosen on a same-prompt sweep, §6.1 |
| Thai text | Never image-model generated; renderer burn-in only |
| Motion | Veo hook (3–5s) on Shorts only; Omni for identity-held; `zoom_pan` bodies |
| Voice | `th-TH-Chirp3-HD-Achernar` (female), locked permanently |
| Sequencing | Unlist English catalogue → rewrite channel identity in Thai → ship EP01 |
| Editorial gate | Three modes + machine first pass |
| Hard gate | Day-14 routing checkpoint |

## 13. Open items

- **AIVDO fallback-chain fix** (§6.5) — chain replacement + `image_cost_table.py` update scheduled for the implementation plan; **not applied yet**, and it is a live production bug meanwhile.
- **Batch API** (§11) — halves image cost and fits a day-ahead production rhythm. Evaluate during implementation.
- **Stale documentation.** This spec supersedes `CLAUDE.md`'s distribution model, slug-selection heuristic, `≤3/week` cap, Algieba voice, and 8-minute runtime — but `CLAUDE.md` is **not yet updated**, so those still read as current instructions. Several memory files are likewise superseded. Both are updated after this spec is approved: `CLAUDE.md` rewrite belongs in the implementation plan, and superseded memories get **marked superseded, not deleted** (they hold the audit trail for why the English run was abandoned).
