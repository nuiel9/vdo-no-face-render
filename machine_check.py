"""Machine first pass over a script, ahead of the human editorial gate.

Per spec §8 this FILTERS what reaches the human gate. It never replaces it,
and it never marks anything verified. Its only job is to surface checkable
claims -- numbers, dates, named entities, superlatives -- so the human spends
their time on the claims that carry risk instead of reading for them.

Runs channel-side against Gemini directly. AIVDO carries its own
video_verifier_model, but reaching it would mean a cross-repo dependency for
no gain -- the check needs no render.
"""
import json
import os
import pathlib

from google import genai
from google.genai import types

from split_script import parse_scenes

# Stable, not -preview: the spec's own §6.1 rule is "pin stable names,
# previews get deprecated". AIVDO uses gemini-3-flash-preview for its
# verifiers; that is their choice and out of scope here. Verified present on
# the production key 2026-08-21, alongside newer stable flash releases.
_MODEL = "gemini-3.6-flash"

_PROMPT = """You are screening a documentary narration script before a human fact-check.

List every factual claim that a careful editor would want a primary source for:
numbers, dates, named companies or people, superlatives ("first", "largest",
"only"), and causal claims about real events.

Do NOT verify anything. Do NOT guess whether a claim is true. Only surface
claims that carry risk if wrong, so the human checks those first.

Return JSON: a list of objects with keys "claim" (quote it verbatim from the
script) and "why" (a short phrase: what kind of claim it is).

Script scene:
"""


def _client() -> genai.Client:
    key = os.environ.get("GOOGLE_AI_API_KEY")
    if not key:
        env = pathlib.Path.home() / "AIVDO" / ".env"
        for line in env.read_text().splitlines():
            if line.startswith("GOOGLE_AI_API_KEY="):
                key = line.split("=", 1)[1].strip().strip('"').strip("'")
                break
    if not key:
        raise RuntimeError("GOOGLE_AI_API_KEY not set and not found in ~/AIVDO/.env")
    return genai.Client(api_key=key)


def screen_script(script: str) -> list[dict]:
    """Return claims worth a human fact-check, scene by scene."""
    client = _client()
    flagged: list[dict] = []

    for index, (_, narration) in enumerate(parse_scenes(script), 1):
        if not narration:
            continue
        resp = client.models.generate_content(
            model=_MODEL,
            contents=_PROMPT + narration,
            config=types.GenerateContentConfig(response_mime_type="application/json"),
        )
        try:
            for item in json.loads(resp.text):
                flagged.append({
                    "scene": index,
                    "claim": item.get("claim", ""),
                    "why": item.get("why", ""),
                })
        except (json.JSONDecodeError, TypeError):
            flagged.append({
                "scene": index,
                "claim": "(screen failed — check this scene by hand)",
                "why": "model returned unparseable output",
            })
    return flagged


if __name__ == "__main__":
    import sys

    text = pathlib.Path(sys.argv[1]).read_text(encoding="utf-8")
    rows = screen_script(text)
    print(f"{len(rows)} claim(s) flagged for human verification\n")
    for row in rows:
        print(f"  [scene {row['scene']}] {row['why']}: {row['claim'][:100]}")
