import pytest

from make_request_parts import (
    _MAX_CHARS_PER_SECOND,
    _SERVER_COMPRESSION_RATE,
    build_request,
    write_parts,
)


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
    # Derived from the guard's own ceiling, never hardcoded -- a literal
    # would stop testing the real boundary the moment the ceiling moves.
    threshold = int(240 * _MAX_CHARS_PER_SECOND)
    text = "ก" * threshold
    req = build_request(text, seconds=240)
    assert req["text"] == text


def test_overshoot_boundary_just_over_raises():
    threshold = int(240 * _MAX_CHARS_PER_SECOND)
    text = "ก" * (threshold + 1)
    with pytest.raises(ValueError, match="too long"):
        build_request(text, seconds=240)


def test_guard_ceiling_is_genuinely_below_aivdos_server_side_trigger():
    # AIVDO silently LLM-compresses any script whose estimated speech exceeds
    # target_duration * 1.2 at scene_planner's measured 11.3 chars/sec for
    # speaking_style "normal" -- a real ceiling of 13.56 chars/sec. Crossing it
    # rewrites a fact-checked script with no error.
    #
    # The margin is asserted, not just the inequality. An earlier version
    # checked only "client < server" and would have passed at 13.55 vs 13.56 --
    # which is what the guard had silently decayed to before this was caught.
    assert _SERVER_COMPRESSION_RATE == pytest.approx(13.56, abs=0.01)
    assert _MAX_CHARS_PER_SECOND < _SERVER_COMPRESSION_RATE
    margin = (_SERVER_COMPRESSION_RATE - _MAX_CHARS_PER_SECOND) / _SERVER_COMPRESSION_RATE
    assert margin >= 0.03, f"guard margin decayed to {margin:.1%}"


def test_guard_ceiling_is_independent_of_our_budget_constants():
    # The regression this file exists to prevent: the ceiling used to be
    # derived from RATES, so measuring a new rate silently eroded the margin.
    # Changing RATES must not move the ceiling at all.
    import make_request_parts
    import thai_budget

    before = make_request_parts._MAX_CHARS_PER_SECOND
    original = thai_budget.RATES["mixed"]
    try:
        thai_budget.RATES["mixed"] = 99.0
        assert make_request_parts._MAX_CHARS_PER_SECOND == before
    finally:
        thai_budget.RATES["mixed"] = original


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


def test_images_only_is_true():
    # False routes every part to the Veo motion lane (~150 credits/part)
    # instead of the still-image lane (~15 credits/part). Every shipped
    # English request used True; owner decision 2026-08-20 sets it True
    # here too.
    req = build_request("สวัสดีค่ะ", seconds=240)
    assert req["images_only"] is True


def test_music_mood_resolves_to_a_real_track_selector():
    # "documentary" is not a key in AIVDO's MOOD_DEFAULTS -- resolve_track
    # would return None and the render would silently ship with no music,
    # unannounced. "none" is the explicit no-BGM path.
    req = build_request("สวัสดีค่ะ", seconds=240)
    assert req["music_mood"] == "none"


def test_write_parts_rejects_empty_list(tmp_path):
    with pytest.raises(ValueError, match="empty"):
        write_parts(tmp_path, [], part_seconds=240)


def test_write_parts_clears_stale_parts_from_a_shorter_previous_episode(tmp_path):
    # A folder that previously held a 5-part episode, now being overwritten
    # with a 3-part one, must not leave REQUEST_PART_4/5.json behind --
    # render.py's discover_parts would see a contiguous 1..5 and stitch two
    # parts of the PREVIOUS episode's narration into the new final video.
    for n in range(1, 6):
        (tmp_path / f"REQUEST_PART_{n}.json").write_text("{}")

    parts = ["บทที่หนึ่ง", "บทที่สอง", "บทที่สาม"]
    write_parts(tmp_path, parts, part_seconds=120)

    remaining = sorted(p.name for p in tmp_path.glob("REQUEST_PART_*.json"))
    assert remaining == ["REQUEST_PART_1.json", "REQUEST_PART_2.json", "REQUEST_PART_3.json"]


def test_write_parts_writes_correct_files(tmp_path):
    parts = ["สวัสดีค่ะ ตอนที่หนึ่ง", "สวัสดีค่ะ ตอนที่สอง"]
    write_parts(tmp_path, parts, part_seconds=240)

    part1 = tmp_path / "REQUEST_PART_1.json"
    part2 = tmp_path / "REQUEST_PART_2.json"
    assert part1.exists()
    assert part2.exists()

    import json

    payload1 = json.loads(part1.read_text())
    assert payload1["text"] == parts[0]
    assert payload1["custom_seconds"] == 240  # part_seconds, taken directly -- no division
    assert payload1["voice_name"] == "Erinome"

    payload2 = json.loads(part2.read_text())
    assert payload2["text"] == parts[1]
    assert payload2["custom_seconds"] == 240
