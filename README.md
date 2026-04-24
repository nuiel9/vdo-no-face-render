# vdo-no-face-render

Companion repo for the [VDO No Face](https://github.com/nuiel9/AIVDO) faceless-YouTube production project. Holds the render driver + content pipeline + Claude prompt library consumed by two scheduled Claude Code agents:

- **Routine A**: daily 08:00 Bangkok. Script + submit. Picks next queued row, runs the 17-prompt flow, submits two AIVDO renders.
- **Routine B**: hourly. Poll + stitch + upload. Checks `queue/` on Google Drive, stitches completed jobs, uploads `final.mp4` to Drive.

## Layout

```
vdo-no-face-render/
├── README.md              # this file
├── pipeline.json          # 45-row content plan (exported from xlsx, 2026-04-24)
├── render.py              # submit + poll + download + stitch (reused for local too)
└── prompts/
    └── prompts_v2.md      # 17 Claude prompts (V3.1 Path B)
```

## Architecture

**Code** (static, in this repo): `render.py`, `prompts/`, `pipeline.json`.
**State** (mutable, in Google Drive under `My Drive/vdo-no-face/`):
```
My Drive/vdo-no-face/
├── secrets/prod.json       # {"AIVDO_URL": "...", "AIVDO_API_KEY": "..."}
├── pipeline.json           # mirror of this repo's pipeline; user edits here to trigger renders
├── queue/                  # Routine A writes submitted jobs here, Routine B deletes on success
│   └── row_NN_submitted.json
├── Daily/                  # per-video artifacts (script, REQUESTs, final.mp4)
│   └── YYYY-MM-DD_N_slug/
└── failed/                 # Routine B moves queue files here on hard failure
```

## Triggering a render

1. Open Drive → `vdo-no-face/pipeline.json`. Find the row you want to render.
2. Change that row's `script_status` from `"In Progress"` (or `"Planned"`) to `"queue_next"`.
3. Save. Next Routine A run (next weekday 08:00 Bangkok) will pick it up.
4. Routine A produces artifacts + submits to AIVDO + writes `queue/row_N_submitted.json`.
5. Routine B (hourly) detects completion, stitches, uploads to Drive, posts Slack.

## Local fallback

If the routines ever fail or you want to render locally, `render.py` still works standalone. Set `AIVDO_URL` + `AIVDO_API_KEY` in `~/.aivdo.env`, then:

```bash
python render.py <slug_folder_with_REQUEST_PART_{1,2}.json>
```

It will submit, poll, download, and stitch with the same `pace_to_narration` + `xfade` pipeline the routines use.

## Prompts

See `prompts/prompts_v2.md` — 17 Claude prompts that together produce every artifact in a `Daily/<slug>/` folder. The routines' prompts reference the relevant subset:
- Prompt 2: contrarian angles
- Prompt 3: lesser-known facts
- Prompt 4: script with `===PART_BREAK===`
- Prompt 5: scene breakdown (for each half)
- Prompt 7: thumbnail brief
- Prompt 8: YouTube description + chapters

## Related

- Service code: [nuiel9/AIVDO](https://github.com/nuiel9/AIVDO) (the text-to-video API backend)
- Editorial policy for this channel: faceless, business case studies, primary-source first ([[Pitch Deck Template Style]] in the wiki)
- Pace-to-narration fix shipped 2026-04-24 ([aivdo commit `5636ffb`](https://github.com/nuiel9/AIVDO/commit/5636ffb))
