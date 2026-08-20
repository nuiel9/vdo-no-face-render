"""Longer head-to-head: Erinome vs Despina on a script that stresses a real episode.

The 18s clip is too short to choose a permanent narrator. This one carries
numbers (years, percentages, baht figures — the hardest thing for Thai TTS),
a reveal beat, and the mandated subscribe CTA (§5.4), which the voice has to
deliver without sounding like an ad.
"""
import pathlib, struct, time
from google import genai
from google.genai import types

OUT = pathlib.Path("voice"); OUT.mkdir(exist_ok=True)
key = next(l.split("=", 1)[1].strip().strip('"').strip("'")
           for l in (pathlib.Path.home() / "AIVDO" / ".env").read_text().splitlines()
           if l.startswith("GOOGLE_AI_API_KEY="))
client = genai.Client(api_key=key)

TEXT = (
    "ปี 1999 บริษัทเล็กๆ ในอิตาลีชื่อ Luxottica ตัดสินใจซื้อโรงงานผลิตแว่นตาแห่งที่สาม "
    "ตอนนั้นแทบไม่มีใครสนใจ "
    "สิบปีต่อมา บริษัทนี้คุมแบรนด์แว่นตามากกว่ายี่สิบแบรนด์ "
    "คุมร้านค้าปลีกกว่าเจ็ดพันสาขา "
    "และคุมส่วนแบ่งตลาดแว่นกันแดดระดับพรีเมียมเกือบแปดสิบเปอร์เซ็นต์ "
    "แว่นที่คุณจ่ายไปหมื่นสองพันบาท ต้นทุนการผลิตจริงอยู่ที่ประมาณสี่ร้อยห้าสิบบาท "
    "ส่วนต่างนั้นไม่ได้หายไปไหน มันกลับไปที่บริษัทเดียวกันทั้งหมด "
    "ถ้าคุณอยากรู้ว่าเบื้องหลังราคาที่คุณจ่ายทุกวันมีอะไรซ่อนอยู่ "
    "กดติดตาม Disclosed ไว้นะคะ เราปล่อยคลิปใหม่ทุกวันค่ะ"
)
print(f"script: {len(TEXT)} Thai chars → ~{len(TEXT)/11.3:.0f}s predicted at normal rate\n")

def wav(pcm, rate=24000):
    h = b"RIFF" + struct.pack("<I", 36 + len(pcm)) + b"WAVEfmt "
    h += struct.pack("<IHHIIHH", 16, 1, 1, rate, rate * 2, 2, 16)
    return h + b"data" + struct.pack("<I", len(pcm)) + pcm

for voice in ["Erinome", "Despina"]:
    t0 = time.time()
    r = client.models.generate_content(
        model="gemini-2.5-flash-preview-tts", contents=TEXT,
        config=types.GenerateContentConfig(
            response_modalities=["AUDIO"],
            speech_config=types.SpeechConfig(
                language_code="th-TH",
                voice_config=types.VoiceConfig(
                    prebuilt_voice_config=types.PrebuiltVoiceConfig(voice_name=voice)))))
    for part in r.candidates[0].content.parts:
        if part.inline_data and part.inline_data.data:
            d = part.inline_data.data
            m = (part.inline_data.mime_type or "").lower()
            (OUT / f"long-{voice.lower()}.wav").write_bytes(d if "wav" in m else wav(d))
            print(f"{voice:<10} ok  {time.time()-t0:.1f}s gen")
            break
