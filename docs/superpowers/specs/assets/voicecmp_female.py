"""Female Gemini TTS voices for the Thai narrator, per AIVDO's own gender table.

The first sweep was wrong: it forced a ค่ะ script onto Algieba, which
config.py:209 lists as MALE ({"gender": "male", "style": "Smooth"}). In
production AIVDO would have given Algieba ครับ. This sweep uses only voices
the table marks female, all reading the ค่ะ script.

Shortlist reasoning — documentary narration wants clarity and steadiness, so
this covers the three low-pitched female voices (voice_studio.py's "low" group)
plus the three whose style descriptors suit narration.
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

TEXT = (
    "คุณเคยสงสัยไหมว่า ทำไมแว่นตาคู่หนึ่งถึงราคาเป็นหมื่น "
    "ทั้งที่ต้นทุนจริงอาจไม่ถึงห้าร้อยบาท "
    "คำตอบไม่ได้อยู่ที่เลนส์ แต่อยู่ที่บริษัทเดียว "
    "ที่คุมโรงงานแว่นตาเกือบทั้งโลกมานานกว่าสามสิบปี "
    "วันนี้เราจะเปิดแฟ้มนั้นให้ดูกันค่ะ"
)

# (voice, style descriptor from config.py, pitch group)
VOICES = [
    ("Despina", "Smooth", "low"),
    ("Sulafat", "Warm", "low"),
    ("Achernar", "Soft", "low"),
    ("Erinome", "Clear", "mid"),
    ("Kore", "Firm", "mid"),
    ("Schedar", "Even", "mid"),
]

MODEL = "gemini-2.5-flash-preview-tts"
client = genai.Client(api_key=key)


def pcm_to_wav(pcm: bytes, rate: int = 24000) -> bytes:
    header = b"RIFF" + struct.pack("<I", 36 + len(pcm)) + b"WAVEfmt "
    header += struct.pack("<IHHIIHH", 16, 1, 1, rate, rate * 2, 2, 16)
    return header + b"data" + struct.pack("<I", len(pcm)) + pcm


print(f"{'voice':<14} {'style':<10} {'pitch':<6} {'sec':>6}  status")
print("-" * 52)
for voice, style, pitch in VOICES:
    dest = OUT / f"female-{voice.lower()}-{style.lower()}.wav"
    t0 = time.time()
    try:
        resp = client.models.generate_content(
            model=MODEL,
            contents=TEXT,
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
        data = None
        for part in resp.candidates[0].content.parts:
            if part.inline_data and part.inline_data.data:
                mime = (part.inline_data.mime_type or "").lower()
                data = part.inline_data.data if "wav" in mime else pcm_to_wav(part.inline_data.data)
                break
        if not data:
            raise RuntimeError("no audio")
        dest.write_bytes(data)
        print(f"{voice:<14} {style:<10} {pitch:<6} {time.time()-t0:>6.1f}  ok")
    except Exception as exc:  # noqa: BLE001
        print(f"{voice:<14} {style:<10} {pitch:<6} {time.time()-t0:>6.1f}  FAIL {str(exc)[:80]}")
