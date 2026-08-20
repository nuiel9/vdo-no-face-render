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


from render import EXPECTED_ENGINES, engine_is_expected


def test_gemini_engine_satisfies_fast_mode():
    assert engine_is_expected("fast", "gemini-3.1-flash-image") is True


def test_lite_and_pro_also_satisfy_fast_mode():
    # Any model in the Google chain is a legitimate result, including a
    # fallback hop. Only a NON-Gemini engine means the request was misrouted.
    assert engine_is_expected("fast", "gemini-3.1-flash-lite-image") is True
    assert engine_is_expected("fast", "gemini-3-pro-image") is True


def test_openai_engine_does_not_satisfy_fast_mode():
    assert engine_is_expected("fast", "gpt-image-2") is False


def test_unknown_mode_is_permissive():
    # An unrecognised mode must not hard-fail a render mid-flight.
    assert engine_is_expected("some-future-mode", "anything") is True


def _extract_model_dict_list(source: str, var_name: str) -> list[str]:
    """Pull every `"model": "..."` literal out of a module-level list-of-dicts
    assignment, by parsing the AIVDO source with ast rather than importing it
    (AIVDO is a separate repo/venv with its own dependency set — importing it
    from here is not viable). Returns [] if var_name isn't found.
    """
    import ast

    tree = ast.parse(source)
    for node in ast.walk(tree):
        if not isinstance(node, ast.Assign):
            continue
        targets = [t.id for t in node.targets if isinstance(t, ast.Name)]
        if var_name not in targets:
            continue
        models = []
        for elt in node.value.elts:  # type: ignore[attr-defined]
            for key, value in zip(elt.keys, elt.values):
                if isinstance(key, ast.Constant) and key.value == "model":
                    models.append(value.value)
        return models
    return []


def test_every_chain_model_is_in_the_allowlist():
    """Guard against AIVDO's Google image chains drifting away from this
    allowlist. This reads AIVDO's *actual source* (a sibling checkout at
    ~/AIVDO) via ast, rather than asserting literals against literals in
    this repo — the previous version of this test compared three hardcoded
    strings against three other hardcoded strings in the same file, which
    could never fail no matter how far the real chain drifted.

    Checks BOTH AIVDO chains that can produce a "fast"-mode Google engine
    result: ImageGenerator.MODEL_CHAIN (image_generator.py — what
    render_mode="fast" actually executes, via the legacy pipeline) and
    DEFAULT_GOOGLE_CHAIN (google_image.py — the v1.8 image router's chain,
    also referenced for RenderMode.FAST inside image_router.py). Skipped
    entirely if ~/AIVDO isn't checked out on this machine (e.g. CI running
    only this repo) — this repo does not otherwise depend on that checkout.
    """
    import pathlib

    aivdo_root = pathlib.Path.home() / "AIVDO" / "aivdo" / "modules"
    image_generator_py = aivdo_root / "image_generator.py"
    google_image_py = aivdo_root / "google_image.py"
    if not image_generator_py.is_file() or not google_image_py.is_file():
        pytest.skip("~/AIVDO checkout not found — cannot check for chain drift")

    legacy_models = _extract_model_dict_list(image_generator_py.read_text(), "MODEL_CHAIN")
    router_models = _extract_model_dict_list(google_image_py.read_text(), "DEFAULT_GOOGLE_CHAIN")
    assert legacy_models, "could not find MODEL_CHAIN in image_generator.py — extraction broke"
    assert router_models, "could not find DEFAULT_GOOGLE_CHAIN in google_image.py — extraction broke"

    for model in legacy_models:
        assert model in EXPECTED_ENGINES["fast"], (
            f"ImageGenerator.MODEL_CHAIN has {model!r}, which EXPECTED_ENGINES['fast'] "
            "does not know — every render.py run against that model would be "
            "misreported as a misroute."
        )
    for model in router_models:
        assert model in EXPECTED_ENGINES["fast"], (
            f"DEFAULT_GOOGLE_CHAIN has {model!r}, which EXPECTED_ENGINES['fast'] "
            "does not know — every render.py run against that model would be "
            "misreported as a misroute."
        )


import render


def test_in_chain_fallback_does_not_raise_under_strict(monkeypatch):
    # A hop within EXPECTED_ENGINES for the requested mode (e.g. lite ->
    # flash) is a normal outcome, not a misroute — it must not raise even
    # when STRICT_FALLBACK is on. fallback_count > 0 alone must not gate
    # the raise; only an engine outside the allowlist should.
    # image_engine_actually_used is the REAL server shape here: web.py:3438
    # returns sorted(engines_used), a list, not a single string.
    monkeypatch.setattr(render, "STRICT_FALLBACK", True)
    meta = {
        "image_engine_actually_used": ["gemini-3.1-flash-image"],
        "fallback_count": 1,
        "scenes_routed_via": {},
    }
    render.report_routing(1, "fast", meta)  # must not raise


def test_out_of_allowlist_engine_raises_under_strict(monkeypatch):
    # An engine outside EXPECTED_ENGINES for the requested mode is the real
    # failure case report_routing exists to catch.
    monkeypatch.setattr(render, "STRICT_FALLBACK", True)
    meta = {
        "image_engine_actually_used": ["gpt-image-2"],
        "fallback_count": 1,
        "scenes_routed_via": {},
    }
    with pytest.raises(RuntimeError, match="fell back"):
        render.report_routing(1, "fast", meta)


def test_list_of_all_allowed_engines_does_not_raise_under_strict(monkeypatch):
    # A job can render scenes through more than one engine in the same
    # chain (e.g. lite for most scenes, flash for a retried one). Every
    # member being in the allowlist is a correctly routed render.
    monkeypatch.setattr(render, "STRICT_FALLBACK", True)
    meta = {
        "image_engine_actually_used": ["gemini-3.1-flash-lite-image", "gemini-3.1-flash-image"],
        "fallback_count": 1,
        "scenes_routed_via": {},
    }
    render.report_routing(1, "fast", meta)  # must not raise


def test_list_with_one_disallowed_engine_raises_under_strict(monkeypatch):
    # Only ONE member of the list needs to be outside the allowlist for the
    # whole part to be a misroute — "every member allowed" is the bar.
    monkeypatch.setattr(render, "STRICT_FALLBACK", True)
    meta = {
        "image_engine_actually_used": ["gemini-3.1-flash-lite-image", "gpt-image-2"],
        "fallback_count": 1,
        "scenes_routed_via": {},
    }
    with pytest.raises(RuntimeError, match="fell back"):
        render.report_routing(1, "fast", meta)


def test_absent_routing_metadata_does_not_raise_under_strict(monkeypatch):
    # render_mode="fast" leaves job.scene_dna NULL server-side, so web.py
    # omits image_engine_actually_used from the response entirely. That is
    # the normal case for every Thai render and must never be flagged as a
    # misroute, even under STRICT_FALLBACK.
    monkeypatch.setattr(render, "STRICT_FALLBACK", True)
    meta = {
        "image_engine_actually_used": None,
        "scenes_routed_via": None,
        "fallback_count": None,
        "tone_variant_resolved": None,
    }
    render.report_routing(1, "fast", meta)  # must not raise


def test_empty_list_routing_metadata_does_not_raise_under_strict(monkeypatch):
    # An empty list (as opposed to a missing key) must be treated the same
    # way — "no routing data", not a misroute.
    monkeypatch.setattr(render, "STRICT_FALLBACK", True)
    meta = {
        "image_engine_actually_used": [],
        "fallback_count": 0,
        "scenes_routed_via": {},
    }
    render.report_routing(1, "fast", meta)  # must not raise


def test_bare_string_engine_is_still_accepted_for_backward_compatibility(monkeypatch):
    # Not the real server shape (that's a list), but report_routing should
    # not choke if some caller ever hands it a single string directly.
    monkeypatch.setattr(render, "STRICT_FALLBACK", True)
    meta = {
        "image_engine_actually_used": "gpt-image-2",
        "fallback_count": 1,
        "scenes_routed_via": {},
    }
    with pytest.raises(RuntimeError, match="fell back"):
        render.report_routing(1, "fast", meta)


from render import apply_request_defaults


def test_apply_request_defaults_sets_fast_on_a_fresh_request():
    # A new Thai slug's REQUEST_PART_*.json has no render_mode -- it must
    # default to "fast", AIVDO's Gemini-only lane.
    req = {"text": "สวัสดีค่ะ"}
    apply_request_defaults(req)
    assert req["render_mode"] == "fast"
    assert req["video_intent"] == "faceless_youtube"


def test_apply_request_defaults_keeps_an_existing_cinematic_slugs_mode():
    # Re-rendering a shipped English slug (delete partN.mp4, re-run) must
    # NOT silently downgrade it from cinematic/gpt-image-2 to the Gemini
    # fast lane. This is the exact shape a shipped slug's
    # REQUEST_PART_*.json carries: render_mode "cinematic" +
    # strict_cinematic true.
    req = {
        "text": "English narration.",
        "render_mode": "cinematic",
        "strict_cinematic": True,
    }
    apply_request_defaults(req)
    assert req["render_mode"] == "cinematic"
    assert req["strict_cinematic"] is True
    assert req["video_intent"] == "faceless_youtube"
