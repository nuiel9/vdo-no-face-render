#!/usr/bin/env python3
"""
aivdo-render: submit 2 /api/generate jobs (Path B), poll, stitch into final.mp4.
Usage: python render.py "<slug_dir>"  (e.g. Daily/2026-04-23_3_theranos-fake-scope/)
"""
import json, os, sys, time, subprocess
from pathlib import Path
import requests

AIVDO_URL     = os.environ["AIVDO_URL"].rstrip("/")
AIVDO_API_KEY = os.environ["AIVDO_API_KEY"]
POLL_S        = int(os.environ.get("AIVDO_POLL_S", "30"))
MAX_WAIT_MIN  = int(os.environ.get("AIVDO_MAX_WAIT_MIN", "130"))   # 120 stuck-job + 10 buffer
XFADE_S       = float(os.environ.get("AIVDO_XFADE_S", "0.5"))      # 0 = hard-cut concat

H = {"X-API-Key": AIVDO_API_KEY, "Content-Type": "application/json"}


def submit(req: dict) -> str:
    r = requests.post(f"{AIVDO_URL}/api/generate", json=req, headers=H, timeout=60)
    r.raise_for_status()
    return r.json()["job_id"]


def poll(job_id: str) -> str:
    deadline = time.time() + MAX_WAIT_MIN * 60
    last = ""
    while time.time() < deadline:
        r = requests.get(f"{AIVDO_URL}/api/jobs/{job_id}", headers=H, timeout=30)
        r.raise_for_status()
        b = r.json()
        line = f"  {job_id[:8]} {b['status']} {b.get('progress',0)}% — {b.get('current_stage','')}"
        if line != last:
            print(line); last = line
        if b["status"] == "completed":
            return b["output_url"]
        if b["status"] == "failed":
            raise RuntimeError(f"Job {job_id} failed: {b.get('error')}")
        time.sleep(POLL_S)
    raise TimeoutError(f"Job {job_id} exceeded {MAX_WAIT_MIN}min")


def download(url: str, dest: Path) -> None:
    with requests.get(url, stream=True, timeout=300) as r:
        r.raise_for_status()
        with open(dest, "wb") as f:
            for chunk in r.iter_content(1 << 20):
                f.write(chunk)


def probe_duration(p: Path) -> float:
    out = subprocess.check_output(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration",
         "-of", "default=nw=1:nk=1", str(p)],
    )
    return float(out.strip())


def stitch(parts: list[Path], final: Path) -> None:
    if XFADE_S <= 0 or len(parts) < 2:
        lst = final.parent / "concat.txt"
        lst.write_text("\n".join(f"file '{p.absolute()}'" for p in parts))
        subprocess.run(
            ["ffmpeg", "-y", "-f", "concat", "-safe", "0",
             "-i", str(lst), "-c", "copy", str(final)],
            check=True,
        )
        return

    durs = [probe_duration(p) for p in parts]
    inputs: list[str] = []
    for p in parts:
        inputs += ["-i", str(p)]

    filters: list[str] = []
    vlabel, alabel = "[0:v]", "[0:a]"
    cum = 0.0
    for i in range(1, len(parts)):
        cum += durs[i - 1]
        offset = cum - XFADE_S * i
        nv, na = f"[v{i}]", f"[a{i}]"
        filters.append(f"{vlabel}[{i}:v]xfade=transition=fade:duration={XFADE_S}:offset={offset:.3f}{nv}")
        filters.append(f"{alabel}[{i}:a]acrossfade=d={XFADE_S}{na}")
        vlabel, alabel = nv, na

    subprocess.run(
        ["ffmpeg", "-y", *inputs,
         "-filter_complex", ";".join(filters),
         "-map", vlabel, "-map", alabel,
         "-c:v", "libx264", "-preset", "medium", "-crf", "18",
         "-c:a", "aac", "-b:a", "192k",
         "-movflags", "+faststart",
         str(final)],
        check=True,
    )


def render_part(base: Path, n: int) -> Path:
    mp4 = base / f"part{n}.mp4"
    if mp4.exists():
        print(f"part{n}.mp4: cached, skip")
        return mp4
    req = json.loads((base / f"REQUEST_PART_{n}.json").read_text())
    # AIVDO v1.8 Cinematic — opt-in for all VDO No Face renders (2026-04-26).
    # render_mode routes every scene through OpenAI gpt-image-2 medium 1536x1024
    # instead of legacy Gemini Flash. video_intent activates the faceless_youtube
    # profile, server-enforcing "no faces" + documentary realism per-scene.
    req["render_mode"] = "cinematic"
    req["video_intent"] = "faceless_youtube"
    print(f"Part {n}: submitting")
    job_id = submit(req)
    print(f"Part {n}: job {job_id} — polling every {POLL_S}s (max {MAX_WAIT_MIN}min)")
    url = poll(job_id)
    print(f"Part {n}: downloading → {mp4.name}")
    download(url, mp4)
    return mp4


def main(slug_dir: str) -> None:
    base  = Path(slug_dir).resolve()
    final = base / "final.mp4"
    if final.exists():
        print(f"{final} exists, skipping render"); return
    started = time.time()
    p1 = render_part(base, 1)
    p2 = render_part(base, 2)
    print(f"Stitching → {final.name}")
    stitch([p1, p2], final)
    mins = (time.time() - started) / 60
    print(f"\nDone in {mins:.1f} min. {final}")


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else ".")
