# Prompt Library V3 (Thai): Disclosed — เรื่องที่ไม่มีใครบอก

Authored 2026-08-21 against `docs/superpowers/specs/2026-08-20-thai-pivot-design.md`
(§5.1–5.5, §7.1–7.7, §8) — **the spec wins on any conflict with this file.**

**This is a rewrite, not a translation of `prompts_v2.md`.** v2 encodes the retired
English strategy: two-part 10–12 min scripts, the "would a 55-year-old American man
recognise this" gate, second-channel niche scoring, monthly revenue diagnostics, a
single title formula. None of that survives here. What's kept from v2 is called out
prompt-by-prompt as *carried forward, adapted* — never assumed.

Prompt bodies below are written **in Thai**, because the model executing them is
producing Thai output and should read its brief in the language it is writing in.
Structural commentary, rationale, and file-maintenance notes are in **English**, for
whoever next edits this file. This split is a judgement call, not a spec requirement —
see the report for the reasoning.

---

## ⚠️ Architecture note — read this before touching Prompt 4 or restoring v2's Prompt 5

v2's Prompt 5 ("Scene Breakdown — VideoScript JSON per Part") asked the model to author
a hand-built `VideoScript` JSON with a per-scene `visuals[0].prompt` field, then paste
that JSON into AIVDO's `edited_script` request field. **That mechanism no longer
exists in this channel's pipeline.**

Checked directly against `make_request_parts.build_request` (2026-08-21): the payload
it builds carries `text` (bare narration), `render_mode`, `video_intent`,
`images_only`, `visual_style`, `voice_name`, `language`, and duration/format fields —
**no `edited_script` key at all.** AIVDO derives scenes and per-scene visuals
server-side from the bare narration string, in `render_mode="fast"` +
`video_intent="faceless_youtube"` mode. This is also what spec §6.4 found from the
other direction: the shipped `REQUEST_PART_1.json` carried "3,294 chars of plain
prose" with every scene marker and OVERLAYS line already stripped, and AIVDO
"re-derives its own scenes from the bare text."

**The consequence is not cosmetic.** In v2, visual-subject discipline (the "hot-dog
rule": no named real person, anchor-object variety, negative prompts) was enforced in
a *separate authoring step* — a human or model wrote per-scene image prompts and could
patch them independently of the narration. In v3, **the narration text is the only
channel-supplied visual signal AIVDO ever sees.** If a script describes what a real,
named person looks like or wears, that description is the closest thing to an image
prompt AIVDO gets for that scene. The faceless rule and the anchor-variety discipline
therefore had to move from "write better image prompts" to "write narration that is
safe to become an image prompt" — see the Global constraints below and Prompt 3A/3B/4.

**Do not re-introduce a per-scene visual-prompt-authoring prompt** unless
`make_request_parts.py` grows an `edited_script` field again. Until then it would
produce a JSON blob nothing in the pipeline reads.

---

## Global Voice, Register & Visual-Discipline Constraints

Apply these to the output of **every** prompt below. They override anything later in
this file. Most script prompts restate the load-bearing ones inline (register, ครับ,
punctuation) because a model given only prompt 3A in isolation should still get them
right — but this section is the canonical statement.

### เสียงและการปิดท้าย (Voice & sign-off)

ผู้บรรยายคือ **Sadaltager เสียงชาย สไตล์ normal (ล็อกไว้แล้วตามสเปก §5.4, ตัดสินใจใหม่ 2026-08-21
แทนที่ Erinome เสียงหญิง)** อนุภาคท้ายประโยคต้องผูกกับเพศเสียงเสมอ **ปิดท้ายทุกตอนด้วย ครับ
หรือ นะครับ ห้ามใช้ ค่ะ/นะคะ เด็ดขาด** แม้แต่ในตัวอย่างหรือ draft นี่คือบั๊กที่เคยเกิดจริงกับเสียง
Erinome ตอนช่วงที่ผู้บรรยายยังเป็นเสียงหญิง (สคริปต์ที่ปิดด้วยอนุภาคชายหลุดเข้ามาโดยไม่ตั้งใจ) และ
เป็นสิ่งที่ `thai_lint.py` ตรวจจับโดยอัตโนมัติ โดยอ่านค่าเพศผู้บรรยายจาก
`make_request_parts.NARRATOR_GENDER` — ถ้าเสียงเปลี่ยนอีกในอนาคต กฎนี้จะสลับทิศทางเองโดยไม่ต้อง
แก้โค้ด

### เครื่องหมายวรรคตอนต้องห้าม (Banned punctuation)

**ห้ามใช้ em dash (—) และห้ามใช้ double hyphen (--) ในบทพูดเด็ดขาด** ใช้จุด จุลภาค หรือ
วงเล็บแทน และห้ามใช้แม้แต่ในข้อความส่วนที่เป็นพรอมต์ภาษาไทย (ในกรอบโค้ดของแต่ละ Prompt
ด้านล่างของไฟล์นี้) เพราะโมเดลที่มาอ่านพรอมต์นั้นอาจคัดลอกรูปแบบไปโดยไม่ตั้งใจ นี่คือกฎเดียว
กับข้อจำกัดของ v2 (ซึ่งเป็นความชอบส่วนตัวของเจ้าของช่อง) เพียงแต่เปลี่ยนภาษาที่บังคับใช้จาก
อังกฤษเป็นไทย

### ทะเบียนภาษา (Register): กฎที่สำคัญที่สุดของสเปกนี้

**ห้ามแปลจากภาษาอังกฤษ ห้ามเขียนแบบ "ภาษาเขียน" ที่แปลตรงตัว** สคริปต์ต้องเป็นภาษาพูด
ธรรมชาติ แบบที่คนเล่าเรื่องพูดกับเพื่อน ไม่ใช่แบบที่คนอ่านบทความให้ฟัง Thai แยกทะเบียนภาษาพูด
กับภาษาเขียนชัดเจนกว่าอังกฤษมาก และประโยคที่แปลมาตรงๆ จะฟังดูแข็งและเหมือนเครื่องพูด
ต่อให้เสียงสังเคราะห์ดีแค่ไหนก็ตาม จุดสังเกต: อ่านออกเสียงประโยคที่เขียนดัง ๆ ถ้าไม่มีใครพูดแบบนี้
ในชีวิตจริง ให้เขียนใหม่

**กฎที่สอง: ความเข้มงวดต้องไม่แลกมาด้วยความเข้าใจยาก (ย่อยง่าย)** เกตบรรณาธิการเข้มงวด
เรื่องความถูกต้องอยู่แล้ว (§8) นั่นคือจุดต่างที่คู่แข่งไม่มี แต่สคริปต์ที่ถูกต้องทุกจุดแล้วฟัง
ไม่รู้เรื่องก็ยังนับว่าล้มเหลว อธิบายศัพท์เทคนิคทันทีที่พูดถึงครั้งแรกด้วยประโยคสั้นๆ แบบคุย
("Free File คือโปรแกรมที่รัฐบาลจับมือกับบริษัทซอฟต์แวร์ให้คนยื่นภาษีฟรี") ไม่ใช่แบบวิชาการ
ระดับที่เหมาะสม: สารคดี YouTube ภาษาไทยที่คนทั่วไปดูจบได้โดยไม่ต้องหยุดคิด (มาตรฐานเดียว
กับที่ ด.ดล Blog ใช้) ไม่ใช่ Bloomberg Businessweek แบบที่ v2 ใช้เป็นเกณฑ์ นั่นคือทะเบียน
ภาษาเขียนสำหรับผู้อ่านธุรกิจ ไม่ใช่ทะเบียนภาษาพูดสำหรับผู้ฟัง

**ห้ามใช้วลีเกลื่อนกลาดแบบ AI:** "ในโลกที่เปลี่ยนแปลงอย่างรวดเร็ว", "มาเจาะลึกกันเลย",
"อย่างที่เราทราบกันดี", "ก่อนอื่นต้องบอกก่อนว่า", "ปฏิเสธไม่ได้ว่า", "ไม่รอช้า ไปดูกันเลย"
พูดตรงๆ เจาะจง เหมือนคนที่รู้เรื่องจริงๆ กำลังเล่าให้ฟัง

### วินัยเรื่องภาพ: ห้ามบรรยายบุคคลจริงที่มีตัวตน (Visual-subject discipline)

**นี่คือความล้มเหลวที่เคยเกิดขึ้นจริงกับช่องนี้ ไม่ใช่ความเสี่ยงสมมติ** เพราะสถาปัตยกรรม v3
ไม่มีขั้นตอนเขียน image prompt แยกอีกต่อไป (ดู Architecture note ด้านบน) **บทพูดคือสัญญาณ
ภาพเดียวที่ระบบสร้างภาพได้รับ** ดังนั้น:

- **ห้ามบรรยายรูปลักษณ์ทางกายภาพ เครื่องแต่งกาย หรือท่าทางเฉพาะตัวของบุคคลจริงที่มีตัวตน**
  แม้จะไม่เอ่ยชื่อตรงๆ ก็ตาม ถ้าคำบรรยายทำให้จำได้ทันทีว่าเป็นใคร (เช่น "เสื้อคอเต่าสีดำ" ของ
  Steve Jobs, "เสื้อฮู้ดสีเทา" ของ Mark Zuckerberg) ก็ยังผิดกฎ silhouette ที่จำได้โดยไม่มีหน้า
  ก็ยังนับว่าเปิดเผยตัวตนอยู่ดี
- แทนที่ด้วยบทบาท การกระทำ การตัดสินใจ เอกสาร บริษัท สถานที่ วัตถุ: "ผู้ก่อตั้งบริษัท",
  "ซีอีโอ", "ทีมผู้บริหาร", "คนเขียนอีเมลฉบับนั้น" (ไม่ใช่รูปร่างหน้าตา)
- **ความหลากหลายของภาพหลักต่อฉาก (anchor-object variety, สืบทอดจาก v2's "hot-dog rule"
  แต่ปรับใหม่ทั้งหมด):** แต่ละฉากควรมีภาพหลักในหัวคนละแบบกัน (เอกสาร กราฟ อาคาร ห้องประชุม
  มือถือ ป้ายบริษัท ถนน) วัตถุเดียวไม่ควรครองความคิดของบทพูดเกินราวๆ 30% ของฉากทั้งหมด ถ้าทุกฉาก
  พูดถึงวัตถุเดียวกันซ้ำ ระบบสร้างภาพอัตโนมัติมักจะวนภาพซ้ำตาม
- `video_intent="faceless_youtube"` มีการกันหน้าคนในระดับเซิร์ฟเวอร์อยู่แล้ว (ชั้นที่สอง) แต่
  อย่าพึ่งพาชั้นนั้นอย่างเดียว วินัยที่บทพูดต้องทำเองคือชั้นแรก และชั้นแรกคุมได้แค่ตอนเขียน

### การอ้างอิงแหล่งข้อมูลปฐมภูมิ (Primary-source naming)

อ้างชื่อเอกสารต้นทางจริงเสมอ ไม่ใช่คำกลางๆ: "ตามคำร้องของ ก.ล.ต.", "ตามแถลงการณ์ของบริษัท",
"ตามรายงานของ ProPublica" ไม่ใช่ "มีรายงานว่า..." หรือ "ว่ากันว่า..." ถ้าไม่มีแหล่งปฐมภูมิรองรับ
ให้ตัดข้อเท็จจริงนั้นออก ไม่ใช่เขียนให้คลุมเครือแล้วเก็บไว้

### CTA ติดตามช่อง (Subscribe CTA, retained from v4.6.3: the one conversion unlock that
empirically held)

ปิดท้ายทุกตอนด้วยประโยคชวนติดตามสั้นๆ เป็นธรรมชาติ ไม่ใช่โฆษณาแข็งๆ ตัวอย่างที่ใช้ได้จริง
(บรรทัดที่ EP01 เผยแพร่จริง ผ่านทั้งชุดทดสอบของ `thai_lint.py` และ human gate):

> กดติดตาม Disclosed ไว้นะครับ

**ห้ามอ้างความถี่การอัปโหลด (cadence) ที่ pipeline ยังทำไม่ได้จริงในตอนนี้.** EP01 เคยมีร่าง
ที่ปิดท้ายด้วย "เราปล่อยคลิปใหม่ทุกวันครับ" แล้วถูกตัดออกใน round 2 ของ human review เพราะเป็น
ข้อมูลเท็จ: Routine A รันเฉพาะวันธรรมดา (weekdays-only), การเปลี่ยนเป็น 7 วัน/สัปดาห์ยังไม่เกิดขึ้น
จริง (ค้างอยู่ตามสเปก §6), และตอน EP01 จะเผยแพร่นั้นยังไม่มีตอนภาษาไทยแม้แต่ตอนเดียวที่ออกอากาศ
มาก่อน — จึงไม่มีความถี่ใดๆ ให้อ้างอิงได้ด้วยซ้ำ CTA ที่เคยได้ผลจริง (v4.6.3, English run) คือ
CTA ที่ตรงกับความจริง ไม่ใช่ CTA ที่ฟังดูมั่นใจ; สัญญาความถี่ที่เกินจริงคือคำกล่าวอ้างแบบเดียว
กับที่ editorial gate จะตัดทิ้งถ้าเจอที่อื่นในสคริปต์ — กฎนี้ต้องใช้กับ CTA เหมือนกัน ไม่มีข้อยกเว้น
ให้จบ CTA ด้วยคำชวนติดตามเฉยๆ แบบบรรทัดข้างบน จนกว่าจะมีหลักฐานจริงว่า pipeline รักษาจังหวะ
ที่จะอ้างได้ (เช่น ตอนภาษาไทยออกจริงตามผังหลายสัปดาห์ติดต่อกัน) ห้ามพูดถึง aivdo.ai ในบทพูดของ
วิดีโอหลัก (นั่นเป็นงานของคำบรรยายใต้คลิปและ pinned comment ไม่ใช่บทพูด) ห้ามพูดถึง "like button"
หรือกลไกของ YouTube ตรงๆ ในบทพูด

---

## Output format contract — every script must match `split_script.parse_scenes`

Verified against `split_script.py` (2026-08-21) and the two real shipped scripts in
`Daily/`. The parser is authoritative — if a prompt's output disagrees with this
contract, the prompt is wrong, not the parser.

```
# SCRIPT #<เลข EP>: <หัวข้อสั้นๆ เป็นภาษาอังกฤษหรือไทยก็ได้ สำหรับมนุษย์อ่าน>
# <จำนวนคำ/ตัวอักษรโดยประมาณ -> นาทีที่คาดไว้>
# <โน้ตโครงสร้าง: cold open ฉากไหน, CTA ฉากไหน, cross-ref ตอนไหนถ้ามี>

===== PART 1 =====

[Scene 1 | high] <ป้ายกำกับสำหรับบรรณาธิการเท่านั้น ไม่ถูกอ่านออกเสียง>
OVERLAYS: '<แคปชันสั้นๆ 1>' | <แคปชันสั้นๆ 2>
<บทพูดของฉากนี้ หนึ่งย่อหน้า ภาษาพูดธรรมชาติ>

[Scene 2 | medium] <ป้ายกำกับ>
OVERLAYS: <แคปชัน>
<บทพูด>

===== PART 2 =====

[Scene N | ...] ...
```

Rules the parser enforces mechanically (`split_script.parse_scenes`, read 2026-08-21):

- A scene marker is a line starting with `[Scene <number> | <word>]` — the word after
  `|` is the energy tag (`high` / `medium` / `low` by convention; the parser accepts
  any single word but these three are what the rest of the pipeline expects).
- **Anything after the closing `]` on that same line is discarded — never parsed as
  narration.** Use it as a human-readable editorial label only ("Hook: ...", "The
  reveal: ...").
- Lines starting with `#`, `OVERLAYS:`, or `=====` are skipped entirely.
- Blank lines are skipped.
- Every other non-blank line becomes narration for the current scene, joined with
  spaces. Multiple lines under one scene marker are fine — they become one paragraph.
- **A script with zero `[Scene N | energy]` markers raises `ValueError`.** This is the
  single most common way a generated script fails to ship — always include the
  markers, never just plain prose.

`OVERLAYS:` lines are **not currently consumed by the render pipeline** — grepped the
codebase 2026-08-21 and only `split_script.py` references the literal string, to skip
it. They exist today as (a) a human/QA aid matching the shipped-script convention, and
(b) the natural home for the Human Fingerprint Checklist's "primary-source citation
visible on screen in first 90s" once Thai renderer text-burn lands (spec §6.2, still
blocked on the §9 font prerequisite). Write them, but don't assume they render yet.

`===== PART N =====` lines are a **human pacing aid only** — the parser skips them, and
the actual part boundaries are computed automatically by `split_script.split_into_parts`
from the character budget, not from where you put this marker. Use it to track your own
narrative arc (where does the cliffhanger sit), not to hit an exact split point.

---

## 1. Saturation Audit — run before every topic is chosen (spec §7.7)

```
คุณกำลังตรวจสอบว่าหัวข้อ "{หัวข้อที่กำลังพิจารณา}" เคยถูกทำเป็นคลิปโดยช่องคู่แข่งในตลาดไทย
มาก่อนหรือยัง และถ้าเคย เคยทำแล้วผลเป็นอย่างไร

ค้นหาในช่องต่อไปนี้ (ทำทุกช่อง อย่าข้าม):

1. ด.ดล Blog (Geek Daily / Geek Story / Geek Talk / Geek Monday): ค้นที่
   https://www.youtube.com/@mrtharadhol/search?query={หัวข้อ} (คู่แข่งหลักของ Lane B)
   นี่คือช่องที่ปล่อยคลิปราว 2 ตอน/วัน สะสมกว่า 2,600 ตอน
2. ลงทุนแมน (Longtunman): สำหรับเรื่องธุรกิจไทย/SEA โดยเฉพาะ ช่องนี้ครองพื้นที่เรื่อง
   corporate story ของไทยอยู่แล้ว ให้ตรวจก่อนอ้างว่า "ไม่มีใครเล่า"
3. The Secret Sauce
4. Mission to the Moon
5. ช่อง AI/เทคโนโลยีไทยที่กำลังมาแรง (เช่นช่องของโมชิ): คู่แข่งหลักของ Lane A เพราะเป็น
   ส่วนที่มีการแข่งขันสูงที่สุดในตลาดนี้ตอนนี้

สำหรับแต่ละช่อง บันทึก:
- เจอคลิปที่ตรงหรือใกล้เคียงหรือไม่ (ชื่อตอน, EP, ยอดวิว, อายุคลิป)
- ถ้าเจอ: คลิปนั้นยังใหม่/สดอยู่ไหม (สำหรับ Lane A ข่าวเก่าเกิน 2-3 วันคือปิดประเด็นแล้ว) หรือ
  เป็นเรื่องเก่าที่เล่าไปนานแล้วและมีมุมใหม่ที่ยังไม่มีใครแตะ
- ถ้าไม่เจอ: **อย่าตีความว่าเป็นช่องว่างให้รีบเข้าไปทำทันที** ด.ดล Blog ทำคลิปราว 2 ตอน/วัน
  ครอบคลุมเทคโนโลยีแทบทุกมุม ถ้าหัวข้อนี้ไม่มีใน 2,600 ตอนของช่องนั้นเลย เหตุผลที่เป็นไปได้
  มากที่สุดคือหัวข้อนี้ไม่เวิร์กกับผู้ชมไทย ไม่ใช่ว่ายังไม่มีใครคิดถึง ให้ประเมินต่อว่า "ไม่เจอ"
  ครั้งนี้เพราะอะไร: (ก) แบรนด์/บริษัทนี้แทบไม่มีตัวตนในไทยเลย (เหมือนกรณี TurboTax,
  MoviePass, DocuSign ที่พิสูจน์แล้วว่าไม่เวิร์ก) หรือ (ข) หัวข้อนี้เกี่ยวข้องกับผู้ชมไทยจริงๆ
  แค่ยังไม่มีคนทำ (เหมือนกรณี IKEA, Tupperware ที่ผ่านการกรองมาแล้ว)

สรุปท้ายสุด: หัวข้อนี้ **ผ่าน / ไม่ผ่าน** เกณฑ์ พร้อมเหตุผล 1 บรรทัด และถ้าผ่าน ให้เสนอมุมที่
ยังไม่มีใครเล่า (angle) 1 อย่าง

หัวข้อที่มีคนทำไปแล้วและยังใหม่ (Lane A) หรือทำซ้ำจนอิ่มตัว (Lane B, เช่น Blackberry ที่
ด.ดล Blog ทำไปแล้ว 2 ครั้ง) ให้ตัดทิ้งตรงนี้ อย่าส่งต่อไปขั้นเขียนบท
```

**Note for Task 6 and beyond:** run this per candidate, not once for a shortlist —
each candidate needs its own five-channel pass. A candidate that "passes" still needs
the relevance judgement call in the prompt above recorded in `REVIEW.md`, since that
judgement is exactly what §7.4's back-catalogue audit got right in English and this
audit exists to repeat in Thai.

---

## 2. Title Generator — rotate the eleven formulas (spec §5.4)

```
หัวข้อตอนนี้: {หัวข้อ}
เลน: {Lane A - Disclosed Daily | Lane B - Disclosed Story}
ชื่อตอน 8-10 ตอนล่าสุดพร้อมสูตรที่ใช้ไปแล้ว: {วางรายการ "ชื่อตอน: สูตรที่ใช้"}

สูตรชื่อตอนทั้ง 11 แบบของช่อง (ต้องหมุนใช้ ห้ามให้สูตรเดียวครองทั้งเดือน):

| สูตร | ความหมาย |
|---|---|
| ทำไม X ถึง Y? | ทำไม X ถึงเกิด Y |
| ใครฆ่า X? | ใครเป็นคนทำให้ X จบ |
| เกิดอะไรขึ้นกับ X? | เกิดอะไรขึ้นกับ X |
| อวสาน X | จุดสิ้นสุดของ X |
| วาระสุดท้ายของ X? | ช่วงท้ายของ X |
| จุดจบ X | การล่มสลายของ X |
| หายนะ X! | ความหายนะของ X |
| เปิดแฟ้มคดี X | เปิดเผยคดี/เรื่องราวของ X |
| เจาะลึก X / ล้วงลึก X | เจาะลึกเรื่องราวของ X |
| ย้อนรอย X | ย้อนกลับไปดูเส้นทางของ X |
| X จะรอดมั๊ย? | X จะรอดหรือไม่ |

ขั้นตอน:
1. ดูจากรายการ 8-10 ตอนล่าสุด: สูตรไหนถูกใช้ไปแล้วมากกว่า 2 ครั้งในช่วงนี้ ตัดสูตรนั้นออก
   จากตัวเลือก (ไม่ใช่ห้ามตลอดไป แค่ห้ามใช้ซ้ำจนกว่าจะครบรอบ)
2. เลือกสูตรที่เหลือ 4 แบบที่เข้ากับโทนของหัวข้อนี้ที่สุด (เช่น หัวข้อที่เป็นข่าวสดเข้ากับ
   "เกิดอะไรขึ้นกับ X?" ได้ดีกว่า "อวสาน X" ซึ่งฟังดูจบไปแล้ว)
3. เขียนชื่อตอนจริง 4 แบบ ตามสูตรที่เลือก แต่ละแบบต้องมี X (หัวข้อ) ที่เจาะจง ไม่ใช่คำกลางๆ
4. ต่อท้ายด้วย series tag และเลข EP: "<ชื่อตอนภาษาไทย> | {series_tag} EP<เลข>"
   (series_tag คือ "Disclosed Daily" สำหรับ Lane A หรือ "Disclosed Story" สำหรับ Lane B ใช้
   ตัวเลข EP ของเลนนั้นๆ โดยเฉพาะ ไม่ใช่เลขรวมของทั้งช่อง)
5. ให้คะแนนแต่ละชื่อ: ช่องว่างความอยากรู้ (curiosity gap) สูง/กลาง/ต่ำ พร้อมเหตุผล 1 บรรทัด
6. เลือกตัวที่ดีที่สุด 1 ชื่อ พร้อมเหตุผลว่าทำไมสูตรนี้เหมาะกับหัวข้อนี้เป็นพิเศษ

ห้ามเสนอชื่อที่เป็น clickbait เกินจริงหรือสัญญาสิ่งที่บทพูดไม่ได้พิสูจน์
```

**On the tag format — RESOLVED, no need to re-ask.** This file flagged that spec §5.1's
opening example read `| Disclosed EP01` while its own lane table assigned
`Disclosed Daily` / `Disclosed Story` as separate tags with independent counters. That
was a real spec defect, and flagging it rather than silently picking one was correct.

The spec resolved it on 2026-08-21, the same way this file did: **the full lane tag
carries the counter, and each lane counts independently.** `| Disclosed Daily EP01` and
`| Disclosed Story EP01` both exist; a bare `Disclosed EPnn` does not. ด.ดล Blog runs
four series on four separate counters, and a shared counter would make each lane's
numbering jump unpredictably, destroying the franchise signal the counter exists to send.

See spec §5.1's "Resolved 2026-08-21" block. Use the lane tag.

---

## 3A. Script Writer — Lane A (current AI/tech news, 8–10 min, fast gate)

```
เขียนบทพูดภาษาไทยสำหรับคลิปสารคดีไร้หน้าคน (faceless documentary) ความยาวพูด 8-10 นาที
หัวข้อ: {หัวข้อข่าวเทคโนโลยี/AI ปัจจุบัน}

**นี่คือ Lane A ("Disclosed Daily"): ข่าวเทคโนโลยี/AI ที่กำลังเกิดขึ้นตอนนี้ ไม่ใช่ประวัติศาสตร์**
อายุขัยของเรื่องนี้คือ "วัน" ไม่ใช่ "ปี" ทุกอย่างต้องเร็วและแม่นในคราวเดียวกัน

**งบตัวอักษร:** ใช้ฟังก์ชัน `thai_budget.chars_for_duration(seconds, density)` เป็นตัวกำหนด
ความยาวจริง อย่ากะเอง คำนวณจากวินาทีเป้าหมาย (8-10 นาที = 480-600 วินาที) และ density
"mixed" (บทพูดสารคดีทั่วไปที่มีทั้งร้อยแก้วและตัวเลขปนกัน) ตัวอย่างการคำนวณ (2026-08-21,
คำนวณใหม่ทุกครั้งที่ใช้จริง อย่าจำตัวเลขนี้ไปใช้ตรงๆ): 480 วินาทีที่ mixed ≈ 5,900 ตัวอักษร,
600 วินาทีที่ mixed ≈ 7,400 ตัวอักษร ถ้าช่วงไหนของบทมีตัวเลข/สถิติแน่นมาก ให้เผื่อด้วย
density "figures" (เร็วกว่า mixed) แทนที่จะกะรวมเป็น mixed ทั้งหมด

**วินัยแหล่งข้อมูลของ Lane A (เข้มกว่า Lane B เพราะเร็วกว่า, ตามเกต News/fast path §8):**
- ทุกข้อเท็จจริงต้องมาจากแหล่งปฐมภูมิหรือประกาศทางการของบริษัท/หน่วยงานนั้นเอง (blog post,
  press release, filing, tweet ทางการของบัญชีองค์กร) ระบุชื่อแหล่งบนจอ (ผ่าน OVERLAYS)
- ถ้าเรื่องมีข้อโต้แย้งหรือยังไม่ยืนยันชัด ต้องมีรายงานอิสระอย่างน้อย 2 แหล่งยืนยันตรงกัน
- **ห้ามพูดคาดเดาราวกับเป็นข้อเท็จจริงที่ยืนยันแล้ว** ถ้ายังไม่มีแหล่งปฐมภูมิรองรับ ให้เขียน
  ว่า "ยังไม่มีการยืนยัน" หรือตัดประเด็นนั้นออกไปเลย เรื่องที่ยืนยันไม่ทันในงบเวลาของ Lane A
  (~15 นาทีตามเกต) ให้ **ตัด ไม่ใช่ปล่อยผ่านแบบกั๊กคำ**
- ถ้าวันที่จะเผยแพร่จริงยังไม่แน่นอน (เช่น รอ pipeline หรือ infra พร้อม) ให้เลือกเรื่องที่มี
  เส้นเรื่องยืดได้หลายสัปดาห์ (developing story) แทนเรื่องที่จบในวันเดียว เพื่อไม่ให้ประเด็น
  หมดอายุก่อนเผยแพร่ เงื่อนไขนี้ใช้เฉพาะตอนวันเผยแพร่ไม่แน่นอนเท่านั้น ถ้า Routine A
  รันได้ตามปกติทุกวันแล้ว ให้เลือกเรื่องสดที่สุดได้เต็มที่ตามปกติของ Lane A

โครงสร้าง (สำหรับวางแผนเองเท่านั้น ไม่ต้องใส่หัวข้อพวกนี้ในบทพูดจริง):
- เปิดฉากด้วยเหตุการณ์จริง ไม่ใช่เปิดด้วยการวิเคราะห์ (scene-first ไม่ใช่ argument-first)
- ประโยคแรกต้องมีชื่อบริษัท/ผลิตภัณฑ์ที่เจาะจง วันที่หรือช่วงเวลาที่ชัด และตัวเลขอย่างน้อยหนึ่งตัว
- เนื้อหา 2-4 ช่วง แต่ละช่วงอ้างแหล่งปฐมภูมิที่ต่างกัน
- หาจุดที่เชื่อมกับตอนก่อนหน้าของ Disclosed ได้ตามธรรมชาติ ถ้ามี (เช่น เคยเล่าเรื่องบริษัทนี้
  หรือประเด็นคล้ายกันมาก่อน) ถ้าไม่มีจริงๆ อย่าฝืนใส่
- ทิ้งช่องว่างไว้ 1 จุดสำหรับ "ข้อสังเกตหรือข้อแก้ไขที่เจ้าของช่องพิมพ์เอง" (Human Fingerprint
  Checklist ข้อ 2) ทำเครื่องหมายไว้ในบทร่างว่า `[จุดใส่ caveat ของเจ้าของช่อง]` แล้วปล่อยให้
  มนุษย์เขียนทับตรงนั้นจริง อย่าแต่งเองแล้วอ้างว่าเป็นความเห็นส่วนตัวของเจ้าของช่อง
- ปิดท้ายด้วย CTA ติดตามช่อง (ดูส่วน Global constraints ด้านบน) ปิดด้วย ครับ/นะครับ เท่านั้น

**ทะเบียนภาษา:** ภาษาพูดธรรมชาติ ไม่แปลจากอังกฤษ ย่อยง่ายแต่ไม่ลดความแม่นยำ (ดู Global
constraints) ห้าม em dash, ห้าม double hyphen, ห้ามวลี AI-cliché

ส่งมอบเป็นบทพูดร้อยแก้วต่อเนื่อง แบ่งเป็นย่อหน้าตามจังหวะความคิด (แต่ละย่อหน้า = แนวคิดภาพ
เดียวที่ชัดเจน เพราะย่อหน้านี้จะกลายเป็นสัญญาณภาพเดียวที่ระบบสร้างวิดีโอได้รับ ดูหัวข้อ
Architecture note ด้านบนของไฟล์) **ยังไม่ต้องใส่ [Scene N | energy] ตอนนี้** ขั้นตอนนั้นเป็นของ Prompt 4
```

---

## 3B. Script Writer — Lane B (postmortems & curiosity, 15–20 min)

```
เขียนบทพูดภาษาไทยสำหรับคลิปสารคดีไร้หน้าคน ความยาวพูด 15-20 นาที
หัวข้อ: {หัวข้อ}

**นี่คือ Lane B ("Disclosed Story"): เรื่องที่จบไปแล้ว (postmortem, "ทำไม X ถึงล่ม") หรือเรื่องที่
คนสงสัยมานาน (curiosity) เน้นหนักไปทางเทคโนโลยีมากกว่าธุรกิจล้วนๆ (spec §5.3, ไม่ใช่
business-case-only แบบเดิม) แต่ยังคงครอบคลุมธุรกิจ/consumer curiosity ได้ ไม่จำกัดเฉพาะเทค**

**งบตัวอักษร:** เช่นเดียวกับ Lane A ใช้ `thai_budget.chars_for_duration(seconds, density)`
คำนวณจากวินาทีเป้าหมายจริง (15-20 นาที = 900-1,200 วินาที) ที่ density "mixed" ตัวอย่าง
คำนวณ (2026-08-21, คำนวณใหม่เสมอ): 900 วินาทีที่ mixed ≈ 11,100 ตัวอักษร, 1,200 วินาทีที่
mixed ≈ 14,800 ตัวอักษร

**โหมดของเรื่อง (เลือกให้ตรงกับเกตที่จะใช้ตรวจ, spec §8):**

- **Research / verifiable (ค่าเริ่มต้น):** หัวข้อธุรกิจ/เทคโนโลยีใหม่ที่มีแหล่งปฐมภูมิรองรับ
  ทุกข้อเท็จจริง เขียนแบบยืนยันตรงๆ ได้ ("บริษัทประกาศ...", "ตามคำร้องของ...")
- **Research / attribution:** ถ้าหัวข้อเป็นตำนาน ข่าวลือ หรือเรื่องที่ยังพิสูจน์ไม่ได้ (เช่น
  ทฤษฎีสมคบคิด, การอ้างตัวปริศนา) **ห้ามยืนยันว่าเป็นความจริง ให้ระบุที่มาของคำกล่าวอ้างเสมอ**
  ใช้โครงประโยคแบบ "มีการอ้างว่า...โดย...", "ตามคำบอกเล่าของ...", "ยังไม่มีใครพิสูจน์ได้ว่า..."
  ตลอดทั้งบท ไม่ใช่แค่ตอนเปิด
- **Remake (จากคลังเก่า, เมื่อมีสคริปต์อังกฤษที่ผ่านการตรวจสอบข้อเท็จจริงแล้วและผ่านตัวกรอง
  ความเกี่ยวข้องกับผู้ชมไทย ดูสเปก §7.4, ปัจจุบันคลังนี้ว่างเปล่า 0 เรื่อง):** ใช้สคริปต์เดิม
  เป็น **แหล่งข้อเท็จจริงและโครงเรื่องเท่านั้น** แล้วเขียนบทพูดภาษาไทยใหม่ทั้งหมดในทะเบียน
  ภาษาพูด **ห้ามแปลประโยคต่อประโยค** ตัวเลข ชื่อ วันที่ ต้องตรงกับต้นฉบับทุกจุด (translation
  fidelity) แต่จังหวะประโยค มุก และวิธีเล่าต้องเป็นภาษาไทยธรรมชาติ ไม่ใช่ English syntax
  ที่ใส่คำไทยแทน

โครงสร้าง (วางแผนเองเท่านั้น ไม่ต้องใส่หัวข้อในบทจริง):
- เปิดฉากด้วยเหตุการณ์หรือภาพที่จับต้องได้ (scene-first) ไม่ใช่เปิดด้วยการตั้งคำถามเชิงวิเคราะห์
- เนื้อหา 4-8 ช่วง แต่ละช่วงอ้างแหล่งปฐมภูมิที่ต่างกัน แต่ละช่วงมีภาพหลักในหัวคนละแบบ (ดู
  วินัยเรื่องภาพใน Global constraints)
- เชื่อมโยงกับตอนก่อนหน้าของ Disclosed ถ้าเข้ากันได้ตามธรรมชาติ
- ทิ้งช่องว่างไว้สำหรับ caveat ที่เจ้าของช่องพิมพ์เอง เหมือน Lane A
- ช่วงท้าย: มุมกลับหรือบทสรุปเชิงโครงสร้าง (ไม่ใช่แค่สรุปเหตุการณ์ซ้ำ) ตามด้วย CTA ติดตามช่อง
  ปิด ครับ/นะครับ

**ทะเบียนภาษาและวินัยเรื่องภาพ:** เหมือน Lane A ทุกประการ (ดู Global constraints ด้านบน)

ส่งมอบเป็นบทพูดร้อยแก้วต่อเนื่อง แบ่งย่อหน้าตามแนวคิดภาพ ยังไม่ต้องใส่ [Scene N | energy]
```

---

## 4. Scene Breakdown → `SCRIPT.txt` (works for either lane's output)

```
รับบทพูดร้อยแก้วที่เขียนเสร็จแล้ว (จาก Prompt 3A หรือ 3B) แล้วแปลงเป็นไฟล์ SCRIPT.txt ที่
พร้อมส่งเข้าไปป์ไลน์การตัดพาร์ต (split_script.py) โดยไม่ต้องเปลี่ยนเนื้อหาบทพูดเลยแม้แต่
คำเดียว งานของขั้นตอนนี้คือแบ่งฉากและติดป้ายกำกับเท่านั้น

รูปแบบเอาต์พุตต้องตรงตามนี้เป๊ะ (ตรวจสอบกับ split_script.parse_scenes แล้ว):

# SCRIPT #<เลข EP>: <ชื่อหัวข้อสั้นๆ>
# <จำนวนตัวอักษรโดยประมาณ -> นาทีที่คาดไว้>
# <โน้ตโครงสร้าง: cold open ฉากไหน, CTA ฉากไหน, cross-ref ตอนไหนถ้ามี>

===== PART 1 =====

[Scene 1 | high] <ป้ายกำกับสั้นๆ สำหรับบรรณาธิการ>
OVERLAYS: '<แคปชันเด่นที่ 1>' | <แคปชันเด่นที่ 2>
<ย่อหน้าบทพูดของฉากนี้ คัดลอกมาจากบทต้นฉบับตรงๆ ห้ามเปลี่ยนคำ>

[Scene 2 | medium] ...
OVERLAYS: ...
...

กติกาการแบ่งฉาก:
1. **หนึ่งฉาก = หนึ่งย่อหน้าจากบทต้นฉบับ = หนึ่งแนวคิดภาพเดียว** อย่ารวมสองแนวคิดเข้าฉากเดียว
   และอย่าหั่นแนวคิดเดียวออกเป็นหลายฉาก
2. **ห้ามแก้ไข ห้ามถอดคำ ห้ามสรุปย่อบทพูดต้นฉบับ** งานนี้คือติดป้ายกำกับ ไม่ใช่เขียนใหม่
   ทุกประโยคในต้นฉบับต้องปรากฏอยู่ในฉากใดฉากหนึ่งครบถ้วน
3. energy: ฉากแรกและฉากสุดท้ายเป็น "high" ฉากกลางส่วนใหญ่เป็น "medium" แทรก "low" 1-2 ฉาก
   ตรงจุดที่บทพูดผ่อนจังหวะลง (breathing beat) หมายเหตุ: แท็กนี้ยังไม่ถูกส่งต่อไปถึง AIVDO
   จริง (spec §6.4) แต่ยังต้องใส่เพราะ split_script.parse_scenes ต้องใช้เป็น token คู่กับ
   ชื่อฉาก และมีประโยชน์กับมนุษย์ที่อ่านตรวจงาน
4. OVERLAYS: ใส่แคปชันสั้น (ไม่เกิน 6 คำ) ที่สรุปฉากนั้นได้แม้ปิดเสียง เน้นตัวเลข/ชื่อ/วันที่
   ที่เป็นแก่นของฉาก คั่นด้วย `|` ถ้ามีมากกว่าหนึ่งแคปชัน หมายเหตุ: บรรทัดนี้ยังไม่ถูกเรนเดอร์
   ขึ้นจอโดยอัตโนมัติในตอนนี้ (ดู Output format contract ด้านบนของไฟล์) แต่ยังต้องเขียนไว้
   เพราะเป็นที่ที่การอ้างอิงแหล่งข้อมูลปฐมภูมิ (Human Fingerprint Checklist ข้อ 1) ควรอยู่
   เมื่อการเบิร์นตัวอักษรไทยพร้อมใช้งาน
5. **ห้ามบรรยายรูปลักษณ์บุคคลจริงในป้ายกำกับหรือ OVERLAYS เช่นเดียวกับในบทพูด** (ดู Global
   constraints) ป้ายกำกับควรพูดถึงเหตุการณ์/เอกสาร ไม่ใช่รูปคน

ตรวจสอบก่อนส่งมอบ:
- มีเครื่องหมาย [Scene N | energy] อย่างน้อย 1 ฉาก (ถ้าไม่มีเลย split_script.parse_scenes
  จะ raise ValueError ทันที)
- ไม่มี — หรือ -- ที่ไหนเลยในบทพูด
- ทุกฉากปิดท้าย (ฉากสุดท้าย) ด้วย ครับ หรือ นะครับ ไม่มี ค่ะ/คะ ที่ไหนเลย
- ทุกฉากมีตัวอักษรไทยอยู่จริง (ไม่ใช่บทที่ยังไม่แปล)
```

**Why this prompt is lane-agnostic:** the scene-tagging mechanics are identical for
an 8-minute Lane A script and a 20-minute Lane B script — only the source text
differs. Keeping it as one prompt avoids duplicating the format contract and reduces
the chance the two drift apart.

---

## 5. Description + Chapters + Citations

```
สคริปต์: {วางบทพูดฉบับสมบูรณ์}
ชื่อตอนที่เลือก: {จาก Prompt 2}
เลข EP และเลน: {เช่น Disclosed Daily EP01}

สร้าง:
1. คำบรรยายใต้คลิป (description) ยาวราว 150 คำ สองบรรทัดแรกต้องดึงความสนใจ (hook)
   บรรทัดสุดท้ายเป็น CTA พร้อมลิงก์ aivdo.ai ที่มี UTM:
   https://aivdo.ai/?utm_source=youtube&utm_medium=channel&utm_campaign={slug}&utm_content={video-id}
   (ลิงก์นี้คือสิ่งที่วัด aivdo_trials_attributed ซึ่งเป็น KPI หลักของช่องตอนนี้ ไม่ใช่ยอดวิว
   ห้ามลืมใส่)
2. รายการ chapter พร้อมเวลาโดยประมาณ (ปรับให้ตรงกับ final.mp4 จริงหลังเรนเดอร์)
3. บล็อกแหล่งอ้างอิง 4-7 แหล่ง พร้อม URL (เรียงตามลำดับที่ปรากฏในบทพูด)
4. แฮชแท็ก 10 คำ (3 คำกว้างๆ + 7 คำเจาะจงหัวข้อ)
5. ตัวเลือกความคิดเห็นปักหมุด (pinned comment) แบบร่าง: ลิงก์แหล่งข้อมูลหลัก 1-2 อัน
   **ทำเครื่องหมายไว้ชัดเจนว่านี่คือ "ร่างสำหรับเจ้าของช่องตรวจและพิมพ์ใหม่เอง" ห้ามให้ระบบ
   โพสต์ข้อความนี้ตรงๆ** ช่องนี้เคยถูกจับได้ว่าตอบคอมเมนต์ด้วย AI มาก่อน กฎของช่องคือ
   ความคิดเห็นทุกอันต้องพิมพ์เองโดยเจ้าของช่อง

ต่อท้ายด้วยข้อความลิขสิทธิ์นี้เสมอ คำต่อคำ ห้ามแก้ไขหรือย่อ:

---
Disclosed เป็นเนื้อหาวิเคราะห์และแสดงความคิดเห็นอิสระ ไม่มีความเกี่ยวข้องกับบริษัทที่กล่าวถึง
เครื่องหมายการค้า โลโก้ และทรัพย์สินทางแบรนด์ทั้งหมดที่ปรากฏเป็นของเจ้าของลิขสิทธิ์นั้นๆ
ใช้เพื่อการอ้างอิง วิจารณ์ และการศึกษาเท่านั้น
---

ทำเครื่องหมายแหล่งข้อมูลใดที่ต้องเสียเงินอ่าน (paywalled) และเสนอแหล่งสำรองที่เข้าถึงได้ฟรี
```

---

## 6. Thumbnail Concept — text-as-hero, Thai

```
สคริปต์: {วางบทพูด}
ชื่อตอน: {จาก Prompt 2}

สร้างแนวคิดปกคลิป (thumbnail) 3 แบบ ทุกแบบต้องเป็น **text-as-hero แบบภาษาไทย** ตามสเปกช่อง
(§5.4) ข้อความไทยตัวใหญ่คือพระเอกของภาพ ไม่ใช่รูปคน

สำหรับแต่ละแบบ ระบุ:
1. ข้อความหลักบนปก (ไม่เกิน 4-6 คำ ต้องอ่านได้ชัดที่ขนาด 320px บนมือถือ)
2. องค์ประกอบภาพพื้นหลัง (ฉาก/วัตถุ ไม่ใช่คน ไม่มีโลโก้ที่อ่านออกได้ของแบรนด์จริง)
3. โทนสี (3 รหัสสี hex)
4. คำเตือนเรื่องคน: **ห้ามมีใบหน้า ห้ามมีรูปคนที่ระบุตัวตนได้ ห้ามมี silhouette ที่จำได้ว่า
   เป็นใคร** (กฎเดียวกับ Global constraints ของบทพูด)

ตัวเลือกเส้นทางผลิต: ปัจจุบันการเบิร์นตัวอักษรไทยโดยตัวเรนเดอร์เองยังติดอยู่ที่งานโครงสร้าง
พื้นฐาน (Thai font ในเส้นทาง burn-in, spec §9) ดังนั้นให้เขียน brief สำหรับเครื่องมือสร้างภาพ
ภายนอกหรือดีไซเนอร์ไปพลางก่อน ไม่ใช่พึ่งโหมด poster ของ AIVDO

เลือกแบบที่ดีที่สุด 1 แบบ พร้อมเหตุผล และเขียน brief ฉบับสมบูรณ์สำหรับส่งต่อให้ดีไซเนอร์หรือ
เครื่องมือสร้างภาพ
```

---

## 7. Register & Fingerprint Final Pass — run before `machine_check.py`

```
สคริปต์ฉบับ SCRIPT.txt: {วางไฟล์ทั้งหมด}

ตรวจสอบทีละฉาก ([Scene N | energy] แต่ละอัน) และตอบเป็นรายการปัญหา (ถ้าไม่มีปัญหาให้ตอบว่า
"ผ่าน"):

1. **ทะเบียนภาษา:** มีประโยคไหนอ่านแล้วรู้สึกเหมือนแปลจากอังกฤษหรือเป็นภาษาเขียนทางการเกินไป
   ไหม ถ้ามี เขียนใหม่เป็นภาษาพูดธรรมชาติ (คงข้อเท็จจริงเดิมทุกจุด ห้ามเปลี่ยนตัวเลข/ชื่อ/วันที่)
2. **วลี AI-cliché:** มีวลีอย่าง "ในโลกที่เปลี่ยนแปลงอย่างรวดเร็ว", "มาเจาะลึกกันเลย" หรือ
   คำกลางๆ ที่ไม่มีใครพูดจริงหรือไม่ ถ้ามี เขียนใหม่
3. **ค่ะ/ครับ:** สแกนหาคำว่า "ค่ะ" หรือ "คะ" ทุกจุด (ต้องไม่มีเลย เพราะผู้บรรยายเป็นเสียงชาย) และ
   ตรวจว่าฉากสุดท้ายปิดด้วย ครับ หรือ นะครับ จริง
4. **เครื่องหมายวรรคตอน:** สแกนหา — และ -- ทุกจุด (ต้องไม่มีเลย)
5. **บุคคลจริงในบทพูด:** มีฉากไหนบรรยายรูปลักษณ์ เครื่องแต่งกาย หรือท่าทางเฉพาะตัวของบุคคล
   จริงที่มีตัวตนหรือไม่ (ดู Global constraints) ถ้ามี เขียนใหม่ให้พูดถึงบทบาท/การกระทำแทน
6. **ย่อยง่าย:** มีฉากไหนที่ใช้ศัพท์เทคนิคโดยไม่อธิบายครั้งแรกที่พูดถึงหรือไม่
7. **หนึ่งฉากหนึ่งภาพหลัก:** มีฉากไหนที่พูดถึงวัตถุ/ภาพหลักเดียวกันซ้ำเกิน 30% ของฉากทั้งหมด
   หรือไม่ (นับดูว่าวัตถุ/ภาพหลักไหนซ้ำกี่ฉาก)
8. **การันตีคำทับศัพท์ชื่อบุคคล — แยกจากการตรวจข้อเท็จจริง:** สำหรับชื่อบุคคลจริงทุกชื่อที่
   ปรากฏในบทพูด (ไม่ว่าจะเป็นชื่อไทยทับศัพท์จากภาษาอื่นหรือชื่อต่างชาติ) ต้องตรวจสอบ **การสะกด
   คำทับศัพท์ภาษาไทยของชื่อนั้นแยกต่างหาก** จากการตรวจตำแหน่ง คำพูด และวันที่ของบุคคลคนนั้น
   การยืนยันว่าคำพูด/ตำแหน่ง/วันที่ถูกต้อง **ไม่ได้แปลว่าตัวสะกดชื่อภาษาไทยถูกต้องไปด้วย** —
   นี่คือช่องโหว่ที่ระเบียบการตรวจข้อเท็จจริงแบบเดิมมองไม่เห็นโดยธรรมชาติของมันเอง
   คำทับศัพท์ที่ดูสมเหตุสมผลอาจสะกดออกมาเป็นคำที่มีความหมายไม่ได้ตั้งใจ — ตัวอย่างจริงจาก EP01:
   `เชตายวอน` (ทับศัพท์ชื่อ Chey Tae-won) มีคำว่า "ตาย" ซ่อนอยู่ตรงกลาง ทั้งที่ตำแหน่ง คำพูด
   และวันที่ของบุคคลนี้ถูกต้องหมดแล้ว ต้องแก้เป็น `ชเว แทวอน` เมื่อตรวจสอบกับแหล่งข่าวไทยจริง
   ให้ **ค้นหาการสะกดจากสำนักข่าวไทยที่เชื่อถือได้ (เช่น Thairath, RYT9, Infoquest) อย่างน้อย
   หนึ่งแหล่ง** อย่าอนุมานคำทับศัพท์จากชื่อภาษาอังกฤษเอง เมื่อ EP01 เริ่มใช้ขั้นตอนนี้อย่างจริงจัง
   มันจับข้อผิดพลาดเพิ่มได้อีกสองจุดทันที: `ควักโนจุง` (พยัญชนะต้นผิด) → ที่ถูกคือ `กวัก โน-จุง`
   และ `คิมแจจุน` (ไม่มีเว้นวรรค) → ที่ถูกคือ `คิม แจจุน`

ส่งคืนเป็นรายการปัญหาต่อฉาก พร้อมประโยคที่เขียนใหม่แล้ว (ถ้ามีปัญหา) หลังจากนี้ให้รัน
`thai_lint.py` และ `machine_check.py` ต่อตามลำดับในสเปก §8 พาสนี้เป็นการเตรียมความพร้อม
ก่อนถึงสองขั้นตอนนั้น ไม่ใช่ตัวแทนของมัน
```

---

## How to use this library

Mapped to spec §8's four gate modes:

| Gate mode | Prompts, in order |
|---|---|
| **News / fast path** (Lane A) | 1 (audit) → 2 (title) → 3A (script) → 4 (scene breakdown) → 7 (register pass) → `machine_check.py` → human sourcing → `python3 thai_lint.py Daily/<slug>/SCRIPT.txt` → `python3 lint_urls.py Daily/<slug>/` → 5 (description) → 6 (thumbnail) |
| **Research / verifiable** (Lane B) | Same chain with 3B in "Research / verifiable" mode |
| **Research / attribution** (Lane B) | Same chain with 3B in "Research / attribution" mode — never assert, attribute |
| **Remake** | 1 (audit, to confirm the remake still clears Thai relevance) → 3B in "Remake" mode, sourced from the recovered/verified English draft → 4 → 7 → same gate tail |

`thai_lint.py`, run as a script this way, prints every problem it finds and exits
non-zero; a clean script prints an explicit "clean" line and exits 0. Fix everything
it reports, or confirm each is a false positive, before running `lint_urls.py`. Do not
fall back to `python3 -c "from thai_lint import lint_script; ..."` — that path exists in
the implementation plan, not here, and skips the exit-code gate entirely.

`.facts_verified` still blocks render in every mode (unchanged, spec §8). Comment
replies and the pinned-comment final text stay hand-typed by the channel owner in
every mode — prompts here only draft.

**Shorts:** out of scope for this file. Spec §7.6 assigns daily Shorts a Veo hook on
the first 3-5s and the existing character-anchored injustice pattern from
`make_short.py`; that work (plus the Veo prompt guard — no brand names, no named
people, environment only) belongs with Plan 4, not this prompt library.

---

## Dropped from v2, and why

- **American cultural-touchstone gate** ("would a 55-year-old American man
  recognise this") — the entire premise this gate optimised for (English, American
  Browse audience) is the retired strategy. Its replacement is the saturation audit
  above, gated on Thai relevance instead.
- **Second-channel niche scoring** (v2 Prompt 13) — `Business Postmortems` is now a
  settled English archive/showcase channel (spec §4), not an open scoring decision.
- **Monthly revenue diagnostics** (v2 Prompt 12) — built around AdSense RPM math for
  a channel now targeting mixed revenue with `aivdo_trials_attributed` as the primary
  KPI (spec §2). A UTM-tracking diagnostic belongs with the analytics/measurement
  work in Plan 3, not the content-authoring library.
- **English script prompts** (v2 Prompts 4, 4.5) — retired outright; the channel
  writes Thai now, natively, per spec §5.5.
- **v2's Prompt 5 VideoScript JSON schema** — see the Architecture note at the top
  of this file. `make_request_parts.build_request` has no `edited_script` field;
  the mechanism this prompt fed does not exist in v3's pipeline.
- **Sponsorship pitch email, tool-failure fallback, competitor gap-finder,
  retention-killer audit, AIVDO showcase script, feature-highlight short** (v2
  Prompts 9, 11, 14, 15, 16, 17) — none are retired by the spec, but none are named
  in this task's required scope either. They are generic operations prompts whose
  content (metrics, competitor names, tool names) doesn't change with the language
  pivot; porting them untouched would be busywork, not authoring against the spec.
  Left for a future task if the owner wants them in Thai.
