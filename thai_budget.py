"""Thai script-length budgeting for Disclosed episodes.

Why this exists: AIVDO's scene_planner carries a measured constant of
11.3 Thai chars/sec for `normal` speaking style. That figure is right for
plain prose, and wrong for the script this channel actually writes.

Measured 2026-08-20 on Gemini TTS at `normal`:

    ~200 chars, prose          11.3-11.4 c/s   (matches the constant)
    ~509 chars, figure-dense   12.5-13.7 c/s   (10 voices, incl. Erinome)

Thai number-words are character-heavy but spoken fast -- สี่ร้อยห้าสิบ,
แปดสิบเปอร์เซ็นต์ -- so counting characters OVER-predicts duration on
figure-dense passages by 11-21%. Budgeting a 15-minute episode at 11.3
would land it near 12:30.

MEASURED 2026-08-21, TTS only (no render): 1,362 chars of realistic Thai
narration -- mixed prose and figures, translated from #57 TurboTax's already
fact-verified script -- synthesised with Erinome at `normal` and ffprobed.
Result: 110.54s of speech, **12.32 chars/sec**. Per-chunk it ran 11.93 (prose-
heavy) and 12.83 (figure-heavy), straddling the prose/figures bounds below and
confirming the direction of the model. The prior estimate was 12.2, so the
number barely moved -- but it is now measured on 2.7x more speech rather than
interpolated between two short clips.

Still outstanding: this measures TTS in isolation. A full render may differ
(pacing, scene gaps), so re-check against a real ffprobe when one exists.

`mixed` is the working default: most episodes are prose carrying a
handful of figures. Recalibrate against a real ffprobe after the first
full render of each lane (spec §6.4).
"""

# Thai characters spoken per second, voice `Erinome`, style `normal`.
RATES: dict[str, float] = {
    "prose": 11.3,     # narrative passages, few numerals
    "mixed": 12.32,    # MEASURED 2026-08-21 (see below), not interpolated
    "figures": 13.2,   # measured for Erinome on figure-dense script
}


def chars_for_duration(seconds: float, density: str = "mixed") -> int:
    """Thai characters needed to fill `seconds` of narration."""
    if seconds <= 0:
        raise ValueError("seconds must be positive")
    return int(seconds * RATES[density])


def duration_for_chars(chars: int, density: str = "mixed") -> float:
    """Seconds of narration a script of `chars` Thai characters produces."""
    if chars <= 0:
        raise ValueError("chars must be positive")
    return chars / RATES[density]
