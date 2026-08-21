#!/usr/bin/env python3
"""make_short.py — extract a 60-sec Short from a slug's final.mp4.

Vertical 9:16 crop with blurred-background letterbox (preserves cinematic
content while filling the 1080x1920 frame).

Usage:
  python3 make_short.py <slug_dir> [--start HH:MM:SS] [--duration 60]
  python3 make_short.py Daily/2026-05-04_30_the-mcdonalds-lawsuit-that-changed-ice-cream-forever/
  python3 make_short.py Daily/.../slug --start 0:30 --duration 45

Output:
  <slug_dir>/final_short.mp4  (1080x1920, ~10-15 MB, ready to upload as YouTube Short)

Notes:
- YouTube auto-classifies as Short if duration <= 60s AND aspect is vertical (9:16 or taller)
- Add #Shorts to the title or description on upload to maximize Shorts-shelf placement
"""
import argparse, subprocess, sys
from pathlib import Path


def main():
    p = argparse.ArgumentParser()
    p.add_argument("slug_dir")
    p.add_argument("--start", default="0:00", help="HH:MM:SS or seconds (default 0:00)")
    p.add_argument("--duration", type=int, default=60, help="seconds (default 60, max 60 for YouTube Shorts)")
    p.add_argument("--blur", type=int, default=30, help="background blur strength (default 30)")
    p.add_argument("--output", default="final_short.mp4", help="output filename in slug_dir")
    args = p.parse_args()

    slug = Path(args.slug_dir).resolve()
    src = slug / "final.mp4"
    dst = slug / args.output

    if not src.exists():
        print(f"error: {src} not found", file=sys.stderr)
        sys.exit(1)

    if args.duration > 60:
        print(f"warning: duration {args.duration}s exceeds YouTube Shorts cap (60s); clamping to 60")
        args.duration = 60

    # Blurred-background letterbox technique.
    # - [bg]: scale to 1080x1920 + heavy boxblur for backdrop
    # - [fg]: scale to 1080 wide (preserves aspect, gives ~608 tall)
    # - overlay [fg] vertically centered on [bg]
    vf = (
        f"[0:v]split[a][b];"
        f"[a]scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,boxblur={args.blur}:1[bg];"
        f"[b]scale=1080:-2[fg];"
        f"[bg][fg]overlay=(W-w)/2:(H-h)/2[out]"
    )

    cmd = [
        "ffmpeg", "-y",
        "-ss", str(args.start),
        "-i", str(src),
        "-t", str(args.duration),
        "-filter_complex", vf,
        "-map", "[out]",
        "-map", "0:a",
        "-c:v", "libx264", "-preset", "fast", "-crf", "22",
        "-c:a", "aac", "-b:a", "128k",
        "-movflags", "+faststart",
        str(dst),
    ]

    print(f"Source:  {src}")
    print(f"Output:  {dst}")
    print(f"Range:   {args.start} + {args.duration}s")
    print(f"Format:  1080x1920 (9:16 vertical), blurred-bg letterbox")
    print()
    subprocess.run(cmd, check=True)
    print()
    print(f"✓ Done. Upload {dst.name} as a YouTube Short (auto-detected by aspect + duration).")
    print(f"  Suggested title format: \"<hook> #Shorts\"")


if __name__ == "__main__":
    main()
