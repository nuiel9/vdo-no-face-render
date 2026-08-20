"""Add the lite tier + stable (non-preview) names to the comparison.

Kept separate from imgcmp.py so importing one never re-runs the other's sweep.
"""
import pathlib
import re
import time

from google import genai
from google.genai import types

OUT = pathlib.Path(__file__).parent / "out"
OUT.mkdir(exist_ok=True)

ENV = pathlib.Path.home() / "AIVDO" / ".env"
key = ""
for line in ENV.read_text().splitlines():
    if line.startswith("GOOGLE_AI_API_KEY="):
        key = line.split("=", 1)[1].strip().strip('"').strip("'")
        break
client = genai.Client(api_key=key)

MODELS = [("gemini-3.1-flash-lite-image", 0.0336)]

PROMPTS = {
    "scene": (
        "A dimly lit American tax-preparation storefront office at night in the "
        "late 1990s. Empty desks, deep stacks of paper tax forms, a single warm "
        "desk lamp, hard venetian-blind shadows striping the back wall, cold blue "
        "streetlight through the window, dust in the air. Cinematic documentary "
        "still, 35mm, shallow depth of field, muted teal and amber palette, "
        "film grain. No people. No text. No logos. 16:9."
    ),
    "thai_text": (
        "A bold editorial magazine cover on a dark textured surface, dramatic side "
        "lighting. The large headline text reads exactly: ทำไมแว่นตาถึงแพง — "
        "set in heavy black Thai type, centred, sharp and legible. "
        "Cinematic product photograph, 16:9."
    ),
}

total = 0.0
print(f"{'prompt':<10} {'model':<32} {'sec':>6} {'KB':>7}  status")
print("-" * 72)
for pkey, prompt in PROMPTS.items():
    for model, price in MODELS:
        safe = re.sub(r"[^a-z0-9.]+", "-", model.lower())
        dest = OUT / f"{pkey}__{safe}.png"
        t0 = time.time()
        try:
            resp = client.models.generate_content(
                model=model,
                contents=prompt,
                config=types.GenerateContentConfig(response_modalities=["IMAGE"]),
            )
            data = None
            for part in resp.candidates[0].content.parts:
                if part.inline_data and part.inline_data.data:
                    data = part.inline_data.data
                    break
            if not data:
                raise RuntimeError("no image data")
            dest.write_bytes(data)
            total += price
            print(f"{pkey:<10} {model:<32} {time.time()-t0:>6.1f} {len(data)//1024:>7}  ok")
        except Exception as exc:  # noqa: BLE001
            print(f"{pkey:<10} {model:<32} {time.time()-t0:>6.1f} {'-':>7}  FAIL {str(exc)[:90]}")
print("-" * 72)
print(f"est. spend: ${total:.4f}")
