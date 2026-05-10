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
