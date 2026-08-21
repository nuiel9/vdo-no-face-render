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
