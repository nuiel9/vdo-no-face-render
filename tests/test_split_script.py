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


def _big_script(num_scenes: int = 12, filler_chars: int = 900) -> str:
    """A script whose scenes are large enough to force more than one part.

    Each scene's narration is made unique (a per-scene suffix, not just
    repeated filler) deliberately: an earlier fixture used identical text
    for every scene, which let a packer bug that truncates one scene hide
    behind another scene's byte-for-byte-identical, intact copy. Uniqueness
    is what makes "this exact narration appears whole in exactly one part"
    an assertion that can actually fail.
    """
    return "# t\n\n" + "".join(
        f"[Scene {i} | medium] s\nOVERLAYS: none\n{'ก' * filler_chars}-scene{i:02d}\n\n"
        for i in range(1, num_scenes + 1)
    )


def test_long_script_splits_into_multiple_parts():
    # This is the only fixture in the suite that forces split_into_parts to
    # emit more than one part -- so it is the only place that can actually
    # observe a straddled scene. A prior version of the no-straddle
    # assertion lived in its own test against the module-level SCRIPT
    # fixture (~70 narration chars against a ~2,956 char budget), which
    # always produced exactly one part; that test could not fail no matter
    # how badly the packer mangled scenes crossing a boundary, and a
    # reviewer confirmed it: mutating split_into_parts to truncate a scene
    # mid-pack left all tests, including that one, green.
    big = _big_script()
    scenes = parse_scenes(big)
    parts = split_into_parts(big, part_seconds=240.0)
    assert len(parts) > 1

    # Parts render as independent jobs, so a scene split across two parts
    # would be cut mid-thought with a hard join in the middle. Assert each
    # scene's narration survives whole, and lands in exactly one part.
    for _, narration in scenes:
        matches = [p for p in parts if narration in p]
        assert len(matches) == 1, narration


def test_every_part_fits_the_request_guard():
    # The whole point: a part this produces must not be rejected by
    # build_request, and must not trip AIVDO's silent compression.
    from make_request_parts import _MAX_CHARS_PER_SECOND

    big = _big_script()
    for part in split_into_parts(big, part_seconds=240.0):
        assert len(part) <= int(240.0 * _MAX_CHARS_PER_SECOND)
