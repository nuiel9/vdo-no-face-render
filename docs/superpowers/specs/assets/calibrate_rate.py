"""Measure Erinome's real Thai speaking rate — TTS only, no render.

thai_budget.py currently ships ESTIMATES derived from two short clips
(506 and ~200 chars). Every script Plan 2 writes gets sized by them, so
they are the most load-bearing unverified numbers in the plan.

Source text is a Thai translation of #57 TurboTax's SCRIPT.txt — already
fact-verified and shipped, so no new factual claims are introduced. The
topic fails the Thai-relevance filter, which does not matter: speech rate
is indifferent to whether a topic suits the market.

Chunked at ~800 chars to mirror AIVDO's own `_split_text`, and durations
are SUMMED per chunk rather than measured on a concatenation — inter-chunk
silence is a stitching artefact, not speech time, and the rate constant
budgets speech.
"""
import pathlib
import struct
import subprocess
import time

from google import genai
from google.genai import types

OUT = pathlib.Path(__file__).parent / "calib"
OUT.mkdir(exist_ok=True)

key = next(l.split("=", 1)[1].strip().strip('"').strip("'")
           for l in (pathlib.Path.home() / "AIVDO" / ".env").read_text().splitlines()
           if l.startswith("GOOGLE_AI_API_KEY="))
client = genai.Client(api_key=key)

# Paragraph-separated so chunking never splits mid-sentence.
PARAGRAPHS = [
    "ทุกฤดูใบไม้ผลิ โฆษณาเหล่านั้นจะกลับมาอีกครั้ง ฟรี ฟรี ฟรี "
    "เพลงโฆษณาที่สัญญาว่าปีนี้ คุณจะยื่นภาษีได้โดยไม่เสียเงินสักบาท "
    "คุณจึงนั่งลง เปิดโปรแกรม แล้วเริ่มกรอกชีวิตของคุณลงไป "
    "งานประจำ หนี้กู้ยืมเพื่อการศึกษา อาจมีงานฟรีแลนซ์เล็กน้อย "
    "แล้วที่ไหนสักแห่งระหว่างทาง คำว่าฟรีก็หายไปเงียบๆ ถูกแทนที่ด้วยค่าบริการ "
    "เก้าสิบดอลลาร์ นี่ไม่ใช่ความผิดพลาดของระบบ แต่มันคือการออกแบบทั้งหมด",

    "ปีที่แล้ว รัฐบาลสหรัฐสร้างเครื่องมือที่ให้ประชาชนยื่นภาษีได้ฟรีจริงๆ "
    "มีชาวอเมริกันราวสองแสนเก้าหมื่นหกพันคนใช้มัน ปีนี้ ตัวเลขนั้นเหลือศูนย์ "
    "บริษัทซอฟต์แวร์ภาษีที่คนเชื่อถือมากที่สุด "
    "ใช้เงินหลายล้านดอลลาร์เพื่อให้แน่ใจว่ามันจะเป็นแบบนั้น",

    "นี่คือเรื่องราวของบริษัทเดียว ที่เปลี่ยนคำว่าฟรี "
    "ให้กลายเป็นคำที่แพงที่สุดของฤดูกาลยื่นภาษี "
    "แล้วทุ่มเงินมหาศาลเพื่อปกป้องมันเอาไว้",

    "เริ่มจากโฆษณาก่อน หลายปีที่ผ่านมา บริษัทโฆษณาสินค้าที่เรียกว่าฟรี "
    "แต่คณะกรรมาธิการการค้าแห่งสหรัฐพบในภายหลังว่า ผู้เสียภาษีราวสองในสาม "
    "ไม่สามารถใช้มันได้จริง เวอร์ชันฟรีใช้ได้เฉพาะกับการยื่นที่ง่ายที่สุดเท่านั้น "
    "เพิ่มการลดหย่อนหนี้การศึกษา เพิ่มแบบฟอร์มฟรีแลนซ์ เพิ่มรายได้หลังเกษียณ "
    "แล้วหน้าจอจะหยุดคุณไว้ พร้อมเสนอให้อัปเกรด คำว่าฟรีคือประตู "
    "ส่วนค่าบริการคือห้องที่อยู่ข้างหลังประตูบานนั้น",

    "เพื่อจะเข้าใจว่าทำไม ต้องย้อนกลับไปปีสองพันสอง "
    "บริษัทซอฟต์แวร์ภาษีทำข้อตกลงกับกรมสรรพากรสหรัฐ "
    "พวกเขาจะให้บริการยื่นภาษีฟรีแก่ชาวอเมริกันที่มีรายได้น้อย และแลกกับสิ่งนั้น "
    "กรมสรรพากรจะไม่สร้างระบบยื่นภาษีฟรีของตัวเองขึ้นมาแข่งค่ะ",
]


def chunk(paras: list[str], max_chars: int = 800) -> list[str]:
    """Group paragraphs into <=max_chars chunks, never splitting one."""
    chunks, cur = [], ""
    for para in paras:
        if cur and len(cur) + len(para) + 1 > max_chars:
            chunks.append(cur)
            cur = para
        else:
            cur = f"{cur} {para}".strip()
    if cur:
        chunks.append(cur)
    return chunks


def wav(pcm: bytes, rate: int = 24000) -> bytes:
    h = b"RIFF" + struct.pack("<I", 36 + len(pcm)) + b"WAVEfmt "
    h += struct.pack("<IHHIIHH", 16, 1, 1, rate, rate * 2, 2, 16)
    return h + b"data" + struct.pack("<I", len(pcm)) + pcm


def duration(path: pathlib.Path) -> float:
    return float(subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration",
         "-of", "csv=p=0", str(path)],
        capture_output=True, text=True).stdout.strip())


chunks = chunk(PARAGRAPHS)
print(f"{len(chunks)} chunk(s), {sum(len(c) for c in chunks):,} Thai chars total\n")
print(f"{'chunk':<7} {'chars':>7} {'sec':>8} {'c/s':>7}")
print("-" * 34)

total_chars = total_secs = 0.0
for i, text in enumerate(chunks, 1):
    dest = OUT / f"chunk{i}.wav"
    resp = client.models.generate_content(
        model="gemini-2.5-flash-preview-tts",
        contents=text,
        config=types.GenerateContentConfig(
            response_modalities=["AUDIO"],
            speech_config=types.SpeechConfig(
                language_code="th-TH",
                voice_config=types.VoiceConfig(
                    prebuilt_voice_config=types.PrebuiltVoiceConfig(voice_name="Erinome")))))
    data = None
    for part in resp.candidates[0].content.parts:
        if part.inline_data and part.inline_data.data:
            m = (part.inline_data.mime_type or "").lower()
            data = part.inline_data.data if "wav" in m else wav(part.inline_data.data)
            break
    if not data:
        raise RuntimeError(f"chunk {i}: no audio returned")
    dest.write_bytes(data)
    secs = duration(dest)
    total_chars += len(text)
    total_secs += secs
    print(f"{i:<7} {len(text):>7,} {secs:>8.2f} {len(text)/secs:>7.2f}")
    time.sleep(1)

print("-" * 34)
print(f"{'TOTAL':<7} {int(total_chars):>7,} {total_secs:>8.2f} {total_chars/total_secs:>7.2f}")
print()
print(f"MEASURED RATE: {total_chars/total_secs:.2f} Thai chars/sec "
      f"(Erinome, normal, mixed prose+figures)")
print(f"15-min episode -> {int(900 * total_chars/total_secs):,} chars")
print(f" 8-min episode -> {int(480 * total_chars/total_secs):,} chars")
