# Thai Script Production Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Produce a fact-verified Thai episode script that `render.py` can turn into a video — and the tooling that makes the next fifty repeatable.

**Architecture:** Plan 1 built the render path and stopped at a gap: `write_parts` consumes `list[str]` of part narration, and nothing produces it. This plan fills that gap end to end — a script splitter, a Thai register linter, a machine first-pass fact check, a rewritten prompt library, and one real EP01 script through the editorial gate.

**Tech Stack:** Python 3.13, pytest, `google-genai` (Gemini, via the key already in `~/AIVDO/.env`). **No AIVDO commits** — every change is channel-side.

**Spec:** `docs/superpowers/specs/2026-08-20-thai-pivot-design.md` (approved 2026-08-20, amended through 2026-08-21)
**Predecessor:** `docs/superpowers/plans/2026-08-20-thai-render-pipeline.md` (merged, deployed)

## Global Constraints

- **Narrator:** `Erinome`, female, `normal` style, per-request. Narration closes in **ค่ะ**, never ครับ.
- **The `text` field carries narration ONLY.** Verified against the shipped request: `[Scene N | high]`, `OVERLAYS:` and energy tags are stripped before the request is built. Scene markers are authoring metadata, not a channel-to-server signal.
- **Per-part target ≈ 240 seconds**, derived from shipped evidence (3,294 and 3,172 chars rendering at 4:03 and 3:49), not invented.
- **Script length obeys `make_request_parts._MAX_CHARS_PER_SECOND`** (12.88 c/s). Above AIVDO's 13.56 c/s trigger it silently LLM-compresses a fact-checked script.
- **`.facts_verified` gates render.** No exceptions, no `acknowledged_no_editorial` without it.
- **Rigour must not cost digestibility** (§5.5, ย่อยง่าย). Both are checked.
- **No em dashes or double hyphens** in narration — existing channel voice rule.

## ⚠️ Decision required before Task 6

**Which lane is EP01?** §7.2 says Lane A (news) leads, and §7.4 confirms it is the only lane with supply. But a news episode has a shelf life of days, and shipping is still gated on user-owned work with no timeline — OAuth console fix, unlisting 30 videos, channel rename (all Plan 3).

**A news episode produced now can rot before the channel can receive it.**

Recommendation: **EP01 = evergreen tech topic in documentary form.** It decouples production from the user-gated track and does not contradict §7.2, which governs steady-state share rather than the first ship. **EP02 becomes the first live Lane A run**, which is also the only honest way to measure the news-cycle wall clock §7.5 flags as the riskiest untested assumption.

**DECIDED 2026-08-21: EP01 is Lane A — a current AI/tech news story.** The owner chose news over the evergreen recommendation, having seen the shelf-life tradeoff stated.

**Consequence, and it is now the critical path:** a news episode decays in days, so the owner-gated work — OAuth publishing-status fix, re-auth, unlisting the 30 English videos, channel rename — is no longer "whenever". If that track is not ready within roughly a week of the script being finished, EP01 rots and we learn nothing about the news cycle either. Task 6 must pick a topic with the longest defensible shelf life inside Lane A (a developing situation, not a single-day story).

---

## File Structure

| File | Responsibility |
|---|---|
| `CLAUDE.md` (rewrite) | Project context. Currently contradicts the approved spec in seven places. |
| `split_script.py` (create) | `SCRIPT.txt` → balanced part narration. Scene-boundary splits only. |
| `thai_lint.py` (create) | Thai register + budget checks on a script |
| `machine_check.py` (create) | Gemini-backed first-pass fact screen ahead of the human gate |
| `prompts/prompts_v3_th.md` (create) | Thai prompt library, authored against the spec |
| `tests/test_split_script.py`, `tests/test_thai_lint.py` (create) | Unit coverage |

---

### Task 1: Rewrite CLAUDE.md

**This is first because everything after it is judgment work.** Plan 1's implementers were safe from a stale `CLAUDE.md` because their briefs contained verbatim code. Plan 2's tasks require an implementer to reason about the channel — and today `CLAUDE.md` tells them the wrong thing in seven places.

**Files:** Modify `CLAUDE.md`

**Interfaces:** Consumes nothing. Produces the project context every later task reads.

- [ ] **Step 1: Read both documents in full**

Read `CLAUDE.md` and `docs/superpowers/specs/2026-08-20-thai-pivot-design.md`. The spec's header says it supersedes `CLAUDE.md`'s distribution model; the list below is what actually conflicts.

- [ ] **Step 2: Correct each superseded claim**

| `CLAUDE.md` currently says | Truth |
|---|---|
| American-cultural-touchstone distribution model; Tier A/B/C ranking; "#40 Tupperware ships next" | Superseded by spec §7. That model was for an English channel that no longer exists. The Tier labels actively **mis-rank** slugs for Thai — Blackberry was Tier C for reading "foreign-tech" to a US audience, when BBM was widespread in Thailand. |
| "Avoid numeric-suffix titles" | **Reversed** by §5.2. Episodes carry a persistent EP counter, like the benchmark channel. |
| Voice: Algieba | Algieba is **male**. Voice is `Erinome`, female, `normal` style (§5.4). |
| Render mode: AIVDO Cinematic + gpt-image-2, ~$1.32/video | `render_mode="fast"`, Gemini-only chain (§6.1). |
| 8-minute runtime, two parts | Lane A 8–10 min, Lane B 15–20 min, 4–5 parts (§7.1). |
| Cadence ≤3 videos/week | Retired. Replaced by the four-mode editorial gate (§8). |
| **Drive is canonical for `Daily/<slug>/`** | **False and load-bearing.** Verified 2026-08-21: the vault holds two empty folders from the April dry run. The last ~16 ships wrote to local disk only. |

Keep what is still true: the editorial gate, the human-fingerprint checklist, the three-locations map (corrected), and the AIVDO relationship.

- [ ] **Step 3: Mark superseded memory files**

In `/Users/krainats/.claude/projects/-Users-krainats-vdo-no-face-render/memory/`, prepend a `**SUPERSEDED 2026-08-21 by docs/superpowers/specs/2026-08-20-thai-pivot-design.md**` line to the body of `feedback_browse_impression_rationing.md`, `feedback_hook_taxonomy_and_subscribe_unlock.md`, and `feedback_channel_rescue_metadata_2026_06_14.md`.

**Mark, do not delete.** They hold the audit trail for why the English run was abandoned, which is the evidence base for §1 and §2.1. Update the one-line hooks in `MEMORY.md` to say superseded.

- [ ] **Step 4: Verify no contradiction survives**

Run: `grep -niE "algieba|tier a|tier b|tier c|≤3|3 videos/week|cinematic|gpt-image|8-minute|numeric-suffix" CLAUDE.md`
Expected: every remaining hit is inside an explicitly historical section, not stated as current guidance. Report any hit you chose to keep and why.

- [ ] **Step 5: Commit**

```bash
git add CLAUDE.md
git commit -m "CLAUDE.md: align with the approved Thai spec

Seven claims contradicted the spec and would misdirect any agent doing
judgment work: the American distribution model and its Tier labels, the
numeric-suffix ban, Algieba as voice, cinematic/gpt-image-2 rendering,
8-minute two-part runtime, the 3/week cap, and Drive as canonical for
Daily/<slug>/ -- that last one verified false, the vault holds two empty
folders from April.

Superseded memories marked, not deleted; they carry the audit trail for
why the English run ended."
```

---

### Task 2: `split_script.py` — script to part narration

`write_parts(slug_dir, part_texts, total_seconds)` needs `part_texts`, and nothing produces it. Plan 1's Task 6 assumed hand-written `PART_*.txt` files.

**Files:** Create `split_script.py`, `tests/test_split_script.py`

**Interfaces:**
- Consumes: `thai_budget.chars_for_duration`
- Produces:
  - `parse_scenes(script: str) -> list[tuple[str, str]]` — `(energy, narration)` per scene, metadata stripped
  - `split_into_parts(script: str, part_seconds: float = 240.0) -> list[str]`

- [ ] **Step 1: Write the failing tests**

Create `tests/test_split_script.py`:

```python
import pytest

from split_script import parse_scenes, split_into_parts

SCRIPT = """# SCRIPT #99 — a test
# some header note

===== PART 1 =====

[Scene 1 | high] Hook
OVERLAYS: 'Free.' | Somehow: $90
สวัสดีค่ะ นี่คือประโยคแรก

[Scene 2 | medium] Thesis
OVERLAYS: none
นี่คือประโยคที่สอง และยาวกว่าเดิมนิดหน่อยค่ะ
"""


def test_strips_all_metadata_from_narration():
    scenes = parse_scenes(SCRIPT)
    joined = " ".join(n for _, n in scenes)
    for marker in ("#", "[Scene", "OVERLAYS:", "====="):
        assert marker not in joined


def test_captures_energy_per_scene():
    # Energy never reaches AIVDO (it is stripped from the request text), but
    # it is authoring signal and must survive parsing rather than be silently
    # discarded -- a future per-scene mechanism needs it.
    scenes = parse_scenes(SCRIPT)
    assert [e for e, _ in scenes] == ["high", "medium"]


def test_narration_is_preserved_verbatim():
    scenes = parse_scenes(SCRIPT)
    assert scenes[0][1] == "สวัสดีค่ะ นี่คือประโยคแรก"


def test_empty_script_raises():
    with pytest.raises(ValueError, match="no scenes"):
        parse_scenes("# just a header\n")


def test_split_never_straddles_a_scene():
    # Parts render as independent jobs, so a scene split across two parts
    # would be cut mid-thought with a hard join in the middle.
    scenes = parse_scenes(SCRIPT)
    parts = split_into_parts(SCRIPT, part_seconds=240.0)
    for _, narration in scenes:
        assert any(narration in p for p in parts), narration


def test_short_script_is_one_part():
    parts = split_into_parts(SCRIPT, part_seconds=240.0)
    assert len(parts) == 1


def test_a_single_scene_too_big_to_fit_raises():
    # Scenes are never split internally, so one oversized scene cannot be
    # placed at all. Fail here with a usable message rather than emitting a
    # part that build_request rejects several steps later.
    huge = "# t\n\n[Scene 1 | medium] s\nOVERLAYS: none\n" + "ก" * 9000 + "\n"
    with pytest.raises(ValueError, match="scene 1 alone"):
        split_into_parts(huge, part_seconds=240.0)


def test_long_script_splits_into_multiple_parts():
    big = "# t\n\n" + "".join(
        f"[Scene {i} | medium] s\nOVERLAYS: none\n{'ก' * 900}\n\n" for i in range(1, 13)
    )
    parts = split_into_parts(big, part_seconds=240.0)
    assert len(parts) > 1


def test_every_part_fits_the_request_guard():
    # The whole point: a part this produces must not be rejected by
    # build_request, and must not trip AIVDO's silent compression.
    from make_request_parts import _MAX_CHARS_PER_SECOND

    big = "# t\n\n" + "".join(
        f"[Scene {i} | medium] s\nOVERLAYS: none\n{'ก' * 900}\n\n" for i in range(1, 13)
    )
    for part in split_into_parts(big, part_seconds=240.0):
        assert len(part) <= int(240.0 * _MAX_CHARS_PER_SECOND)
```

- [ ] **Step 2: Run the tests and verify they fail**

Run: `python3 -m pytest tests/test_split_script.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'split_script'`

- [ ] **Step 3: Implement the module**

Create `split_script.py`:

```python
"""Turn a SCRIPT.txt into per-part narration for make_request_parts.write_parts.

The request's `text` field carries narration ONLY -- verified against the
shipped REQUEST_PART_1.json, where 3,294 chars of plain prose survived and
every [Scene N | high] marker, OVERLAYS: line and header comment was stripped.
This module reproduces that stripping deliberately rather than by accident.

Splitting happens on SCENE boundaries only. Parts render as independent AIVDO
jobs and are stitched afterwards, so a scene split across two parts would be
cut mid-thought with a hard join through the middle of it.

The 240s default per part comes from shipped evidence, not from a target:
parts of 3,294 and 3,172 chars rendered at 4:03 and 3:49.
"""
import re

from thai_budget import chars_for_duration

_SCENE = re.compile(r"^\[Scene\s+\d+\s*\|\s*(\w+)\]", re.MULTILINE)
_SKIP_PREFIXES = ("#", "OVERLAYS:", "=====")


def parse_scenes(script: str) -> list[tuple[str, str]]:
    """Return [(energy, narration)] per scene, all metadata stripped."""
    scenes: list[tuple[str, str]] = []
    energy: str | None = None
    buf: list[str] = []

    for line in script.splitlines():
        stripped = line.strip()
        match = _SCENE.match(stripped)
        if match:
            if energy is not None:
                scenes.append((energy, " ".join(buf).strip()))
            energy, buf = match.group(1), []
            continue
        if not stripped or stripped.startswith(_SKIP_PREFIXES):
            continue
        if energy is not None:
            buf.append(stripped)

    if energy is not None:
        scenes.append((energy, " ".join(buf).strip()))
    if not scenes:
        raise ValueError("no scenes found — expected [Scene N | energy] markers")
    return scenes


def split_into_parts(script: str, part_seconds: float = 240.0) -> list[str]:
    """Group scenes into parts, each within the budget for `part_seconds`."""
    budget = chars_for_duration(part_seconds)
    parts: list[str] = []
    cur: list[str] = []

    for index, (_, narration) in enumerate(parse_scenes(script), 1):
        if not narration:
            continue
        if len(narration) > budget:
            raise ValueError(
                f"scene {index} alone is {len(narration):,} chars against a "
                f"{budget:,} char budget for {part_seconds:.0f}s. Scenes are "
                "never split internally — shorten the scene in SCRIPT.txt."
            )
        candidate = " ".join(cur + [narration])
        if cur and len(candidate) > budget:
            parts.append(" ".join(cur))
            cur = [narration]
        else:
            cur.append(narration)
    if cur:
        parts.append(" ".join(cur))
    return parts
```

- [ ] **Step 4: Run the tests and verify they pass**

Run: `python3 -m pytest tests/ -v`
Expected: PASS — all previous tests plus 7 new.

- [ ] **Step 5: Verify against the one real script we have**

Run:

```bash
python3 -c "
from split_script import parse_scenes, split_into_parts
s = open('Daily/2026-06-15_57_turbotax-free-that-wasnt/SCRIPT.txt').read()
sc = parse_scenes(s)
print(f'{len(sc)} scenes, energies: {sorted({e for e,_ in sc})}')
parts = split_into_parts(s)
print(f'{len(parts)} parts: {[len(p) for p in parts]} chars')
print('shipped was 2 parts at 3,294 and 3,172 chars')
"
```

Expected: scenes parse, energies are real words (`high`/`medium`/`low`), and the part sizes land in the same ballpark as the shipped ones. **If the scene count is 0, the regex does not match the real format — fix the regex against the real file, not the test fixture.**

- [ ] **Step 6: Commit**

```bash
git add split_script.py tests/test_split_script.py
git commit -m "Add script splitter: SCRIPT.txt to per-part narration

write_parts consumes list[str] of part narration and nothing produced it;
Plan 1 Task 6 assumed hand-written PART_*.txt files.

Strips metadata deliberately, matching what the shipped request actually
sent -- narration only, every scene marker and overlay removed. Splits on
scene boundaries only, because parts render as independent jobs and a
straddled scene would be cut mid-thought. The 240s default is derived
from shipped evidence, not chosen."
```

---

### Task 3: `thai_lint.py` — register and budget checks

The editorial gate catches wrong facts. Nothing catches wrong *register* — and §5.5 says a literal English translation yields stiff written-register Thai that sounds synthetic through a perfect voice.

**Files:** Create `thai_lint.py`, `tests/test_thai_lint.py`

**Interfaces:**
- Consumes: `split_script.split_into_parts`, `make_request_parts._MAX_CHARS_PER_SECOND`
- Produces: `lint_script(script: str, part_seconds: float = 240.0) -> list[str]` — human-readable problems, empty when clean

- [ ] **Step 1: Write the failing tests**

Create `tests/test_thai_lint.py`:

```python
from thai_lint import lint_script

GOOD = """# ok
[Scene 1 | high] Hook
OVERLAYS: none
คุณเคยสงสัยไหมคะว่าทำไมราคาถึงแพงขนาดนี้

[Scene 2 | medium] Close
OVERLAYS: none
กดติดตาม Disclosed ไว้นะคะ เราปล่อยคลิปใหม่ทุกวันค่ะ
"""


def test_clean_script_has_no_problems():
    assert lint_script(GOOD) == []


def test_flags_male_particle_with_a_female_narrator():
    # The voice is Erinome (female). A ครับ close is the exact bug commit
    # e2775e9 fixed inside AIVDO, and it is audible.
    bad = GOOD.replace("ทุกวันค่ะ", "ทุกวันครับ")
    problems = lint_script(bad)
    assert any("ครับ" in p for p in problems)


def test_flags_em_dash():
    bad = GOOD.replace("ราคาถึงแพง", "ราคา—ถึงแพง")
    assert any("em dash" in p.lower() for p in lint_script(bad))


def test_flags_double_hyphen():
    bad = GOOD.replace("ราคาถึงแพง", "ราคา--ถึงแพง")
    assert any("--" in p for p in lint_script(bad))


def test_flags_a_part_that_would_be_silently_compressed():
    big = "# t\n\n" + "".join(
        f"[Scene {i} | medium] s\nOVERLAYS: none\n{'ก' * 4000}\n\n" for i in range(1, 3)
    )
    assert any("compress" in p.lower() or "too long" in p.lower()
               for p in lint_script(big, part_seconds=60.0))


def test_flags_narration_with_no_thai_at_all():
    # An untranslated script is the failure this exists to catch early.
    english = GOOD.replace("คุณเคยสงสัยไหมคะว่าทำไมราคาถึงแพงขนาดนี้",
                           "Have you ever wondered why the price is so high")
    assert any("thai" in p.lower() for p in lint_script(english))

```

- [ ] **Step 2: Run the tests and verify they fail**

Run: `python3 -m pytest tests/test_thai_lint.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'thai_lint'`

- [ ] **Step 3: Implement the linter**

Create `thai_lint.py`:

```python
"""Register and length checks for a Thai episode script.

The editorial gate catches wrong facts. This catches a script that is
factually right and still wrong to ship: male particles under a female
narrator, punctuation the channel banned, an untranslated passage, or a part
long enough that AIVDO silently rewrites it.

Deliberately NOT a style judge. It flags what is mechanically checkable and
leaves taste to the human gate.
"""
import re

from make_request_parts import _MAX_CHARS_PER_SECOND
from split_script import split_into_parts

_THAI = re.compile(r"[฀-๿]")
_MALE_PARTICLE = re.compile(r"ครับ")


def lint_script(script: str, part_seconds: float = 240.0) -> list[str]:
    """Return human-readable problems. Empty list means clean."""
    problems: list[str] = []
    parts = split_into_parts(script, part_seconds)
    ceiling = int(part_seconds * _MAX_CHARS_PER_SECOND)

    for i, part in enumerate(parts, 1):
        if _MALE_PARTICLE.search(part):
            problems.append(
                f"part {i}: contains ครับ, but the narrator Erinome is female "
                "— use ค่ะ / นะคะ"
            )
        if "—" in part:
            problems.append(f"part {i}: contains an em dash, banned in channel voice")
        if "--" in part:
            problems.append(f"part {i}: contains '--', banned in channel voice")
        if not _THAI.search(part):
            problems.append(f"part {i}: contains no Thai characters — untranslated?")
        if len(part) > ceiling:
            problems.append(
                f"part {i}: {len(part):,} chars exceeds {ceiling:,} — AIVDO will "
                "silently compress and rewrite a fact-checked script"
            )
    return problems
```

- [ ] **Step 4: Run the tests and verify they pass**

Run: `python3 -m pytest tests/ -v`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add thai_lint.py tests/test_thai_lint.py
git commit -m "Add Thai register linter

The editorial gate catches wrong facts. Nothing caught a script that is
factually right and still unshippable: ครับ under a female narrator (the
bug AIVDO's e2775e9 fixed, and audible), banned punctuation, an
untranslated passage, or a part long enough that AIVDO silently rewrites
it.

Mechanical checks only. Taste stays with the human gate."
```

---

### Task 4: `machine_check.py` — first-pass fact screen

§8 says the machine first pass is "the single highest-leverage change for making daily cadence survivable." It filters what reaches the human gate; it does not replace it.

**Files:** Create `machine_check.py`

**Interfaces:**
- Consumes: `split_script.parse_scenes`
- Produces: `screen_script(script: str) -> list[dict]` — claims flagged as needing a source, each `{"scene": int, "claim": str, "why": str}`

- [ ] **Step 1: Write the module**

Create `machine_check.py`:

```python
"""Machine first pass over a script, ahead of the human editorial gate.

Per spec §8 this FILTERS what reaches the human gate. It never replaces it,
and it never marks anything verified. Its only job is to surface checkable
claims -- numbers, dates, named entities, superlatives -- so the human spends
their time on the claims that carry risk instead of reading for them.

Runs channel-side against Gemini directly. AIVDO carries its own
video_verifier_model, but reaching it would mean a cross-repo dependency for
no gain -- the check needs no render.
"""
import json
import os
import pathlib

from google import genai
from google.genai import types

from split_script import parse_scenes

# Stable, not -preview: the spec's own §6.1 rule is "pin stable names,
# previews get deprecated". AIVDO uses gemini-3-flash-preview for its
# verifiers; that is their choice and out of scope here. Verified present on
# the production key 2026-08-21, alongside newer stable flash releases.
_MODEL = "gemini-3.6-flash"

_PROMPT = """You are screening a documentary narration script before a human fact-check.

List every factual claim that a careful editor would want a primary source for:
numbers, dates, named companies or people, superlatives ("first", "largest",
"only"), and causal claims about real events.

Do NOT verify anything. Do NOT guess whether a claim is true. Only surface
claims that carry risk if wrong, so the human checks those first.

Return JSON: a list of objects with keys "claim" (quote it verbatim from the
script) and "why" (a short phrase: what kind of claim it is).

Script scene:
"""


def _client() -> genai.Client:
    key = os.environ.get("GOOGLE_AI_API_KEY")
    if not key:
        env = pathlib.Path.home() / "AIVDO" / ".env"
        for line in env.read_text().splitlines():
            if line.startswith("GOOGLE_AI_API_KEY="):
                key = line.split("=", 1)[1].strip().strip('"').strip("'")
                break
    if not key:
        raise RuntimeError("GOOGLE_AI_API_KEY not set and not found in ~/AIVDO/.env")
    return genai.Client(api_key=key)


def screen_script(script: str) -> list[dict]:
    """Return claims worth a human fact-check, scene by scene."""
    client = _client()
    flagged: list[dict] = []

    for index, (_, narration) in enumerate(parse_scenes(script), 1):
        if not narration:
            continue
        resp = client.models.generate_content(
            model=_MODEL,
            contents=_PROMPT + narration,
            config=types.GenerateContentConfig(response_mime_type="application/json"),
        )
        try:
            for item in json.loads(resp.text):
                flagged.append({
                    "scene": index,
                    "claim": item.get("claim", ""),
                    "why": item.get("why", ""),
                })
        except (json.JSONDecodeError, TypeError):
            flagged.append({
                "scene": index,
                "claim": "(screen failed — check this scene by hand)",
                "why": "model returned unparseable output",
            })
    return flagged


if __name__ == "__main__":
    import sys

    text = pathlib.Path(sys.argv[1]).read_text(encoding="utf-8")
    rows = screen_script(text)
    print(f"{len(rows)} claim(s) flagged for human verification\n")
    for row in rows:
        print(f"  [scene {row['scene']}] {row['why']}: {row['claim'][:100]}")
```

- [ ] **Step 2: Verify it runs against the one real script**

Run: `python3 machine_check.py Daily/2026-06-15_57_turbotax-free-that-wasnt/SCRIPT.txt`

Expected: a list of flagged claims including the specific figures that script carries — the `$90` charge, `296,000` free filers, the `2002` IRS deal, and the FTC's "two-thirds" finding. **If it flags nothing, the screen is broken** — that script is dense with checkable numbers.

Note: the script is English. The screen is language-agnostic; verifying against it first is deliberate, because it is the only fact-verified script available.

- [ ] **Step 3: Confirm it does not claim to verify**

Read your own output. If any flagged row asserts a claim is true or false, the prompt has drifted from its job — fix the prompt. This tool surfaces; it never adjudicates.

- [ ] **Step 4: Commit**

```bash
git add machine_check.py
git commit -m "Add machine first-pass fact screen

Spec §8 calls this the highest-leverage change for surviving daily
cadence. It surfaces checkable claims -- numbers, dates, entities,
superlatives -- so the human gate spends its time on the risky ones
instead of reading to find them.

It never verifies and never marks anything checked. Channel-side against
Gemini directly; AIVDO has its own verifier but reaching it would add a
cross-repo dependency for no gain, since this needs no render."
```

---

### Task 5: Author `prompts/prompts_v3_th.md`

**This is a rewrite against the spec, not a translation.** `prompts_v2.md` encodes the retired model: two-part 10–12 minute English scripts, the American touchstone gate, second-channel scoring, one title formula. The spec needs prompts v2 has no equivalent for.

**Files:** Create `prompts/prompts_v3_th.md`

- [ ] **Step 1: Read the source material**

Read `prompts/prompts_v2.md` (for structure and the prompts still valid), and spec sections §5.1–5.5, §7.1–7.7, §8.

- [ ] **Step 2: Author the library**

It must cover, and v2 does not:

| Prompt | Requirement |
|---|---|
| Lane A news | 8–10 min, fast gate, current AI/tech events |
| Lane B documentary | 15–20 min, postmortems and curiosity, tech-weighted (§5.3) |
| Title generator | **Rotates the eleven formulas** in §5.4 — `ทำไม X ถึง Y?`, `ใครฆ่า X?`, `เกิดอะไรขึ้นกับ X?`, `อวสาน X`, `วาระสุดท้ายของ X?`, `จุดจบ X`, `หายนะ X!`, `เปิดแฟ้มคดี X`, `เจาะลึก X`, `ย้อนรอย X`, `X จะรอดมั๊ย?` — never letting one dominate a month |
| Script writer | Spoken-register Thai, **not translated English** (§5.5). Closes in ค่ะ. Character budget from `thai_budget.chars_for_duration`. ย่อยง่าย — rigour must not cost digestibility. |
| Saturation audit | Searches ด.ดล Blog's catalogue (`youtube.com/@mrtharadhol/search?query=…`), ลงทุนแมน, and Thai AI/tech creators, **before** each ship (§7.7). Treats "no match" as a **relevance signal, not an opening**. |
| Scene breakdown | Emits `[Scene N | energy]` markers `split_script.parse_scenes` can read |

Carry forward from v2, adapted to Thai: the em-dash ban, anti-filler rules, primary-source naming, the visual-subject discipline (no named people — the faceless rule), and the subscribe CTA close.

Drop: American touchstone gate, second-channel scoring, revenue diagnostics, the English script prompts.

- [ ] **Step 3: Verify the output is machine-readable**

Generate one short test script with the scene-breakdown prompt, then run:

```bash
python3 -c "
from split_script import parse_scenes
from thai_lint import lint_script
s = open('/tmp/test_script.txt').read()
print(f'{len(parse_scenes(s))} scenes parsed')
print('lint:', lint_script(s) or 'clean')
"
```

Expected: scenes parse and lint is clean. **If `parse_scenes` finds zero scenes, the prompt's output format does not match the splitter** — fix the prompt, not the splitter, since the splitter matches the shipped format.

- [ ] **Step 4: Commit**

```bash
git add prompts/prompts_v3_th.md
git commit -m "Add Thai prompt library v3

Authored against the approved spec rather than translated from v2, which
encodes the retired model: English two-part 10-12 min scripts, the
American touchstone gate, second-channel scoring, one title formula.

v3 adds what the spec needs and v2 has no prompt for: two lanes split by
recency, eleven rotated title formulas, spoken-register Thai closing in
ค่ะ, density-aware character budgets, and a saturation audit that
searches the benchmark channel's own catalogue and reads a no-match as a
relevance signal rather than an opening.

Output format verified against split_script.parse_scenes."
```

---

### Task 6: Produce EP01 and pass the editorial gate

**This task's test is the gate itself.** There are no pytest steps — the deliverable is a fact-verified script, and the check is `lint_urls.py` → REVIEW.md → sources → `.facts_verified`.

Per the project's own rule, **the executing agent does the fact-check** rather than handing a checklist back.

**Files:** Create `Daily/<ep01-slug>/SCRIPT.txt`, `REVIEW.md`, `.facts_verified`

- [ ] **Step 1: Confirm the lane decision**

Check the plan's ⚠️ block above and the owner's answer at approval. Do not pick the lane yourself.

- [ ] **Step 2: Produce a saturation-audited shortlist**

Using the v3 audit prompt, generate 5 candidate topics that pass §5.3's tech weighting. For each, search ด.ดล Blog, ลงทุนแมน and Thai AI/tech channels. Record hits **and** misses — a miss is a relevance signal (§7.7).

Present the shortlist with one `AskUserQuestion` for the pick. **Do not choose the topic unilaterally** — topic selection is the channel's editorial identity.

- [ ] **Step 3: Write the script**

Use the v3 script prompt. Target the chosen lane's runtime. Spoken register, ค่ะ close, subscribe CTA, cross-reference discipline per the human-fingerprint checklist.

- [ ] **Step 4: Run the machine first pass**

Run: `python3 machine_check.py Daily/<ep01-slug>/SCRIPT.txt`
Record every flagged claim in `REVIEW.md`.

- [ ] **Step 5: Run the linter**

Run: `python3 -c "from thai_lint import lint_script; print(lint_script(open('Daily/<ep01-slug>/SCRIPT.txt').read()) or 'clean')"`
Fix every problem. Do not proceed with a non-empty list.

- [ ] **Step 6: Do the human-gate fact check yourself**

For every claim the machine pass flagged, find a **primary source** — filing, court document, company statement, first-party report. Not a news summary of one. Record source URLs in `REVIEW.md` beside each claim.

Correct anything wrong with `propagate_correction.py`. If a claim cannot be sourced, **cut it** rather than softening it.

Run: `python3 lint_urls.py Daily/<ep01-slug>/`

- [ ] **Step 7: Verify the parts split cleanly**

Run:

```bash
python3 -c "
from split_script import split_into_parts
from make_request_parts import build_request
parts = split_into_parts(open('Daily/<ep01-slug>/SCRIPT.txt').read())
print(f'{len(parts)} parts: {[len(p) for p in parts]}')
for p in parts:
    build_request(p, seconds=240)
print('all parts accepted by build_request')
"
```

Expected: every part accepted. A `ValueError` here means the script overshoots — trim it now, not after a paid render.

- [ ] **Step 8: Mark verified and commit**

Only when every claim has a primary source recorded:

```bash
touch Daily/<ep01-slug>/.facts_verified
git add Daily/<ep01-slug>/
git commit -m "EP01 <slug>: script written and facts verified

Machine first pass flagged N claims; each carries a primary source in
REVIEW.md. Thai register lint clean. Splits into N parts, all accepted
by build_request."
```

**Do not render.** Rendering is Plan 1's Task 6, which resumes once this script exists — and it still needs the owner's go-ahead for the spend.

---

## Self-Review

**Spec coverage:**

| Spec item | Task |
|---|---|
| §13 stale `CLAUDE.md` and memories | Task 1 |
| §5.5 spoken register, ค่ะ | Tasks 3, 5 |
| §5.4 eleven title formulas | Task 5 |
| §6.4 character budgets | Tasks 2, 3 |
| §7.1 two lanes | Task 5 |
| §7.7 saturation audit, no-match-is-a-signal | Tasks 5, 6 |
| §8 four-mode gate, machine first pass | Tasks 4, 6 |
| Script → parts gap left by Plan 1 | Task 2 |

**Deliberately excluded:** `yt-dlp` caption recovery of the back-catalogue (recovered scripts need the Research gate anyway, so remakes lose their advantage); Shorts and Veo (Plan 4); OAuth, unlisting, channel identity, utm and the day-14 checkpoint (Plan 3); any AIVDO commit.

**Known gap:** Task 6 produces a script but cannot ship it. Publishing needs Plan 3's OAuth fix and channel identity work, which is owner-gated. That is deliberate — script production and channel operations are independent, and blocking one on the other would idle both.
