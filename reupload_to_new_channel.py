#!/usr/bin/env python3
"""Clean-channel re-upload test (staged 2026-06-19).

Re-uploads the 3 proven @disclosedch videos to a NEW, US-classified channel to
isolate the question: is the ceiling Thai-classification (a restart fixes it) or
a no-authority-niche wall (a restart repeats May then stalls)? Same content,
clean channel => the channel/classification variable is isolated.

The final.mp4 masters are no longer on disk, so this pulls each video back from
its public YouTube URL (yt-dlp) plus its current custom thumbnail (maxres), then
re-uploads to the new channel tagged en/en, PRIVATE, with the thumbnail.

Quality note: re-downloading from YouTube is one re-encode lossier than the
original master. Fine for a ROUTING test (quality isn't the variable). If the new
channel becomes the real one, re-render clean masters from the REQUEST JSONs later.

USAGE
  # 1. pre-stage (no token needed) — download videos + thumbnails to cache:
  python3 reupload_to_new_channel.py --download-only

  # 2. after you CREATE the new channel and mint its token:
  #    python3 yt_reauth.py token_newchannel.json   (pick the NEW channel/brand)
  # 3. upload the staged files to the new channel (private):
  python3 reupload_to_new_channel.py --token token_newchannel.json

Then: in the new channel's Studio, QC each, add the maxres thumbnail if not set,
and publish on a 2-3/week cadence (no flooding). Watch impressions + geography.
"""
import argparse, subprocess, sys, time
from pathlib import Path
import urllib.request

# The 3 proven CTR winners (lifetime views on @disclosedch).
SOURCES = [
    {"id": "cMUJdU2StLM", "tag": "30_mcdonalds"},   # 679 views, 4.2% CTR, 78% US
    {"id": "WPEr3psnIIw", "tag": "28_patagonia"},   # 486 views
    {"id": "-Up3dqFNnuI", "tag": "38_peloton"},     # 461 views
]
CACHE = Path("Daily/_reupload_cache")
CRED_DIR = Path.home() / ".config" / "youtube-upload"
SCOPES = [
    "https://www.googleapis.com/auth/youtube.upload",
    "https://www.googleapis.com/auth/youtube.force-ssl",
]


def stage_download():
    CACHE.mkdir(parents=True, exist_ok=True)
    for s in SOURCES:
        vid = s["id"]
        mp4 = CACHE / f"{vid}.mp4"
        thumb = CACHE / f"{vid}.jpg"
        url = f"https://www.youtube.com/watch?v={vid}"
        if mp4.exists() and mp4.stat().st_size > 1_000_000:
            print(f"[{s['tag']}] {vid}.mp4 cached, skip")
        else:
            print(f"[{s['tag']}] downloading {vid} ...")
            subprocess.run(
                ["yt-dlp", "-f", "bestvideo[height<=1080][ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best",
                 "--merge-output-format", "mp4", "-o", str(mp4), url],
                check=True,
            )
        if not thumb.exists():
            turl = f"https://i.ytimg.com/vi/{vid}/maxresdefault.jpg"
            # curl uses the system cert store (urllib on this Python lacks certs)
            r = subprocess.run(["curl", "-sS", "-o", str(thumb), turl])
            if r.returncode == 0 and thumb.exists() and thumb.stat().st_size > 5000:
                print(f"[{s['tag']}] thumbnail saved")
            else:
                print(f"[{s['tag']}] thumbnail download failed — set manually in Studio")
    print(f"\nStaged {len(SOURCES)} videos in {CACHE}/")


def _service(token_path):
    from google.oauth2.credentials import Credentials
    from google.auth.transport.requests import Request
    from googleapiclient.discovery import build
    tok = CRED_DIR / token_path if not Path(token_path).is_absolute() else Path(token_path)
    if not tok.exists():
        sys.exit(f"missing new-channel token at {tok}. Create the new channel, then run:\n"
                 f"  python3 yt_reauth.py {token_path}   (and SELECT the new channel)")
    creds = Credentials.from_authorized_user_file(str(tok), SCOPES)
    if creds.expired and creds.refresh_token:
        creds.refresh(Request())
        tok.write_text(creds.to_json())
    return build("youtube", "v3", credentials=creds)


def upload(token_path, read_token="token.json"):
    from googleapiclient.http import MediaFileUpload
    # read public source metadata with whatever token is handy (same Google login)
    src = _service(token_path)              # new channel = the upload target
    meta_reader = _service(read_token) if (CRED_DIR / read_token).exists() else src

    # SAFETY: confirm the target token is NOT @disclosedch (don't dump onto the old channel)
    me = src.channels().list(part="snippet", mine=True).execute()["items"][0]["snippet"]["title"]
    print(f"Upload target channel: {me}")
    if me.strip().lower() == "disclosed":
        sys.exit("REFUSING: target token is the OLD @disclosedch channel. Re-auth token_newchannel.json "
                 "and SELECT the new channel/brand account before uploading.")

    results = []
    for s in SOURCES:
        vid = s["id"]; mp4 = CACHE / f"{vid}.mp4"; thumb = CACHE / f"{vid}.jpg"
        if not mp4.exists():
            print(f"[{s['tag']}] {vid}.mp4 not staged — run --download-only first; skipping"); continue
        snip = meta_reader.videos().list(part="snippet", id=vid).execute()["items"][0]["snippet"]
        body = {
            "snippet": {
                "title": snip["title"],
                "description": snip.get("description", ""),
                "tags": snip.get("tags", []),
                "categoryId": snip.get("categoryId", "27"),
                "defaultLanguage": "en",
                "defaultAudioLanguage": "en",
            },
            "status": {"privacyStatus": "private", "selfDeclaredMadeForKids": False},
        }
        media = MediaFileUpload(str(mp4), mimetype="video/mp4", chunksize=8 * 1024 * 1024, resumable=True)
        req = src.videos().insert(part="snippet,status", body=body, media_body=media)
        resp = None
        print(f"[{s['tag']}] uploading '{snip['title'][:50]}' ...")
        while resp is None:
            status, resp = req.next_chunk()
            if status:
                print(f"   {int(status.progress()*100)}%")
        new_id = resp["id"]
        if thumb.exists():
            try:
                src.thumbnails().set(videoId=new_id,
                    media_body=MediaFileUpload(str(thumb), mimetype="image/jpeg")).execute()
                print("   thumbnail set")
            except Exception as e:
                print(f"   thumbnail set failed ({e}) — add in Studio")
        url = f"https://www.youtube.com/watch?v={new_id}"
        print(f"   -> {url} (private)")
        results.append((s["tag"], url))
    print("\nDONE. New-channel private uploads:")
    for tag, url in results:
        print(f"  {tag}: {url}")
    print("\nNext: QC each in the new channel's Studio, confirm thumbnail, then publish 2-3/week.")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--download-only", action="store_true", help="pre-stage videos+thumbs (no token)")
    ap.add_argument("--token", default="token_newchannel.json", help="new-channel token filename in ~/.config/youtube-upload/")
    args = ap.parse_args()
    if args.download_only:
        stage_download()
    else:
        stage_download()   # idempotent: ensures cache present
        upload(args.token)
