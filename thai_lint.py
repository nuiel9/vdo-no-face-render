"""Register and length checks for a Thai episode script.

The editorial gate catches wrong facts. This catches a script that is
factually right and still wrong to ship: sentence-final particles that
contradict the configured narrator's gender (make_request_parts.NARRATOR_GENDER),
punctuation the channel banned, an untranslated passage, an unfilled
placeholder (`[...]` scaffolding or a TODO/TBD/XXX/FIXME marker) left in
narration for TTS to read aloud, or a part long enough that AIVDO silently
rewrites it.

Deliberately NOT a style judge. It flags what is mechanically checkable and
leaves taste to the human gate.

Implementation note: content checks (particle, dashes, Thai-presence) run
per SCENE via `split_script.parse_scenes`, not per PART. `split_into_parts`
merges scenes into a part up to the character budget, so an untranslated
scene can end up sharing a part with a scene that does have Thai narration
-- checking at part granularity would let that untranslated scene hide
behind its neighbor. Presence checks (ครับ / em dash / --) would survive
merging either way, but scene-level keeps all four checks consistent and
lets a flagged problem point at the same scene number the human sees in
SCRIPT.txt.

The length check still needs `split_into_parts`, because the render-request
ceiling is a property of the assembled part, not any single scene. As
currently implemented, `split_into_parts` raises ValueError itself when a
single scene is too big to fit any part at the requested `part_seconds` --
that's the case this module's own test suite exercises for "too long".
That ValueError is converted into a lint problem here rather than left to
propagate, so a caller always gets a problem list back instead of having to
catch an exception from a different module.
"""
import re
import sys
from pathlib import Path

import make_request_parts
from make_request_parts import _MAX_CHARS_PER_SECOND
from split_script import parse_scenes, split_into_parts

_THAI = re.compile(r"[฀-๿]")

# Both particle families. Which one is a PROBLEM depends on
# make_request_parts.NARRATOR_GENDER -- read at call time (not imported by
# value) so a test can monkeypatch NARRATOR_GENDER and see lint_script's
# behaviour flip with it. See _particle_rule below.
_MALE_PARTICLE = re.compile(r"ครับ")            # covers ครับ and นะครับ
# ค่ะ|คะ covers ค่ะ and นะคะ (the particle), but bare คะ also occurs INSIDE
# ordinary words -- คะแนน (score/points, e.g. a Geekbench or credit-score
# number, likely on a tech/business channel), คะเน (estimate/guess), คะน้า
# (kale), คะนอง (reckless/thunder). A blanket "not followed by any Thai
# character" lookahead was considered and rejected: Thai has no mandatory
# word-boundary space, so a particle can legitimately run straight into the
# next clause with no separator (e.g. "ไหมคะว่า...", a real pattern this
# module's own former test fixture used) -- excluding every following-
# consonant case would have created false NEGATIVES, silently letting a
# genuinely wrong-gender script pass. Excluding by the specific known
# false-positive WORDS instead keeps the check narrow and safe in the
# direction that matters (see module docstring: this stays a mechanical
# check, not a full Thai tokenizer).
_FEMALE_PARTICLE = re.compile(r"ค่ะ|คะ(?!แนน|เน|น้า|นอง)")
# parse_scenes matches [Scene N | energy] only at the start of a stripped
# line and consumes it before narration accumulates -- see its docstring
# and the _SCENE regex in split_script.py. That means every legitimate
# scene marker is gone by the time lint_script ever sees narration text.
# Any [ or ] that survives into narration is therefore never a scene
# marker -- it is leftover authoring scaffolding (an unfilled caveat slot,
# a bracketed TODO) that TTS would read aloud verbatim, brackets included.
_PLACEHOLDER_BRACKET = re.compile(r"[\[\]]")
_PLACEHOLDER_WORD = re.compile(r"\b(?:TODO|TBD|XXX|FIXME)\b", re.IGNORECASE)


def _particle_rule() -> tuple[re.Pattern, str, str]:
    """Return (pattern-to-flag, flagged-label, expected-label) for the
    CURRENTLY configured narrator gender.

    Reads make_request_parts.NARRATOR_GENDER fresh on every call, not at
    import time, so this stays correct if the narrator changes again and so
    tests can monkeypatch NARRATOR_GENDER and observe the rule flip.
    """
    gender = make_request_parts.NARRATOR_GENDER
    if gender == "male":
        return _FEMALE_PARTICLE, "ค่ะ / นะคะ", "ครับ"
    if gender == "female":
        return _MALE_PARTICLE, "ครับ / นะครับ", "ค่ะ / นะคะ"
    raise ValueError(f"unknown NARRATOR_GENDER: {gender!r}")


def lint_script(script: str, part_seconds: float = 240.0) -> list[str]:
    """Return human-readable problems. Empty list means clean."""
    problems: list[str] = []

    wrong_particle, wrong_label, expected_label = _particle_rule()
    narrator_voice = make_request_parts.NARRATOR_VOICE
    narrator_gender = make_request_parts.NARRATOR_GENDER

    # Register/content checks: per scene, before any part-merging can hide
    # one scene's problem behind another scene's clean narration.
    for i, (_, narration) in enumerate(parse_scenes(script), 1):
        if not narration:
            continue
        if wrong_particle.search(narration):
            problems.append(
                f"scene {i}: contains {wrong_label}, but the narrator "
                f"{narrator_voice} is {narrator_gender} — use {expected_label}"
            )
        if "—" in narration:
            problems.append(f"scene {i}: contains an em dash, banned in channel voice")
        if "--" in narration:
            problems.append(f"scene {i}: contains '--', banned in channel voice")
        if not _THAI.search(narration):
            problems.append(f"scene {i}: contains no Thai characters — untranslated?")
        if _PLACEHOLDER_BRACKET.search(narration):
            problems.append(
                f"scene {i}: contains [ or ] in spoken narration -- every "
                "legitimate [Scene N | energy] marker is already stripped by "
                "parse_scenes before this check runs, so this is an unfilled "
                "placeholder (e.g. a caveat slot) that TTS would read aloud"
            )
        if _PLACEHOLDER_WORD.search(narration):
            problems.append(
                f"scene {i}: contains a TODO/TBD/XXX/FIXME placeholder marker "
                "left in spoken narration"
            )

    # Length check: needs the assembled parts, since the render-request
    # ceiling applies to a part, not a lone scene. split_into_parts raises
    # ValueError when a scene can't fit any part at this part_seconds --
    # that IS a "too long to ship" finding, so it becomes a problem instead
    # of an uncaught exception.
    try:
        parts = split_into_parts(script, part_seconds)
    except ValueError as exc:
        problems.append(
            f"script is too long to split at {part_seconds:.0f}s/part: {exc} "
            "— AIVDO would silently compress and rewrite a fact-checked script"
        )
        return problems

    ceiling = int(part_seconds * _MAX_CHARS_PER_SECOND)
    for i, part in enumerate(parts, 1):
        if len(part) > ceiling:
            problems.append(
                f"part {i}: {len(part):,} chars exceeds {ceiling:,} — AIVDO will "
                "silently compress and rewrite a fact-checked script"
            )
    return problems


if __name__ == "__main__":
    # A pure module invoked as `python3 thai_lint.py <script>` used to print
    # nothing and exit 0 whether the script was clean or broken — silence
    # read as a pass. This block exists so the gate flow documented in
    # prompts/prompts_v3_th.md and CLAUDE.md has something real to run:
    # exit 0 with an explicit "clean" line on success, exit 1 with every
    # problem printed on failure. Silence must never be the success signal.
    if len(sys.argv) != 2:
        sys.stderr.write("usage: python3 thai_lint.py <SCRIPT.txt>\n")
        sys.exit(2)

    script_path = Path(sys.argv[1])
    problems = lint_script(script_path.read_text(encoding="utf-8"))

    if problems:
        print(f"thai_lint: {len(problems)} problem(s) in {script_path}:")
        for p in problems:
            print(f"  - {p}")
        print("\nDO NOT commit .facts_verified until these are resolved.")
        sys.exit(1)

    print(f"thai_lint: clean — {script_path}")
    sys.exit(0)
