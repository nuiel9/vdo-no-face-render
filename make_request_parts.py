"""Build AIVDO request payloads for a Thai Disclosed episode.

The shipped English requests carry voice_name="Algieba", language="en-US".
Algieba is MALE (AIVDO config.py:209) and the channel's narrator is now
Erinome, female, th-TH (spec §5.4). voice_name is a PER-REQUEST field --
AIVDO's TTSConfig default is product-wide and must not be touched.
"""
import json
from pathlib import Path

from thai_budget import chars_for_duration, duration_for_chars

# Tolerance before a part's script is treated as mis-sized. 25% is wide
# enough to absorb density variation between prose and figures, and tight
# enough to catch a script that will blow its runtime.
_OVERSHOOT_TOLERANCE = 1.25


def build_request(part_text: str, seconds: float) -> dict:
    """Return the AIVDO request payload for one part of a Thai episode."""
    if not part_text.strip():
        raise ValueError("part_text is empty")

    budget = chars_for_duration(seconds, "figures")
    if len(part_text) > budget * _OVERSHOOT_TOLERANCE:
        predicted = duration_for_chars(len(part_text), "figures")
        raise ValueError(
            f"script too long for its slot: {len(part_text):,} chars "
            f"predicts ~{predicted / 60:.1f} min against a "
            f"{seconds / 60:.1f} min target (budget {budget:,} chars)"
        )

    return {
        "text": part_text,
        "language": "th-TH",
        "voice_name": "Erinome",
        "speaking_style": "normal",
        "render_mode": "fast",
        "video_intent": "faceless_youtube",
        "strict_cinematic": False,
        "resolution": "1080p",
        "subtitles_enabled": True,
        "pace_to_narration": True,
        "custom_seconds": int(seconds),
        "images_only": False,
        "visual_style": "illustration",
        "watermark_mode": "none",
        "music_mood": "documentary",
        "presenter_mode": False,
    }


def write_parts(slug_dir: Path, part_texts: list[str], total_seconds: float) -> None:
    """Write REQUEST_PART_N.json for every part of an episode."""
    per_part = total_seconds / len(part_texts)
    for index, text in enumerate(part_texts, start=1):
        payload = build_request(text, per_part)
        dest = slug_dir / f"REQUEST_PART_{index}.json"
        dest.write_text(json.dumps(payload, ensure_ascii=False, indent=2))
        print(f"{dest.name}: {len(text):,} chars, ~{per_part / 60:.1f} min")
