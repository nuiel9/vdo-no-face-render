from thai_lint import lint_script

GOOD = """# ok
[Scene 1 | high] Hook
OVERLAYS: none
คุณเคยสงสัยไหมคะว่าทำไมราคาถึงแพงขนาดนี้

[Scene 2 | medium] Close
OVERLAYS: none
กดติดตาม Disclosed ไว้นะคะ เราปล่อยคลิปใหม่ทุกวันค่ะ
"""


def test_clean_script_has_no_problems():
    assert lint_script(GOOD) == []


def test_flags_male_particle_with_a_female_narrator():
    # The voice is Erinome (female). A ครับ close is the exact bug commit
    # e2775e9 fixed inside AIVDO, and it is audible.
    bad = GOOD.replace("ทุกวันค่ะ", "ทุกวันครับ")
    problems = lint_script(bad)
    assert any("ครับ" in p for p in problems)


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
    english = GOOD.replace("คุณเคยสงสัยไหมคะว่าทำไมราคาถึงแพงขนาดนี้",
                           "Have you ever wondered why the price is so high")
    assert any("thai" in p.lower() for p in lint_script(english))


def test_flags_unfilled_placeholder_left_in_narration():
    # This is the real bug: [จุดใส่ caveat ...] sat at the end of a narration
    # line and would have been read aloud, brackets and all. parse_scenes has
    # already stripped every legitimate [Scene N | energy] marker by the time
    # lint_script sees narration, so any [ or ] surviving into it is by
    # definition leftover authoring scaffolding, not a scene marker.
    bad = GOOD.replace(
        "ทุกวันค่ะ",
        "ทุกวันค่ะ [จุดใส่ caveat ของเจ้าของช่อง]",
    )
    problems = lint_script(bad)
    assert any("placeholder" in p.lower() for p in problems)


def test_flags_todo_left_in_narration():
    bad = GOOD.replace("ทุกวันค่ะ", "ทุกวันค่ะ TODO: fill this in")
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
