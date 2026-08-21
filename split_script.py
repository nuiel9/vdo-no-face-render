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
import sys
from pathlib import Path

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


if __name__ == "__main__":
    # The split_into_parts -> write_parts chain was previously joined only
    # inside tests/test_split_write_integration.py -- no non-test caller
    # existed. Rendering a real slug raised FileNotFoundError: no
    # REQUEST_PART_*.json files, because nothing turned SCRIPT.txt into
    # them. This is that glue, callable directly: read a slug directory's
    # SCRIPT.txt, split it, and write REQUEST_PART_N.json for render.py's
    # discover_parts to find.
    from make_request_parts import write_parts

    if len(sys.argv) != 2:
        sys.stderr.write("usage: python3 split_script.py <slug_dir>\n")
        sys.exit(2)

    slug_dir = Path(sys.argv[1]).resolve()
    script_path = slug_dir / "SCRIPT.txt"
    if not script_path.exists():
        sys.stderr.write(f"no SCRIPT.txt in {slug_dir}\n")
        sys.exit(2)

    script_text = script_path.read_text(encoding="utf-8")
    parts = split_into_parts(script_text)
    write_parts(slug_dir, parts)
    print(f"{slug_dir}: wrote {len(parts)} REQUEST_PART_*.json file(s) from {script_path.name}")
