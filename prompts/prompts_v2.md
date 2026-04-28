# Prompt Library V2 — Faceless YouTube × AIVDO

17 Claude prompts for running a faceless channel where **AIVDO is your production stack**. Copy-paste into Claude Pro. Every prompt assumes you own the video tool — no references to Solo.ai / Kling / ElevenLabs retail pricing.

Updated: 2026-04-23 — Prompts 4 and 5 revised for V3.1 **Path B** (10-12 min = 2 × AIVDO `standard` jobs, stitched locally). Earlier prompts (2, 3, 6–17) unchanged.

---

## 1. Title & Thumbnail Framework Decoder

```
You are a YouTube strategist for a Business Case Studies faceless channel.

Here are the top 10 performing video titles from our niche in the last 90 days:
{paste titles}

Decode them into:
1. Framework patterns (curiosity gap, number, proper-noun hook, contrarian)
2. Emotional register (awe, outrage, vindication, nostalgia)
3. Thumbnail visual cues implied by the title
4. The ONE rhetorical device doing the heavy lift

Return a 2-column table: Title → Framework. End with the 3 framework slots we have NOT used this month.
```

---

## 2. Topic Angling — Contrarian Angles

```
Topic: {paste raw topic, e.g., "Kodak's decline"}

Generate 7 contrarian or lesser-known angles that a diligent analyst could defend with at least 3 primary sources. 

For each angle:
- 1-sentence thesis
- Strongest public source (SEC filing, archived interview, book chapter)
- Why the mainstream narrative is wrong or incomplete
- Which AIVDO template best fits (Rise and Fall, Hidden Truth, Pitch Deck, Product-pip, or Story)

Flag any angle that relies only on secondary reporting — we will not ship those.
```

---

## 3. Lesser-Known Facts — Primary-Source Hints

```
Topic: {paste topic}

List 12 lesser-known, documented facts. For each:
- The fact (1 sentence)
- Where it's documented (book, SEC filing, court record, archive URL pattern)
- Why it was buried or overlooked
- A 5-word "hook phrase" for the on-screen lower-third

Do NOT speculate. If fewer than 12 are verifiable, return fewer and explain the gap.
```

---

## 4. Script with POV — Path B (two-part, 10-12 min total) *(V3.1)*

```
Write a 10-12 minute faceless YouTube script on: {topic}.

Strategy context: this script is rendered as TWO AIVDO `standard` jobs (≈5.5 min each), then stitched locally. Your output must therefore split cleanly at the halfway point with a single `===PART_BREAK===` marker on its own line. Each half must work standalone for a viewer who momentarily tunes out.

Structure (internal planning only — do NOT include these as headers in output):
- 0:00-0:20 presenter hook, first-person opinion (Part 1)
- 0:20-1:30 thesis + 3 stakes (Part 1)
- Part 1 body: 2-3 chapters, each with a named primary source on-screen
- `===PART_BREAK===` at a natural cliffhanger/transition ("but here's what most people miss…")
- Part 2 body: 2-3 chapters, each with a named primary source on-screen
- Last 90s of Part 2: contrarian reframe + personal caveat ("I was wrong about X until I read Y")
- CTA mentions aivdo.ai once, naturally, in Part 2's sign-off ONLY

HOOK SCENE SPECIFICITY (REQUIRED for AIVDO v1.8 Cinematic — added 2026-04-26, English-only from 2026-04-27):
The 0:00-0:20 hook narration (in English) MUST contain ALL FOUR — and every fact MUST be REAL, fact-checked against a primary source:
  1. A specific named brand or location — REAL, verified against the source documents (NOT "plausibly real" — the AIVDO image generator renders plausible fabrications faithfully, which produces publication-blocking factual errors. e.g., "Theranos lab in Newark, California" is correct; placing it elsewhere without verification = fabrication)
  2. A specific year or time marker (1995, 2018) — verifiable against a filing, news archive, or company record
  3. A specific number (revenue, branches, customers, age, employees, market cap) — citation required in REVIEW.md
  4. At least one visual handle (building shape, street name, weather, era marker) — must match reality (Google Street View, archival photo, etc.)

Critical: the AIVDO server-side `faceless_youtube` editorial gate fires a warning if `acknowledged_no_editorial` is not set on the REQUEST. This gate exists EXACTLY to catch fabricated narration. Render flow:
  - Human writes narration with REAL specifics → records sources in REVIEW.md
  - Human fact-checks each "specific" → creates `.facts_verified` empty marker file in the slug folder
  - render.py sees the marker → sets `acknowledged_no_editorial: true` → server-side gate stays quiet
  - No marker → server warning fires in logs → reminds you the video still needs fact-check

Example contrast (test results 2026-04-26, illustrating fabrication risk):
  VAGUE (calm B-roll, no fabrication risk): "In 2010, a small grocery store opened somewhere in the city."
  SPECIFIC + FABRICATED (DO NOT SHIP): naming a real brand at a wrong location → image generator renders the fabricated combination faithfully → publication-blocking factual error
  SPECIFIC + REAL (Netflix-doc cinematic, ship-ready): use only details traceable to a primary source (10-K filings, court dockets, earnings transcripts, company press releases, archival news)

Same provider, same model, same cost. The visual lift is real — but it amplifies whatever facts the narration contains, true OR false. Fact-checking specificity is now the load-bearing editorial step.

The server-side hook punch-up (Lever 2, shipped 2026-04-26 in commit 0b10b5e) prepends cinematic-framing cues for `scene_role=hook` only when video_intent=faceless_youtube — so the more visual handles you give it, the more dramatic the establishing shot becomes. This makes the fact-check requirement non-negotiable.

Voice: confident analyst, English narration, no hype, no AI-era filler phrases. ≥2 direct quotes from primary sources (preserve exact wording from source). No numbered lists spoken aloud — use prose.

Return TWO deliverables:

═══ DELIVERABLE A: PLANNING SCRIPT (with timestamps) ═══
Full script with timestamp blocks [0:00 — 0:20], chapter headers, stage directions, "Named source on-screen:" lines. Include `===PART_BREAK===` on its own line at the midpoint.

═══ DELIVERABLE B: AIVDO-READY NARRATION ═══
Same script but cleaned for TTS. Include `===PART_BREAK===` on its own line between the two halves. Strict rules:
- NO timestamps, chapter headers, stage directions, "source on-screen" lines
- NO markdown (*italics*, **bold**, # headers)
- NO numbered/bulleted lists — convert to prose
- Replace em dashes (—) with commas or periods
- Introduce quotes naturally ("According to the filing…") instead of raw quotation marks
- Keep paragraph breaks (blank line between paragraphs) — AIVDO uses these as scene hints
- Keep parenthetical rhythm asides (e.g., "Read that again.")
- Target: 150-180 wpm (English narration). 10-12 min total → 1,500-2,100 words split ~50/50 (so 750-1,050 per part)
- End Part 2 with a single CTA sentence mentioning aivdo.ai once
- Do NOT say "subscribe", "like", or reference YouTube mechanics
```

---

## 4.5. Script Cleaner — Convert Any Script to AIVDO-Ready Text *(new)*

```
I have an existing script with timestamps, chapter headers, and stage directions.
I need to paste it into aivdo.ai — the text box expects clean narration only.

Script to clean:
{paste full script here}

Rules (apply ALL):
1. Remove all timestamps like [0:00 — 0:20], [15:30-16:00], etc.
2. Remove all chapter headers (### CHAPTER 1 —, ## Intro, etc.)
3. Remove all stage directions: "(presenter avatar on-screen)", "(cut to B-roll)", "*whisper*"
4. Remove "Named source on-screen:" lines — these are visual overlays, not spoken
5. Remove markdown: **bold**, *italic*, > quotes, # headers, bullet points
6. Replace em dashes (—) with commas for natural speech pacing
7. Remove references to YouTube mechanics: "subscribe", "like button", "description below"
8. Replace "click the link" / "link in description" with "visit aivdo.ai" if CTA retained
9. Keep paragraph breaks — AIVDO uses blank lines as scene hints
10. Preserve direct quotes but introduce them naturally ("According to the filing..." instead of just """)
11. Do NOT paraphrase or shorten — keep 100% of the factual content

Output format:
- Clean narration text only
- No preamble, no "Here is the cleaned script"
- Just the prose, ready to paste
- End with a final word count at the bottom like: "Word count: 2,847 words (≈16 min at 178 wpm)"
```

---

## 5. Scene Breakdown — VideoScript JSON per Part *(V3.1.1)*

```
Input: ONE half of the Path B script (either Part 1 or Part 2, split at `===PART_BREAK===`).

Output: a valid VideoScript JSON dict ready to drop into the `edited_script` field of AIVDO's POST /api/generate. Produce only the JSON — no prose before or after.

Schema (exact keys — AIVDO's Pydantic validator will reject extras):

{
  "title": "short working title for this part only",
  "description": "one-sentence summary of this part",
  "source_text": "<verbatim narration text of this part, with paragraph breaks>",
  "language": "en",
  "target_total_duration": 0,
  "scenes": [
    {
      "scene_number": 1,
      "title": "<INTERNAL label — not rendered if text_overlays is populated>",
      "target_duration": 0,
      "energy_level": "high" | "medium" | "low",
      "reference_image_id": null,
      "text_overlays": [
        "<viewer-facing broadcast lower-third caption, ≤6 words, data-dense>"
      ],
      "narration": {
        "text": "<the narration spoken during this scene — ONE paragraph from source_text>",
        "language": "en",
        "estimated_duration": 0
      },
      "visuals": [
        {
          "visual_type": "image",
          "prompt": "<cinematic visual prompt, specific lighting + camera angle + named subject. No text overlays, no faces unless the topic requires. Business Case Studies style.>",
          "description": "",
          "duration": 0,
          "zoom_pan": true
        }
      ]
    }
  ]
}

## Hard rules

**Duration (zero-config audio-driven pacing):**
- Set `scene.target_duration = 0` on every scene. AIVDO's composer uses `max(target_duration, audio_duration + 1s)` — with 0, pacing tracks the TTS audio exactly +1s padding. Never set a manual value, it causes dead-air at scene ends (confirmed at `video_composer.py:546`).
- Set `target_total_duration = 0` as well. AIVDO derives from preset.
- Set `narration.estimated_duration = 0`. AIVDO computes at TTS time.

**text_overlays (the visible captions):**
- MUST be populated, 1–3 entries per scene. This is what AIVDO renders as on-screen lower-third subtitles (`video_composer.py:593`).
- Keep each entry short: ≤6 words, data-dense. Good examples: `"$1.9B net loss · 2018"`, `"SoftBank Q3 FY2019"`, `"Next: Theranos"`, `"aivdo.ai"`.
- Bad examples: `"Hook: the $47B everyone remembers"`, `"Stake 1: S-1 revealed nothing new"` — these are editorial-planning labels, NOT viewer captions. Never ship them.
- Use Unicode middle-dot `·` for separators (tighter than `,` on a lower-third).
- Rule of thumb: if a viewer watching on mute can't tell what scene is about from the text_overlays, rewrite them.

**scene.title (internal only):**
- Still required by the schema but no longer visible when text_overlays is populated. Use it as your editorial planning label ("Hook", "Stake 1: S-1 new"). Future-proofing: if you ever clear text_overlays, AIVDO falls back to title — so keep title readable too, just in case.

**Narration:**
- `narration.text` drawn VERBATIM from source_text, no paraphrase. Every sentence in source_text appears in exactly one scene.

**Visuals:**
- All `visual_type = "image"` (we run images_only=true).
- `zoom_pan = true` on all scenes (Ken Burns pacing).
- AIVDO Template (passed separately as visual_style at request level) guides vocabulary: Rise and Fall → cinematic documentary; Hidden Truth → infographic with data viz; Pitch Deck → illustration / slide-like; News → broadcast-press style; Story → photojournalism.
- NO request for readable text in image prompts (subtitle layer handles it).
- NO generic face close-ups ("businessman in suit"). Named subjects OK (Neumann's silhouette), archival objects OK, always OK.

**Visual subject discipline (the hot-dog rule, 2026-04-28):**

Background: AIVDO's `render_mode=cinematic` + `video_intent=faceless_youtube` is currently leaking the topic's *anchor object* (the dominant noun in the hook — e.g. "hot dog" in a Costco-pricing topic, "pitch deck" in a WeWork topic, "blood vial" in a Theranos topic) into every per-scene image-engine call server-side. Without explicit defense, gpt-image-2 will insert the anchor object into chart scenes, boardroom scenes, factory scenes, and aerial scenes that didn't ask for it. Verified failure: 2026-04-28 Costco render had hot dogs in financial-dashboard, factory-aerial, and boardroom scenes despite clean per-scene prompts.

When generating each scene's `visuals[0].prompt`, follow these three rules:

1. **Anchor-recurrence cap**: identify the topic's anchor object (the hero subject of the hook). It may appear in AT MOST 30% of scenes — typically scene 1 (hook), the moment-it-lands beat (when the topic's defining number/quote/document is introduced), and the closing callback. All other scenes must have a different hero subject: data viz, archival document, factory aerial, boardroom, supply-chain cutaway, exterior establishing shot, magazine-cover macro, etc.

2. **Negative-prompt defense on non-anchor scenes**: every scene that does NOT feature the anchor must end its prompt with explicit exclusions, e.g.:
   - For a chart scene: `... NEGATIVE: no hot dog, no food, no Kirkland packaging, no consumable products visible.`
   - For a boardroom scene: `... NEGATIVE: no hot dog, no food on the table, no product placement.`
   - For a factory scene: `... NEGATIVE: no specific food product, no hot dogs, no sausages on the conveyor — generic packaging or unidentifiable goods.`
   The exclusion list always includes the topic anchor by name. Belt-and-suspenders against AIVDO's server-side topic leak until that's fixed.

3. **Single-frame discipline**: every prompt must end with `Single hero subject. One unified cinematic frame. No collage, no multi-panel layout, no grid composition, no magazine-style composite.` This is non-negotiable — gpt-image-2 in `cinematic` mode otherwise produces 2x2 / 5-panel grids that read as ads, not documentary.

**Structure:**
- Scene count: 14-18 per part.
- Scene 1 and last: `energy_level="high"`. Middle: "medium" with 1-2 "low" breathing beats.

## Workflow

Run this prompt TWICE per topic — once for Part 1, once for Part 2 — with matching visual vocabulary AND matching text_overlays typography so the stitched video feels continuous.
```

---

## 6. Title A/B Generator

```
Script summary: {paste}
Target RPM tier: {$8-19}

Generate:
- 7 title options, each ≤60 chars
- For each: predicted CTR tier (high/med/low) + WHY
- Pair each with a 1-line thumbnail concept
- Flag any title that violates YouTube policy (clickbait, unsubstantiated claim)

Return as a ranked table. Pick the winner and the best underdog for A/B.
```

---

## 7. Thumbnail Concept + Generation Prompt

```
Script: {paste}
Title: {paste chosen title}

Generate 3 thumbnail concepts:
1. Face/no-face composition
2. Primary subject + contrast element
3. Text overlay (≤4 words)
4. Color palette (3 hex codes)
5. AIVDO poster mode template hint OR "custom — send to designer"
6. Mobile legibility check (will text read at 320px?)

Pick the winning concept and write the AIVDO poster-mode prompt or the Canva/designer brief.
```

---

## 8. Description + Chapters + Citations

```
Script: {paste}
Title: {paste}
Channel slug: {e.g., "business-postmortems"}

Generate:
- 150-word description (first 2 lines hook, last line CTA with aivdo.ai UTM link)
- Full chapter list with timestamps
- Source citation block (4-7 sources with URLs)
- 10 hashtags (3 broad + 7 niche)
- UTM link: https://aivdo.ai/?utm_source=youtube&utm_medium=channel&utm_campaign={slug}&utm_content={video-id}

Flag any source that is paywalled and suggest a free mirror.

ALWAYS append this trademark / no-affiliation disclaimer block at the very end of the description, verbatim, after the citations and hashtags:

---
Disclosed is independent commentary and analysis. No affiliation with the companies discussed. All trademarks, logos, and brand assets shown are property of their respective owners and are used for identification, commentary, and educational purposes under nominative fair use.
---

This block is non-negotiable on every video. Do not paraphrase, shorten, or move it.
```

---

## 9. Retention-Killer Audit — Weekly Retro

```
Here are my last 4 videos with retention graphs pasted as text (timestamp, % retained):
{paste data}

Identify:
- The 2 biggest retention drops across all videos
- Common structural issue (intro too long, chapter boundary weak, B-roll dead-spot)
- Specific 30-second fixes per issue
- 2 experiments to run next video

Don't tell me "improve the hook" — be specific about what to change.
```

---

## 10. Human-Fingerprint Line-Rewrite

```
Rewrite the following script passage to sound more like a human analyst with opinion. Remove any AI-tell phrases. Inject:
- One unexpected word choice or metaphor
- One personal caveat or memory
- One specific number that the reader will remember

Keep the factual claims unchanged. Keep length within 10%.

Passage:
{paste}
```

---

## 11. Competitor Gap-Finder

```
Competitor channels: {paste 3-5 channel URLs or names}
My niche: {e.g., Business Case Studies, English}

For each competitor:
- Top 3 topics in last 90 days
- Their upload cadence
- Average video length
- Their visual signature (what stays constant)

Then identify:
- 5 topics they have NOT covered
- 2 topics they covered badly (weak sourcing, shallow)
- 1 format they can't easily copy because it requires AIVDO-specific features (presenter avatar, product-pip, driving-video motion)
```

---

## 12. Monthly Revenue Diagnostics

```
Paste my monthly YouTube Studio + Stripe data:
- Views: {}
- Watch hours: {}
- RPM: {}
- Top 5 videos by revenue: {}
- AIVDO trial signups attributed by UTM: {}
- AIVDO MRR delta this month: {}

Diagnose:
- Is the channel on track for $10K/mo blended (ad + AIVDO MRR)?
- Which videos are driving AIVDO signups per 1k views?
- Which videos have high ad RPM but low AIVDO conversion?
- What 2 experiments for next month?

Return as a 1-page summary + one recommended format test.
```

---

## 13. Second-Channel Niche Scoring (Phase 4)

```
We're considering a second channel. Score these candidates for a channel owner who:
- Already owns AIVDO (aivdo.ai)
- Has Thai + English TTS capability (particles auto-matched)
- Wants both ad revenue AND AIVDO demo surface
- Can commit 2 videos/week max

Candidates: {paste}

Score each on:
1. RPM ceiling (1-10)
2. Policy risk (1-10, reverse)
3. AIVDO showcase fit (1-10)
4. Audience overlap with primary channel (1-10, reverse — we want low overlap)
5. Ramp speed (1-10)

Rank. Recommend 1 primary and 1 backup.
```

---

## 14. Sponsorship Pitch Email

```
Draft a sponsorship pitch to {brand name} for a Business Case Studies channel with:
- Subscribers: {}
- Avg views/video: {}
- Audience demo: {}
- CPM tier: {}

Include:
- 2-sentence opener that demonstrates we studied them
- The exact integration format (60s pre-roll script outline)
- Proof points (top 3 video metrics)
- Pricing: $X per integration, 2-slot minimum
- A mention that we produce with our own proprietary video stack (AIVDO), giving us faster turnaround than typical channels — 5 business days from brief to publish

Close with a request for a 15-min call. ≤180 words total.
```

---

## 15. Tool-Failure Fallback Switch

```
Production incident:
- Tool that broke: {e.g., AIVDO presenter-service / Cloud Run quota / Gemini TTS}
- How many videos affected: {}
- Deadline: {}

Give me:
- The fastest fallback within AIVDO (e.g., SadTalker legacy path for lip-sync, local MuseTalk)
- What external tool I could use as backup (name, cost, signup URL) — but only if AIVDO internal fallback would take > 2 hours
- The exact 5-step recovery procedure
- What to update in the pipeline xlsx when done
```

---

## 16. AIVDO Showcase Video Script Generator *(new in V2)*

```
We need a monthly "stunt" video that doubles as an AIVDO demo and drives trial signups.

Constraints:
- Must finish in under 90 minutes of our time (script → export)
- Must use at least 2 AIVDO features competitors don't have:
  [ ] EchoMimic V2 full-body avatar
  [ ] Product-pip / product-popup layout
  [ ] Thai-first TTS with gender particles
  [ ] Driving-video motion template
  [ ] 63-template library (name one that fits)
- Must be framed as a result, not a tutorial ("I remade this $10M ad" NOT "how to use AIVDO")
- Must have a CTA in the first 30s that's organic, not promo-read

Topic candidate: {paste or ask me}

Deliver:
- 3 script concepts, each 60-90s
- For each: AIVDO features used, expected view count tier, friction points for viewers to copy
- Pick one and write the full 90-second script with timestamps
```

---

## 17. Feature-Highlight Short for TikTok/Shorts *(new in V2)*

```
Turn this AIVDO feature into a 30-60 second vertical short for TikTok + YouTube Shorts:

Feature: {e.g., product-pip layout, Thai gender-particle TTS, EchoMimic V2 full-body avatar}

Format:
- Hook (0-3s): the surprising claim or visual result
- Demo (3-35s): showing the feature in action with split-screen before/after if relevant
- Punchline / CTA (35-60s): where to try it + one friction-reducing line ("no credit card")

Constraints:
- Vertical (9:16) aspect ratio
- Captions on-screen (AIVDO subtitle layer)
- At most 6 cuts — viewer should not feel rushed
- Single sentence CTA: "Free at aivdo.ai"

Return: script + shot list + the AIVDO template to start from.
```

---

## How to use this library

1. **Daily workflow (Mon-Fri):** Prompt 2 → 3 → 4 (Path B two-part) → 5 (run twice, once per part) → 6 → 7 → 8. Then the `aivdo-daily-production-pipeline` skill wraps each Part 5 output into a `/api/generate` request and invokes `aivdo-render` to submit + stitch.
2. **No manual paste into AIVDO anymore.** V3.1 drives the API directly. If you're running a one-off manually, Prompt 4.5 still produces AIVDO-ready text for the web UI.
3. **Weekly retro (Sun):** Prompt 9 + 11
4. **Monthly retro (1st):** Prompt 12 (phased target — see aivdo-monthly-revenue-diagnostics for Cold Start / Mid-roll Unlock / Scale phases)
5. **Stunt / demo month (once):** Prompt 16 or 17 — these stay at ~90s and use a single `short` AIVDO job, no Path B needed.
6. **Incident response:** Prompt 15
7. **Growth:** Prompt 13 (quarterly), Prompt 14 (when subs > 10k)

Keep prompts 16 and 17 in rotation — they are the only two whose output directly drives AIVDO MRR, which is the thing you cannot replicate with any competitor stack.

---

## AIVDO-Ready Output Checklist

When any prompt's output will be pasted into aivdo.ai, the text MUST:

- ✅ Be plain prose (no markdown, no tables, no bullets)
- ✅ Have no timestamps or scene markers
- ✅ Have no stage directions in parentheses
- ✅ Have no "source on-screen" labels (those are visual, not spoken)
- ✅ Use commas and periods instead of em dashes
- ✅ Keep paragraph breaks (blank lines) for scene boundaries
- ✅ Mention aivdo.ai at most once, naturally, in the final paragraph
- ❌ NEVER include YouTube mechanics ("subscribe", "like", "description below")
