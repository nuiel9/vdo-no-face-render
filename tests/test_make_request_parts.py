import pytest

from make_request_parts import build_request


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
