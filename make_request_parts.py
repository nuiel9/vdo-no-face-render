"""Build AIVDO request payloads for a Thai Disclosed episode.

The shipped English requests carry voice_name="Algieba", language="en-US".
Algieba is MALE (AIVDO config.py:209) and the channel's narrator is now
Erinome, female, th-TH (spec §5.4). voice_name is a PER-REQUEST field --
AIVDO's TTSConfig default is product-wide and must not be touched.
"""
import json
from pathlib import Path

from thai_budget import chars_for_duration, duration_for_chars

# Density used for the pre-render script-length guard below. Exported as a
# constant (not inlined as a "figures"/"mixed" literal) so tests derive the
# guard's boundary from the same value the guard itself uses -- otherwise a
# future density change here silently stops being covered by those tests.
#
# See the _OVERSHOOT_TOLERANCE comment for why this is "mixed" and not
# "figures".
_GUARD_DENSITY = "mixed"

# Tolerance before a part's script is treated as mis-sized by THIS guard.
#
# This guard exists to catch a script before it reaches AIVDO at all. But
# AIVDO's own server-side guard (text_analyzer.needs_compression) SILENTLY
# LLM-compresses -- rewrites and shortens -- any script whose estimated
# speech exceeds target_duration * _LENGTH_TOLERANCE, where
# _LENGTH_TOLERANCE is 1.2 (text_analyzer.py) and the estimate uses
# scene_planner's measured 11.3 chars/sec for speaking_style "normal"
# (scene_planner.py). That's a real ceiling of 11.3 * 1.2 = 13.56 chars/sec
# of the target duration. If our guard's effective ceiling sits ABOVE that
# number, a script can pass clean here and still get silently rewritten
# server-side -- dropping narration from a fact-checked script with no
# error and nothing for lint_urls.py to catch.
#
# This guard's effective ceiling is RATES[_GUARD_DENSITY] * _OVERSHOOT_TOLERANCE
# chars/sec, and it must land BELOW 13.56. The original 1.25 with "figures"
# (13.2 c/s) gave 13.2 * 1.25 = 16.5 -- comfortably above the server's
# trigger, so this guard could never have caught the case it exists for.
# Switching only the density to "mixed" (12.2 c/s) is not enough by itself
# either: 12.2 * 1.25 = 15.25, still above 13.56 (in fact no RATES entry
# clears 13.56 at 1.25 -- even "prose" at 11.3 c/s gives 14.125). 1.10 is
# the loosest tolerance that clears it with "mixed": 12.2 * 1.10 = 13.42,
# a ~1% margin below the server's real number. If RATES or AIVDO's
# constants change, re-derive both _GUARD_DENSITY and this value rather
# than assuming the margin still holds.
_OVERSHOOT_TOLERANCE = 1.10


def build_request(part_text: str, seconds: float) -> dict:
    """Return the AIVDO request payload for one part of a Thai episode."""
    if not part_text.strip():
        raise ValueError("part_text is empty")

    budget = chars_for_duration(seconds, _GUARD_DENSITY)
    if len(part_text) > budget * _OVERSHOOT_TOLERANCE:
        predicted = duration_for_chars(len(part_text), _GUARD_DENSITY)
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
        # GenerateRequest.duration_preset defaults to "standard" (AIVDO
        # web.py:461), and VideoConfig.apply_preset assigns
        # custom_duration_seconds ONLY when preset == CUSTOM (AIVDO
        # config.py:347-363) -- "standard" resolves to a fixed 300/330/360s
        # range and silently discards custom_seconds. Setting "custom" here
        # makes the request internally coherent: the seconds we compute are
        # the seconds the server is told to honour. This is NOT a proven fix
        # for actual render duration -- the shipped English parts (preset
        # "standard", custom_seconds 0) rendered at 4:03 and 3:49, not the
        # 330s the standard preset implies, which points at
        # pace_to_narration=True dominating over the preset once full text
        # is supplied. Real runtime behaviour under preset "custom" is
        # unverified until measured against a full render.
        "duration_preset": "custom",
        "custom_seconds": int(seconds),
        # True, not False. False routes every part to the Veo motion lane
        # (~150 credits/part) instead of the still-image lane (~15
        # credits/part) -- ~10x cost for a channel spec (§ Veo POC,
        # 2026-05-11) that scopes Veo to Shorts hooks, not long-form
        # bodies, and separately recorded the faceless-prompt path as
        # unreliable. Every shipped English request used True; this was a
        # plan defect with no recorded rationale for the deviation. Owner
        # decision 2026-08-20: set True.
        "images_only": True,
        "visual_style": "illustration",
        "watermark_mode": "none",
        # "documentary" is not a key in AIVDO's music_library.MOOD_DEFAULTS
        # (upbeat/chill/dramatic/inspiring/playful) -- resolve_track()
        # returns None for an unrecognised mood and the render silently
        # ships with no background music. "none" is resolve_track's
        # explicit no-BGM path (not an accident of a missing key), and
        # matches what every shipped English request already used --
        # rather than guessing an untested mood for the Thai lane.
        "music_mood": "none",
        "presenter_mode": False,
    }


def write_parts(slug_dir: Path, part_texts: list[str], total_seconds: float) -> None:
    """Write REQUEST_PART_N.json for every part of an episode.

    Clears any REQUEST_PART_*.json already in slug_dir before writing.
    Without this, writing 3 parts over a folder that previously held 5
    leaves REQUEST_PART_4/5.json behind; discover_parts (render.py) then
    sees a contiguous 1..5 and stitches two parts of the PREVIOUS
    episode's narration into the new final video.

    All payloads are built (and validated by build_request's length guard)
    BEFORE any file is deleted or written, so a script that overshoots its
    slot raises before the folder is touched -- a folder left mid-write by
    a validation failure would be worse than the stale-file bug this fixes.
    """
    if not part_texts:
        raise ValueError("part_texts must not be empty")
    per_part = total_seconds / len(part_texts)
    payloads = [build_request(text, per_part) for text in part_texts]

    for stale in slug_dir.glob("REQUEST_PART_*.json"):
        stale.unlink()

    for index, (text, payload) in enumerate(zip(part_texts, payloads), start=1):
        dest = slug_dir / f"REQUEST_PART_{index}.json"
        dest.write_text(json.dumps(payload, ensure_ascii=False, indent=2))
        print(f"{dest.name}: {len(text):,} chars, ~{per_part / 60:.1f} min")
