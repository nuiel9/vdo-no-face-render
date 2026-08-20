"""Male narrator shortlist, same long script as the female head-to-head.

Picked by AIVDO's style descriptors (config.py) for documentary narration:
Charon and Rasalgethi are "Informative", Sadaltager "Knowledgeable",
Iapetus "Clear" (the male counterpart to Erinome), Algieba "Smooth" — the
voice the channel has actually been running all along.

Particles are male (ครับ) throughout, as AIVDO would render them.
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
    "กดติดตาม Disclosed ไว้นะครับ เราปล่อยคลิปใหม่ทุกวันครับ"
)

VOICES = [("Charon", "Informative"), ("Sadaltager", "Knowledgeable"),
          ("Iapetus", "Clear"), ("Algieba", "Smooth (current)")]

def wav(pcm, rate=24000):
    h = b"RIFF" + struct.pack("<I", 36 + len(pcm)) + b"WAVEfmt "
    h += struct.pack("<IHHIIHH", 16, 1, 1, rate, rate * 2, 2, 16)
    return h + b"data" + struct.pack("<I", len(pcm)) + pcm

print(f"{len(TEXT)} Thai chars\n")
for voice, style in VOICES:
    t0 = time.time()
    try:
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
                d, m = part.inline_data.data, (part.inline_data.mime_type or "").lower()
                (OUT / f"male-{voice.lower()}.wav").write_bytes(d if "wav" in m else wav(d))
                print(f"{voice:<12} {style:<18} ok  {time.time()-t0:.1f}s")
                break
    except Exception as e:
        print(f"{voice:<12} {style:<18} FAIL {str(e)[:70]}")
