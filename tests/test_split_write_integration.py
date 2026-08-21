"""Integration test for the split_script -> make_request_parts seam.

This seam had no direct test before: split_script.py and make_request_parts.py
were each unit-tested in isolation, and nothing exercised them back-to-back.
That gap is exactly how the write_parts bug survived two rounds of review --
write_parts used to take total_seconds and derive per_part = total_seconds /
len(part_texts), a number with NO guaranteed relationship to the part_seconds
value split_into_parts actually packed against. Splitting the real #57
TurboTax script at part_seconds=240 produced parts of 2,885 and 2,766 chars;
handing write_parts the resulting total (523.6s) computed per_part=174.5s and
a 2,248-char ceiling that rejected both of them. write_parts now takes
part_seconds directly (see its docstring), and this test locks the seam so
the two stages can't drift apart again.

Uses Thai filler text deliberately -- chars_for_duration/duration_for_chars
are calibrated for Thai speech density, and applying them to English (as the
one real SCRIPT.txt on disk is) is what produced the 3-parts-vs-2 confusion
documented in task-2-report.md. A synthetic Thai script keeps this test
honest about what the budget math actually models.
"""
import json

from make_request_parts import _MAX_CHARS_PER_SECOND, write_parts
from split_script import split_into_parts


def _thai_script(num_scenes: int = 16, filler_chars: int = 380) -> str:
    """A multi-scene Thai script sized to force more than one part at the
    240s default -- exercising the real multi-part path, not the trivial
    single-part case."""
    return "# realistic thai script\n\n" + "".join(
        f"[Scene {i} | medium] s\nOVERLAYS: none\n{'ก' * filler_chars}\n\n"
        for i in range(1, num_scenes + 1)
    )


def test_every_written_part_fits_its_own_build_request_ceiling(tmp_path):
    part_seconds = 240.0
    script = _thai_script()

    parts = split_into_parts(script, part_seconds=part_seconds)
    assert len(parts) > 1  # otherwise this never touches the seam that broke

    # This must not raise -- the whole point of the fix. Before it, this line
    # threw ValueError on the equivalent real-script split (see docstring).
    write_parts(tmp_path, parts, part_seconds=part_seconds)

    request_files = sorted(tmp_path.glob("REQUEST_PART_*.json"))
    assert len(request_files) == len(parts)

    ceiling = int(part_seconds * _MAX_CHARS_PER_SECOND)
    for path in request_files:
        payload = json.loads(path.read_text())
        assert len(payload["text"]) <= ceiling
