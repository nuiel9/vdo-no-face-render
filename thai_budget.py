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

`mixed` is the working default: most episodes are prose carrying a
handful of figures. Recalibrate against a real ffprobe after the first
full render of each lane (spec §6.4).
"""

# Thai characters spoken per second, voice `Erinome`, style `normal`.
RATES: dict[str, float] = {
    "prose": 11.3,     # narrative passages, few numerals
    "mixed": 12.2,     # default: prose carrying occasional figures
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
