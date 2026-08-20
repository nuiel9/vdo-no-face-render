import pytest

from thai_budget import RATES, chars_for_duration, duration_for_chars


def test_prose_rate_matches_measured_value():
    # 2026-08-20: ~200-char prose clip ran 17.3-17.8s across four voices.
    assert RATES["prose"] == 11.3


def test_figure_dense_is_faster_than_prose():
    # Counter-intuitive but measured: Thai number-words are character-heavy
    # and spoken quickly, so figure-dense script needs MORE characters per
    # minute, not fewer.
    assert RATES["figures"] > RATES["prose"]


def test_fifteen_minute_episode_mixed_density():
    # 900s at the mixed rate. Lane B lower bound.
    assert chars_for_duration(900) == 10980


def test_lane_a_eight_minute_episode():
    assert chars_for_duration(480) == 5856


def test_density_changes_the_budget():
    assert chars_for_duration(900, "figures") > chars_for_duration(900, "prose")


def test_round_trip_is_stable():
    chars = chars_for_duration(900, "figures")
    assert duration_for_chars(chars, "figures") == pytest.approx(900, abs=1)


def test_unknown_density_is_rejected():
    # A typo must not silently fall back to a rate that mis-sizes every
    # script in the batch.
    with pytest.raises(KeyError):
        chars_for_duration(900, "dense")


def test_negative_duration_is_rejected():
    with pytest.raises(ValueError, match="positive"):
        chars_for_duration(-1)
