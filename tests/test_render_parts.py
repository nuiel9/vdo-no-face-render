import pytest

from render import discover_parts


def _make(base, numbers):
    for n in numbers:
        (base / f"REQUEST_PART_{n}.json").write_text("{}")


def test_finds_two_parts(tmp_path):
    _make(tmp_path, [1, 2])
    assert discover_parts(tmp_path) == [1, 2]


def test_finds_five_parts(tmp_path):
    _make(tmp_path, [1, 2, 3, 4, 5])
    assert discover_parts(tmp_path) == [1, 2, 3, 4, 5]


def test_sorts_numerically_not_lexically(tmp_path):
    # Lexical sort would give [1, 10, 2, ...]; a 10-part episode must not
    # stitch its scenes out of order. Must be a contiguous 1..10 set so the
    # gap check (test_raises_on_gap) doesn't also fire here.
    _make(tmp_path, list(range(1, 11)))
    assert discover_parts(tmp_path) == list(range(1, 11))


def test_raises_when_no_parts(tmp_path):
    with pytest.raises(FileNotFoundError, match="no REQUEST_PART"):
        discover_parts(tmp_path)


def test_raises_on_gap(tmp_path):
    # A missing part means a missing chunk of narration. Fail loudly rather
    # than silently publishing an episode with a hole in it.
    _make(tmp_path, [1, 2, 4])
    with pytest.raises(ValueError, match="gap"):
        discover_parts(tmp_path)
