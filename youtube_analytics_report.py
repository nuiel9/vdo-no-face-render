#!/usr/bin/env python3
"""youtube_analytics_report.py — pull traffic sources, retention, and
subscriber attribution for the Disclosed catalog.

Answers the question raw view counts cannot: WHY did McDonald's #30 and
Peloton #38 work when the rest of the catalog did not. Needs the analytics
token minted by youtube_analytics_auth.py.

Usage:
  python3 youtube_analytics_report.py                # all videos, lifetime
  python3 youtube_analytics_report.py --days 28      # last 28 days window
  python3 youtube_analytics_report.py --video VIDEO_ID  # one video deep-dive
"""
import json, sys, argparse
from pathlib import Path
from datetime import date, timedelta
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

CRED_HOME = Path.home() / ".config" / "youtube-upload"
TOKEN_ANALYTICS = CRED_HOME / "token_analytics.json"
SCOPES = [
    "https://www.googleapis.com/auth/youtube.readonly",
    "https://www.googleapis.com/auth/yt-analytics.readonly",
]


def creds():
    if not TOKEN_ANALYTICS.exists():
        raise SystemExit(f"missing {TOKEN_ANALYTICS} — run youtube_analytics_auth.py first")
    return Credentials.from_authorized_user_file(str(TOKEN_ANALYTICS), SCOPES)


def discover_videos(yt):
    """Map video_id -> (row#, pipeline_title, publishedAt) from pipeline.json notes."""
    import re
    p = json.load(open("pipeline.json"))
    found = {}
    for r in p["rows"]:
        notes = r.get("notes") or ""
        for m in re.finditer(r"youtube\.com/watch\?v=([A-Za-z0-9_-]{11})", notes):
            found.setdefault(m.group(1), (r["#"], r["title_working_draft"][:38]))
    # enrich with publish date + real title from Data API
    out = {}
    ids = list(found.keys())
    for i in range(0, len(ids), 50):
        resp = yt.videos().list(part="snippet,contentDetails", id=",".join(ids[i:i + 50])).execute()
        for it in resp["items"]:
            vid = it["id"]
            out[vid] = {
                "row": found[vid][0],
                "title": it["snippet"]["title"][:46],
                "published": it["snippet"]["publishedAt"][:10],
                "duration": it["contentDetails"]["duration"],
            }
    return out


def q(ana, **kw):
    kw.setdefault("ids", "channel==MINE")
    return ana.reports().query(**kw).execute()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--days", type=int, default=0, help="window in days; 0 = lifetime since first publish")
    ap.add_argument("--video", help="single video ID deep-dive")
    args = ap.parse_args()

    c = creds()
    yt = build("youtube", "v3", credentials=c)
    ana = build("youtubeAnalytics", "v2", credentials=c)

    vids = discover_videos(yt)
    if not vids:
        raise SystemExit("no video IDs found in pipeline.json notes")

    end = date.today()
    start = end - timedelta(days=args.days) if args.days else date(2026, 4, 19)
    sd, ed = start.isoformat(), end.isoformat()
    print(f"=== Analytics window: {sd} → {ed} ===\n")

    targets = [args.video] if args.video else list(vids.keys())

    # Per-video core metrics + traffic source split
    print(f"{'#':>4} {'pub':<11} {'views':>6} {'avgDur':>7} {'avg%':>5} {'sub+':>5} {'sub-':>5}  title")
    core_rows = []
    for vid in targets:
        meta = vids.get(vid, {"row": "?", "title": vid, "published": sd})
        try:
            r = q(ana, startDate=sd, endDate=ed,
                  metrics="views,averageViewDuration,averageViewPercentage,subscribersGained,subscribersLost",
                  filters=f"video=={vid}")
            row = r.get("rows", [[0, 0, 0, 0, 0]])[0]
            views, avgdur, avgpct, subg, subl = row
            core_rows.append((meta, vid, views, avgdur, avgpct, subg, subl))
            print(f"{str(meta['row']):>4} {meta['published']:<11} {int(views):>6} {int(avgdur):>6}s {avgpct:>4.0f}% {int(subg):>5} {int(subl):>5}  {meta['title']}")
        except Exception as e:
            print(f"{str(meta['row']):>4} {meta['published']:<11}  ERROR: {e}")

    # Traffic source breakdown per video
    print(f"\n=== Traffic sources (views by insightTrafficSourceType) ===")
    for meta, vid, views, *_ in sorted(core_rows, key=lambda x: -x[2]):
        if views == 0:
            continue
        try:
            r = q(ana, startDate=sd, endDate=ed,
                  metrics="views", dimensions="insightTrafficSourceType",
                  filters=f"video=={vid}", sort="-views")
            parts = [f"{row[0]}={int(row[1])}" for row in r.get("rows", [])]
            print(f"  #{meta['row']:>3} {meta['title'][:34]:<34} {' '.join(parts)}")
        except Exception as e:
            print(f"  #{meta['row']:>3} ERROR: {e}")

    # Impressions + CTR (channel-level by video, last window) — may be empty for very new videos
    print(f"\n=== Impressions + CTR (per video) ===")
    try:
        r = q(ana, startDate=sd, endDate=ed,
              metrics="impressions,impressionsClickThroughRate,views",
              dimensions="video", sort="-impressions", maxResults=50)
        for row in r.get("rows", []):
            vid = row[0]
            meta = vids.get(vid, {"row": "?", "title": vid})
            imp, ctr, vw = int(row[1]), row[2], int(row[3])
            print(f"  #{str(meta['row']):>3} {meta['title'][:34]:<34} impressions={imp:>6} CTR={ctr:>5.2f}% views={vw}")
    except Exception as e:
        print(f"  impressions report unavailable: {e}")

    # Channel-level subs trend
    print(f"\n=== Channel daily (last 14d) ===")
    try:
        r = q(ana, startDate=(end - timedelta(days=14)).isoformat(), endDate=ed,
              metrics="views,subscribersGained,subscribersLost,estimatedMinutesWatched",
              dimensions="day", sort="day")
        for row in r.get("rows", []):
            d, vw, sg, sl, mw = row
            print(f"  {d}  views={int(vw):>4}  sub+={int(sg)}  sub-={int(sl)}  watch_min={int(mw)}")
    except Exception as e:
        print(f"  channel daily unavailable: {e}")


if __name__ == "__main__":
    main()
