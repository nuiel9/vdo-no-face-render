import make_request_parts
from thai_lint import lint_script

GOOD = """# ok
[Scene 1 | high] Hook
OVERLAYS: none
คุณเคยสงสัยไหมครับว่าทำไมราคาถึงแพงขนาดนี้

[Scene 2 | medium] Close
OVERLAYS: none
กดติดตาม Disclosed ไว้นะครับ
"""


def test_clean_script_has_no_problems():
    assert lint_script(GOOD) == []


def test_flags_female_particle_with_a_male_narrator():
    # The voice is Sadaltager (male, chosen 2026-08-21). A ค่ะ/นะคะ close is
    # the inverse of the bug commit e2775e9 fixed inside AIVDO -- audible
    # for the same reason, in the other direction.
    bad = GOOD.replace("นะครับ", "นะคะ")
    problems = lint_script(bad)
    assert any("คะ" in p for p in problems)


def test_particle_rule_follows_narrator_gender_constant(monkeypatch):
    # The whole point of centralising the narrator in NARRATOR_GENDER is
    # that the particle rule flips WITH it, automatically, with no lint.py
    # edit required. Prove it directly rather than trusting the two male-
    # narrator tests above to imply it.
    monkeypatch.setattr(make_request_parts, "NARRATOR_GENDER", "female")

    female_ok = GOOD.replace("นะครับ", "นะคะ").replace("ครับ", "ค่ะ")
    assert lint_script(female_ok) == []

    female_bad = GOOD  # still has ครับ / นะครับ from the module fixture
    problems = lint_script(female_bad)
    assert any("ครับ" in p for p in problems)


def test_does_not_flag_khaa_naen_as_a_female_particle():
    # คะแนน (score/points) is a realistic word on a tech/business channel --
    # a Geekbench score, a credit score -- and it contains a bare คะ that is
    # NOT the female particle. A male-narrator script using it correctly
    # must still lint clean; flagging it would block .facts_verified on a
    # script that was never wrong.
    male_with_score = GOOD.replace(
        "ไว้นะครับ", "ไว้นะครับ ได้คะแนน Geekbench สูงสุดในรุ่นครับ"
    )
    assert lint_script(male_with_score) == []


def test_flags_em_dash():
    bad = GOOD.replace("ราคาถึงแพง", "ราคา—ถึงแพง")
    assert any("em dash" in p.lower() for p in lint_script(bad))


def test_flags_double_hyphen():
    bad = GOOD.replace("ราคาถึงแพง", "ราคา--ถึงแพง")
    assert any("--" in p for p in lint_script(bad))


def test_flags_a_part_that_would_be_silently_compressed():
    big = "# t\n\n" + "".join(
        f"[Scene {i} | medium] s\nOVERLAYS: none\n{'ก' * 4000}\n\n" for i in range(1, 3)
    )
    assert any("compress" in p.lower() or "too long" in p.lower()
               for p in lint_script(big, part_seconds=60.0))


def test_flags_narration_with_no_thai_at_all():
    # An untranslated script is the failure this exists to catch early.
    english = GOOD.replace("คุณเคยสงสัยไหมครับว่าทำไมราคาถึงแพงขนาดนี้",
                           "Have you ever wondered why the price is so high")
    assert any("thai" in p.lower() for p in lint_script(english))


def test_flags_unfilled_placeholder_left_in_narration():
    # This is the real bug: [จุดใส่ caveat ...] sat at the end of a narration
    # line and would have been read aloud, brackets and all. parse_scenes has
    # already stripped every legitimate [Scene N | energy] marker by the time
    # lint_script sees narration, so any [ or ] surviving into it is by
    # definition leftover authoring scaffolding, not a scene marker.
    bad = GOOD.replace(
        "นะครับ",
        "นะครับ [จุดใส่ caveat ของเจ้าของช่อง]",
    )
    problems = lint_script(bad)
    assert any("placeholder" in p.lower() for p in problems)


def test_flags_todo_left_in_narration():
    bad = GOOD.replace("นะครับ", "นะครับ TODO: fill this in")
    problems = lint_script(bad)
    assert any("placeholder" in p.lower() or "todo" in p.lower() for p in problems)


def test_scene_markers_do_not_trigger_the_placeholder_check():
    # The check that matters: a script with only legitimate [Scene N | energy]
    # markers (already stripped by parse_scenes before lint_script ever sees
    # the narration) must NOT be flagged. A check that fires on every script
    # is useless.
    assert lint_script(GOOD) == []


def test_bracket_in_a_comment_line_does_not_trigger_the_placeholder_check():
    # A '#'-prefixed line is never spoken -- parse_scenes skips it entirely --
    # so brackets inside it are not a shipping risk.
    commented = GOOD.replace(
        "[Scene 2 | medium] Close",
        "[Scene 2 | medium] Close\n# note: [leave this alone, it's a comment]",
    )
    assert lint_script(commented) == []
