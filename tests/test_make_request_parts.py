import pytest

from make_request_parts import _OVERSHOOT_TOLERANCE, build_request, write_parts
from thai_budget import chars_for_duration


def test_narrator_is_erinome_not_algieba():
    req = build_request("สวัสดีค่ะ", seconds=240)
    assert req["voice_name"] == "Erinome"


def test_language_is_thai():
    req = build_request("สวัสดีค่ะ", seconds=240)
    assert req["language"] == "th-TH"


def test_speaking_style_is_normal():
    # normal is what keeps per-scene energy tags available (spec §6.4);
    # a global style would forfeit them.
    req = build_request("สวัสดีค่ะ", seconds=240)
    assert req["speaking_style"] == "normal"


def test_routes_to_the_gemini_lane():
    req = build_request("สวัสดีค่ะ", seconds=240)
    assert req["render_mode"] == "fast"
    assert req["video_intent"] == "faceless_youtube"


def test_carries_the_narration_text():
    req = build_request("ทำไมแว่นตาถึงแพง", seconds=240)
    assert req["text"] == "ทำไมแว่นตาถึงแพง"


def test_rejects_empty_text():
    with pytest.raises(ValueError, match="empty"):
        build_request("", seconds=240)


def test_warns_when_script_badly_overshoots_its_slot():
    # A part whose script cannot fit its target is the +72% bug in miniature:
    # the render succeeds and the episode is simply the wrong length.
    long_text = "ก" * 20_000
    with pytest.raises(ValueError, match="too long"):
        build_request(long_text, seconds=240)


def test_overshoot_boundary_just_under_does_not_raise():
    # Derived from the real budget + tolerance, not hardcoded -- a
    # hardcoded 3960/3961 would silently stop testing the real boundary
    # the moment RATES or _OVERSHOOT_TOLERANCE changes.
    budget = chars_for_duration(240, "figures")
    threshold = int(budget * _OVERSHOOT_TOLERANCE)
    text = "ก" * threshold
    req = build_request(text, seconds=240)
    assert req["text"] == text


def test_overshoot_boundary_just_over_raises():
    budget = chars_for_duration(240, "figures")
    threshold = int(budget * _OVERSHOOT_TOLERANCE)
    text = "ก" * (threshold + 1)
    with pytest.raises(ValueError, match="too long"):
        build_request(text, seconds=240)


def test_duration_preset_is_custom():
    # GenerateRequest.duration_preset defaults to "standard" (AIVDO
    # web.py:461), and VideoConfig.apply_preset only honours
    # custom_duration_seconds when preset == CUSTOM (AIVDO config.py:347-363).
    # Without this field, custom_seconds is silently discarded server-side.
    req = build_request("สวัสดีค่ะ", seconds=240)
    assert req["duration_preset"] == "custom"


def test_custom_seconds_matches_target():
    req = build_request("สวัสดีค่ะ", seconds=240)
    assert req["custom_seconds"] == 240


def test_write_parts_rejects_empty_list(tmp_path):
    with pytest.raises(ValueError, match="empty"):
        write_parts(tmp_path, [], total_seconds=240)


def test_write_parts_writes_correct_files(tmp_path):
    parts = ["สวัสดีค่ะ ตอนที่หนึ่ง", "สวัสดีค่ะ ตอนที่สอง"]
    write_parts(tmp_path, parts, total_seconds=480)

    part1 = tmp_path / "REQUEST_PART_1.json"
    part2 = tmp_path / "REQUEST_PART_2.json"
    assert part1.exists()
    assert part2.exists()

    import json

    payload1 = json.loads(part1.read_text())
    assert payload1["text"] == parts[0]
    assert payload1["custom_seconds"] == 240  # 480s / 2 parts
    assert payload1["voice_name"] == "Erinome"

    payload2 = json.loads(part2.read_text())
    assert payload2["text"] == parts[1]
    assert payload2["custom_seconds"] == 240
