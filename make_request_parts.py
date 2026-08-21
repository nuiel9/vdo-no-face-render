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
# The guard's ceiling is derived from AIVDO's OWN compression trigger, not
# from our budget constants.
#
# AIVDO silently LLM-compresses -- rewrites and shortens -- any script whose
# estimated speech exceeds target_duration * _LENGTH_TOLERANCE, where
# _LENGTH_TOLERANCE is 1.2 (text_analyzer.py) and the estimate uses
# scene_planner's measured 11.3 chars/sec for speaking_style "normal". That is
# a hard server ceiling of 13.56 chars/sec, and crossing it drops narration
# from a fact-checked script with no error and nothing for lint_urls.py to see.
_SERVER_COMPRESSION_RATE = 11.3 * 1.2  # 13.56 chars/sec

# Reject at 95% of the server's trigger.
#
# An earlier version derived this ceiling as RATES["mixed"] * 1.10, tuned to
# land ~1% under 13.56. That coupling was fragile in a way that bit
# immediately: when RATES["mixed"] was replaced by a MEASURED 12.32 (was an
# estimated 12.2), the same 1.10 produced 13.55 -- a 0.06% margin. The guard
# had quietly stopped guarding, and nothing failed to say so.
#
# Deriving from _SERVER_COMPRESSION_RATE instead means our own budget
# constants can move freely without eroding the margin. The two numbers answer
# different questions and should not share a source: RATES says how much to
# WRITE, this says what gets REJECTED.
_SAFETY_MARGIN = 0.95
_MAX_CHARS_PER_SECOND = _SERVER_COMPRESSION_RATE * _SAFETY_MARGIN  # 12.88

# Density used only for the advisory "budget" figure in the error message --
# what the author should have aimed for. It does not set the ceiling.
_GUARD_DENSITY = "mixed"


def build_request(part_text: str, seconds: float) -> dict:
    """Return the AIVDO request payload for one part of a Thai episode."""
    if not part_text.strip():
        raise ValueError("part_text is empty")

    ceiling = int(seconds * _MAX_CHARS_PER_SECOND)
    if len(part_text) > ceiling:
        budget = chars_for_duration(seconds, _GUARD_DENSITY)
        predicted = duration_for_chars(len(part_text), _GUARD_DENSITY)
        raise ValueError(
            f"script too long for its slot: {len(part_text):,} chars "
            f"predicts ~{predicted / 60:.1f} min against a "
            f"{seconds / 60:.1f} min target. Aim for {budget:,} chars; "
            f"AIVDO silently compresses above {ceiling:,}."
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


def write_parts(slug_dir: Path, part_texts: list[str], part_seconds: float = 240.0) -> None:
    """Write REQUEST_PART_N.json for every part of an episode.

    Takes the PER-PART target duration, not a total to divide. This used to
    take total_seconds and derive per_part = total_seconds / len(part_texts)
    -- a number with no guaranteed relationship to the part_seconds value
    the caller actually packed against in split_script.split_into_parts.
    The two functions were free to disagree, and did: splitting the real
    #57 TurboTax script at part_seconds=240 produced parts of 2,885 and
    2,766 chars, but a caller supplying the resulting total (523.6s) here
    got per_part=174.5s -> a 2,248-char ceiling that rejected both of them.
    Taking part_seconds directly makes the two stages agree by construction
    -- do not "simplify" this back to total_seconds / len(part_texts).

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
    payloads = [build_request(text, part_seconds) for text in part_texts]

    for stale in slug_dir.glob("REQUEST_PART_*.json"):
        stale.unlink()

    for index, (text, payload) in enumerate(zip(part_texts, payloads), start=1):
        dest = slug_dir / f"REQUEST_PART_{index}.json"
        dest.write_text(json.dumps(payload, ensure_ascii=False, indent=2))
        print(f"{dest.name}: {len(text):,} chars, ~{part_seconds / 60:.1f} min")
