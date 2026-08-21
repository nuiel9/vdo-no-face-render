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
