"""Register and length checks for a Thai episode script.

The editorial gate catches wrong facts. This catches a script that is
factually right and still wrong to ship: male particles under a female
narrator, punctuation the channel banned, an untranslated passage, or a part
long enough that AIVDO silently rewrites it.

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

from make_request_parts import _MAX_CHARS_PER_SECOND
from split_script import parse_scenes, split_into_parts

_THAI = re.compile(r"[฀-๿]")
_MALE_PARTICLE = re.compile(r"ครับ")


def lint_script(script: str, part_seconds: float = 240.0) -> list[str]:
    """Return human-readable problems. Empty list means clean."""
    problems: list[str] = []

    # Register/content checks: per scene, before any part-merging can hide
    # one scene's problem behind another scene's clean narration.
    for i, (_, narration) in enumerate(parse_scenes(script), 1):
        if not narration:
            continue
        if _MALE_PARTICLE.search(narration):
            problems.append(
                f"scene {i}: contains ครับ, but the narrator Erinome is female "
                "— use ค่ะ / นะคะ"
            )
        if "—" in narration:
            problems.append(f"scene {i}: contains an em dash, banned in channel voice")
        if "--" in narration:
            problems.append(f"scene {i}: contains '--', banned in channel voice")
        if not _THAI.search(narration):
            problems.append(f"scene {i}: contains no Thai characters — untranslated?")

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
