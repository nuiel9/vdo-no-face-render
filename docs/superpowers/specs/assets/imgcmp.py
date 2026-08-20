"""Generate the same prompts across every Google image model in AIVDO's chain.

Mirrors the call shapes in aivdo/modules/google_image.py exactly (_gemini uses
generate_content with response_modalities=["IMAGE"]; _imagen uses
generate_images), so what we see here is what the render pipeline would produce.

Writes PNGs to ./out/<prompt_key>__<model>.png and prints a cost + timing table.
"""
import os
import pathlib
import re
import time

from google import genai
from google.genai import types

OUT = pathlib.Path(__file__).parent / "out"
OUT.mkdir(exist_ok=True)

# Read the key straight from AIVDO's .env; never echo it.
ENV = pathlib.Path.home() / "AIVDO" / ".env"
key = ""
for line in ENV.read_text().splitlines():
    if line.startswith("GOOGLE_AI_API_KEY="):
        key = line.split("=", 1)[1].strip().strip('"').strip("'")
        break
assert key, "GOOGLE_AI_API_KEY not found in ~/AIVDO/.env"

client = genai.Client(api_key=key)

MODELS = [
    ("imagen-4.0-fast-generate-001", "imagen", 0.020),
    ("imagen-4.0-generate-001", "imagen", 0.040),
    ("gemini-2.5-flash-image", "gemini", 0.039),
    ("gemini-3.1-flash-image-preview", "gemini", 0.067),
    ("gemini-3-pro-image-preview", "gemini", 0.134),
]

PROMPTS = {
    # The bulk of the workload: a faceless cinematic documentary scene.
    "scene": (
        "A dimly lit American tax-preparation storefront office at night in the "
        "late 1990s. Empty desks, deep stacks of paper tax forms, a single warm "
        "desk lamp, hard venetian-blind shadows striping the back wall, cold blue "
        "streetlight through the window, dust in the air. Cinematic documentary "
        "still, 35mm, shallow depth of field, muted teal and amber palette, "
        "film grain. No people. No text. No logos. 16:9."
    ),
    # Validates the §6.2 rule that only pro-image can spell Thai.
    "thai_text": (
        "A bold editorial magazine cover on a dark textured surface, dramatic side "
        "lighting. The large headline text reads exactly: ทำไมแว่นตาถึงแพง — "
        "set in heavy black Thai type, centred, sharp and legible. "
        "Cinematic product photograph, 16:9."
    ),
}


def gen_gemini(model: str, prompt: str) -> bytes:
    resp = client.models.generate_content(
        model=model,
        contents=prompt,
        config=types.GenerateContentConfig(response_modalities=["IMAGE"]),
    )
    if not resp.candidates or not resp.candidates[0].content:
        raise RuntimeError("no candidates")
    for part in resp.candidates[0].content.parts:
        if part.inline_data and part.inline_data.data:
            return part.inline_data.data
    raise RuntimeError("no image data")


def gen_imagen(model: str, prompt: str) -> bytes:
    resp = client.models.generate_images(
        model=model,
        prompt=prompt,
        config=types.GenerateImagesConfig(number_of_images=1, aspect_ratio="16:9"),
    )
    if not resp.generated_images:
        raise RuntimeError("no image generated")
    return resp.generated_images[0].image.image_bytes


total = 0.0
print(f"{'prompt':<10} {'model':<32} {'sec':>6} {'KB':>7}  status")
print("-" * 72)
for pkey, prompt in PROMPTS.items():
    for model, kind, price in MODELS:
        safe = re.sub(r"[^a-z0-9.]+", "-", model.lower())
        dest = OUT / f"{pkey}__{safe}.png"
        t0 = time.time()
        try:
            data = gen_imagen(model, prompt) if kind == "imagen" else gen_gemini(model, prompt)
            dest.write_bytes(data)
            total += price
            print(f"{pkey:<10} {model:<32} {time.time()-t0:>6.1f} {len(data)//1024:>7}  ok")
        except Exception as exc:  # noqa: BLE001 - diagnostic sweep
            print(f"{pkey:<10} {model:<32} {time.time()-t0:>6.1f} {'-':>7}  FAIL {str(exc)[:90]}")
print("-" * 72)
print(f"est. spend: ${total:.3f}")
