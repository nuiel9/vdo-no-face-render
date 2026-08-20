"""Generate Thai narration samples across both TTS systems AIVDO can use.

Two distinct systems, not two voices:
  1. Gemini TTS (gemini-*-tts, prebuilt voice names) — AIVDO's PRIMARY path,
     currently configured with voice "Algieba".
  2. Cloud TTS Chirp3-HD (th-TH-Chirp3-HD-*) — AIVDO's FALLBACK path, native
     Thai voices. These are the names the spec currently pins.

Same script for all four so the comparison is clean, except the closing
particle, which agrees with the narrator's gender (ค่ะ / ครับ) exactly as
AIVDO does in production.
"""
import pathlib
import struct
import time

from google import genai
from google.genai import types

OUT = pathlib.Path(__file__).parent / "voice"
OUT.mkdir(exist_ok=True)

ENV = pathlib.Path.home() / "AIVDO" / ".env"
key = ""
for line in ENV.read_text().splitlines():
    if line.startswith("GOOGLE_AI_API_KEY="):
        key = line.split("=", 1)[1].strip().strip('"').strip("'")
        break

# A real episode cold-open in spoken register (§5.5), not translated English.
BODY = (
    "คุณเคยสงสัยไหมว่า ทำไมแว่นตาคู่หนึ่งถึงราคาเป็นหมื่น "
    "ทั้งที่ต้นทุนจริงอาจไม่ถึงห้าร้อยบาท "
    "คำตอบไม่ได้อยู่ที่เลนส์ แต่อยู่ที่บริษัทเดียว "
    "ที่คุมโรงงานแว่นตาเกือบทั้งโลกมานานกว่าสามสิบปี "
    "วันนี้เราจะเปิดแฟ้มนั้นให้ดูกัน"
)
TEXT = {"female": BODY + "ค่ะ", "male": BODY + "ครับ"}


def pcm_to_wav(pcm: bytes, rate: int = 24000) -> bytes:
    """Wrap raw 16-bit mono PCM in a WAV container."""
    header = b"RIFF" + struct.pack("<I", 36 + len(pcm)) + b"WAVEfmt "
    header += struct.pack("<IHHIIHH", 16, 1, 1, rate, rate * 2, 2, 16)
    header += b"data" + struct.pack("<I", len(pcm))
    return header + pcm


def gemini_tts(model: str, voice: str, text: str) -> bytes:
    client = genai.Client(api_key=key)
    resp = client.models.generate_content(
        model=model,
        contents=text,
        config=types.GenerateContentConfig(
            response_modalities=["AUDIO"],
            speech_config=types.SpeechConfig(
                language_code="th-TH",
                voice_config=types.VoiceConfig(
                    prebuilt_voice_config=types.PrebuiltVoiceConfig(voice_name=voice)
                ),
            ),
        ),
    )
    for part in resp.candidates[0].content.parts:
        if part.inline_data and part.inline_data.data:
            data = part.inline_data.data
            mime = (part.inline_data.mime_type or "").lower()
            return data if "wav" in mime else pcm_to_wav(data)
    raise RuntimeError("no audio in response")


def cloud_tts(voice: str, text: str) -> bytes:
    from google.cloud import texttospeech

    client = texttospeech.TextToSpeechClient()
    resp = client.synthesize_speech(
        input=texttospeech.SynthesisInput(text=text),
        voice=texttospeech.VoiceSelectionParams(language_code="th-TH", name=voice),
        audio_config=texttospeech.AudioConfig(
            audio_encoding=texttospeech.AudioEncoding.LINEAR16
        ),
    )
    return resp.audio_content


JOBS = [
    ("gemini-algieba-female", "gemini", "gemini-2.5-flash-preview-tts", "Algieba", "female"),
    ("gemini-charon-male", "gemini", "gemini-2.5-flash-preview-tts", "Charon", "male"),
    ("chirp3hd-achernar-female", "cloud", "", "th-TH-Chirp3-HD-Achernar", "female"),
    ("chirp3hd-charon-male", "cloud", "", "th-TH-Chirp3-HD-Charon", "male"),
]

print(f"{'sample':<28} {'sec':>6} {'KB':>7}  status")
print("-" * 60)
for label, kind, model, voice, gender in JOBS:
    dest = OUT / f"{label}.wav"
    t0 = time.time()
    try:
        audio = (gemini_tts(model, voice, TEXT[gender]) if kind == "gemini"
                 else cloud_tts(voice, TEXT[gender]))
        dest.write_bytes(audio)
        print(f"{label:<28} {time.time()-t0:>6.1f} {len(audio)//1024:>7}  ok")
    except Exception as exc:  # noqa: BLE001
        print(f"{label:<28} {time.time()-t0:>6.1f} {'-':>7}  FAIL {str(exc)[:100]}")
