#!/usr/bin/env python3
"""youtube_upload.py — upload a slug's final.mp4 to YouTube using the metadata
in its YOUTUBE.md.

Eliminates the manual upload-form-fill step at the end of the editorial
pipeline. Reads YOUTUBE.md, parses out title / description / chapters /
citations / hashtags / pinned-comment, uploads `final.mp4` from the same
folder, sets a custom thumbnail if one's available, posts the pinned-comment
text as a top-level comment, and prints the resulting video + Studio URLs.

After-upload steps you still do by hand (YouTube API limits):
  - Click the "Pin" button on the comment in Studio (the API has no pin
    endpoint; the comment IS posted, just unpinned).
  - Review the auto-generated end-screen / cards if you want any.
  - Flip from `private` → `public` once you've QC'd it in Studio.

Default behavior is intentionally conservative: video uploads as `private`
so you can QC in Studio before publishing. Pass `--privacy public` to skip
the QC step.

Usage:
  python3 youtube_upload.py Daily/<slug>/
  python3 youtube_upload.py Daily/<slug>/ --privacy public
  python3 youtube_upload.py Daily/<slug>/ --thumbnail path/to/thumb.png
  python3 youtube_upload.py Daily/<slug>/ --category-id 27
  python3 youtube_upload.py Daily/<slug>/ --dry-run   # parse-only, no upload
  python3 youtube_upload.py Daily/<slug>/ --no-pinned-comment

Auto-detection within the slug folder:
  - VIDEO:     final.mp4
  - THUMBNAIL: thumbnail.png, thumbnail.jpg, thumb.png, thumb.jpg (first hit)
  - METADATA:  YOUTUBE.md

YOUTUBE.md format expected (matches what the daily routine generates):
  # YOUTUBE.md: <title>
  ## Description (...)
  <body>
  ## Chapters (...)
  0:00 ...
  ## Citations
  1. ...
  ## Hashtags
  #X #Y
  ## Pinned Comment Draft
  <comment text>

  Sections are joined into the YouTube description in this order:
  Description → Chapters → Citations → Hashtags. The Published-URL header
  block is skipped (it's a record-keeping post-publish line).

ONE-TIME OAUTH SETUP (do this once before first upload):

  1. Install Google's libraries:
       pip install google-auth-oauthlib google-api-python-client

  2. Google Cloud Console — create or pick a project; enable
     "YouTube Data API v3" on it.
       https://console.cloud.google.com/apis/library/youtube.googleapis.com

  3. APIs & Services → Credentials → Create credentials → OAuth client ID
     → "Desktop app". Download the JSON. Save it as:
       ~/.config/youtube-upload/client_secret.json

  4. First run of this script: a browser pops for consent. Approve. After
     that, refresh token is cached at:
       ~/.config/youtube-upload/token.json
     Subsequent runs are headless until the refresh token expires
     (typically months).

  Override the credentials directory with $YT_UPLOAD_HOME if you want to
  store creds elsewhere.

Exit codes:
  0 — upload succeeded (or --dry-run completed)
  1 — upload or post-upload step failed
  2 — argument or filesystem error
  3 — auth setup missing or expired (follow the setup steps above)
"""
from __future__ import annotations

import json
import os
import re
import sys
from pathlib import Path
from typing import Any

CRED_HOME = Path(
    os.environ.get("YT_UPLOAD_HOME", str(Path.home() / ".config" / "youtube-upload"))
)
CLIENT_SECRET = CRED_HOME / "client_secret.json"
TOKEN = CRED_HOME / "token.json"

SCOPES = [
    "https://www.googleapis.com/auth/youtube.upload",
    "https://www.googleapis.com/auth/youtube.force-ssl",
]

# YouTube category IDs you might use (full list is API-queryable):
#   22 People & Blogs   24 Entertainment   25 News & Politics
#   26 Howto & Style    27 Education       28 Science & Technology
DEFAULT_CATEGORY_ID = "27"  # Education
DEFAULT_PRIVACY = "private"

THUMB_NAMES = ("thumbnail.png", "thumbnail.jpg", "thumb.png", "thumb.jpg")
MAX_THUMB_BYTES = 2 * 1024 * 1024  # 2 MB; YouTube's hard limit


# ─── Parsing YOUTUBE.md ──────────────────────────────────────────────


def parse_youtube_md(path: Path) -> dict[str, Any]:
    """Extract title / description-body / chapters / citations / hashtags /
    pinned-comment from a YOUTUBE.md.

    Returns a dict ready to feed `videos.insert`. The YouTube description
    is built by concatenating Description → Chapters → Citations → Hashtags.
    """
    text = path.read_text()

    # Title from `# YOUTUBE.md: <title>` (v4.5) or `# YOUTUBE: <title>` (v4.6) first line.
    m = re.search(r"^#\s+YOUTUBE(?:\.md)?:\s*(.+?)\s*$", text, re.MULTILINE)
    if not m:
        raise ValueError(f"{path}: cannot find `# YOUTUBE[.md]: <title>` header")
    title = m.group(1).strip()

    # Split into sections by `## ` headers (ignoring the H1 line).
    sections: dict[str, str] = {}
    current_name: str | None = None
    current_buf: list[str] = []
    for line in text.splitlines():
        h = re.match(r"^##\s+(.+?)\s*$", line)
        if h:
            if current_name is not None:
                sections[current_name] = "\n".join(current_buf).strip()
            current_name = h.group(1).strip()
            current_buf = []
        else:
            if current_name is not None:
                current_buf.append(line)
    if current_name is not None:
        sections[current_name] = "\n".join(current_buf).strip()

    # Match section names tolerantly. The routine wraps each section header
    # with descriptors and counts ("Video Description (100 words)",
    # "6 Chapters with Approximate Timestamps", "4 Citations", "8 Hashtags",
    # "Pinned Comment Draft"), so substring match is the only reliable path
    # — `startswith` breaks on the leading digit/word prefixes.
    def section_containing(needle: str) -> str:
        needle_lower = needle.lower()
        for name, body in sections.items():
            if needle_lower in name.lower():
                # Strip horizontal rules and lone dashes-block disclaimers
                # that the routine wraps the Description in.
                body = re.sub(r"^---\s*$", "", body, flags=re.MULTILINE).strip()
                return body
        return ""

    description_body = section_containing("Description")
    chapters = section_containing("Chapters")
    citations = section_containing("Citations")
    hashtags = section_containing("Hashtags")
    pinned = section_containing("Pinned Comment")

    # Strip any pinned-comment text from the rest (it's the LAST section
    # and shouldn't appear in the YT description).
    parts = [p for p in (description_body, chapters, citations, hashtags) if p]
    description = "\n\n".join(parts)

    # Tags: derive from hashtags string (#X #Y → ["X", "Y"]). YouTube tag
    # field accepts up to ~500 char total; trim if needed.
    tags = re.findall(r"#(\w+)", hashtags)
    if sum(len(t) + 2 for t in tags) > 480:
        # Drop the last few until we fit.
        while tags and sum(len(t) + 2 for t in tags) > 480:
            tags.pop()

    return {
        "title": title,
        "description": description,
        "tags": tags,
        "pinned_comment": pinned,
    }


# ─── Auth + service ──────────────────────────────────────────────────


def _bail_auth(msg: str) -> None:
    sys.stderr.write(
        f"AUTH ERROR: {msg}\n\n"
        "First-time setup:\n"
        "  pip install google-auth-oauthlib google-api-python-client\n"
        "Then complete the steps in the module docstring (`youtube_upload.py`).\n"
    )
    sys.exit(3)


def get_youtube_service():
    try:
        from google.auth.transport.requests import Request
        from google.oauth2.credentials import Credentials
        from google_auth_oauthlib.flow import InstalledAppFlow
        from googleapiclient.discovery import build
    except ImportError as e:
        _bail_auth(f"required library missing: {e}")

    CRED_HOME.mkdir(parents=True, exist_ok=True)

    creds = None
    if TOKEN.exists():
        creds = Credentials.from_authorized_user_file(str(TOKEN), SCOPES)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            if not CLIENT_SECRET.exists():
                _bail_auth(
                    f"missing OAuth client secret at {CLIENT_SECRET}. Download "
                    f"a Desktop-app OAuth client JSON from Google Cloud Console "
                    f"and save it to that path."
                )
            flow = InstalledAppFlow.from_client_secrets_file(str(CLIENT_SECRET), SCOPES)
            creds = flow.run_local_server(port=0)
        TOKEN.write_text(creds.to_json())

    return build("youtube", "v3", credentials=creds)


# ─── Upload ──────────────────────────────────────────────────────────


def upload_video(
    youtube,
    video_path: Path,
    meta: dict[str, Any],
    privacy: str,
    category_id: str,
) -> str:
    """Insert a video. Returns the video ID."""
    from googleapiclient.http import MediaFileUpload

    body = {
        "snippet": {
            "title": meta["title"],
            "description": meta["description"],
            "tags": meta["tags"],
            "categoryId": category_id,
        },
        "status": {
            "privacyStatus": privacy,
            "selfDeclaredMadeForKids": False,
        },
    }

    media = MediaFileUpload(
        str(video_path),
        mimetype="video/mp4",
        chunksize=8 * 1024 * 1024,
        resumable=True,
    )
    request = youtube.videos().insert(
        part="snippet,status", body=body, media_body=media
    )

    response = None
    last_pct = -1
    while response is None:
        status, response = request.next_chunk()
        if status:
            pct = int(status.progress() * 100)
            if pct != last_pct and pct % 5 == 0:
                print(f"  upload progress: {pct}%")
                last_pct = pct
    return response["id"]


def set_thumbnail(youtube, video_id: str, thumb_path: Path) -> None:
    from googleapiclient.http import MediaFileUpload

    if thumb_path.stat().st_size > MAX_THUMB_BYTES:
        sys.stderr.write(
            f"warning: thumbnail {thumb_path.name} is "
            f"{thumb_path.stat().st_size // 1024} KB, exceeds YouTube's 2 MB "
            f"limit. Skipping thumbnail upload.\n"
        )
        return
    youtube.thumbnails().set(
        videoId=video_id,
        media_body=MediaFileUpload(str(thumb_path), mimetype="image/png"),
    ).execute()


def post_top_level_comment(youtube, video_id: str, text: str) -> str:
    """Post a top-level comment. YouTube API has no `pin` endpoint —
    the user must click the Pin button in Studio. Returns the comment ID."""
    body = {
        "snippet": {
            "videoId": video_id,
            "topLevelComment": {"snippet": {"textOriginal": text}},
        }
    }
    resp = youtube.commentThreads().insert(part="snippet", body=body).execute()
    return resp["id"]


# ─── Main ────────────────────────────────────────────────────────────


def find_video(slug: Path) -> Path | None:
    p = slug / "final.mp4"
    return p if p.exists() else None


def find_thumbnail(slug: Path, override: str | None) -> Path | None:
    if override:
        p = Path(override)
        if not p.exists():
            sys.stderr.write(f"warning: --thumbnail {p} does not exist; skipping\n")
            return None
        return p
    for name in THUMB_NAMES:
        p = slug / name
        if p.exists():
            return p
    return None


def parse_args(argv: list[str]) -> dict[str, Any]:
    flags: dict[str, str | bool] = {
        "privacy": DEFAULT_PRIVACY,
        "category_id": DEFAULT_CATEGORY_ID,
        "thumbnail": None,
        "dry_run": False,
        "no_pinned_comment": False,
    }
    positional: list[str] = []
    i = 0
    while i < len(argv):
        a = argv[i]
        if a == "--privacy" and i + 1 < len(argv):
            flags["privacy"] = argv[i + 1]; i += 2; continue
        if a == "--category-id" and i + 1 < len(argv):
            flags["category_id"] = argv[i + 1]; i += 2; continue
        if a == "--thumbnail" and i + 1 < len(argv):
            flags["thumbnail"] = argv[i + 1]; i += 2; continue
        if a == "--dry-run":
            flags["dry_run"] = True; i += 1; continue
        if a == "--no-pinned-comment":
            flags["no_pinned_comment"] = True; i += 1; continue
        if a.startswith("--"):
            sys.stderr.write(f"unknown flag: {a}\n"); sys.exit(2)
        positional.append(a); i += 1
    if len(positional) != 1:
        sys.stderr.write(__doc__ or ""); sys.exit(2)
    flags["slug"] = positional[0]
    return flags


def main(argv: list[str]) -> int:
    args = parse_args(argv)
    slug = Path(args["slug"]).resolve()
    if not slug.is_dir():
        sys.stderr.write(f"error: {slug} is not a directory\n")
        return 2

    md = slug / "YOUTUBE.md"
    if not md.exists():
        sys.stderr.write(f"error: {md} not found\n")
        return 2

    video = find_video(slug)
    if not video and not args["dry_run"]:
        sys.stderr.write(f"error: {slug}/final.mp4 not found\n")
        return 2

    thumb = find_thumbnail(slug, args["thumbnail"])

    try:
        meta = parse_youtube_md(md)
    except ValueError as e:
        sys.stderr.write(f"parse error: {e}\n")
        return 2

    print(f"Parsed {md.name}:")
    print(f"  title: {meta['title']}")
    print(f"  description: {len(meta['description'])} chars")
    print(f"  tags: {meta['tags']}")
    print(f"  pinned comment: {len(meta['pinned_comment'])} chars")
    print()
    if video:
        size_mb = video.stat().st_size / (1024 * 1024)
        print(f"video: {video.name} ({size_mb:.1f} MB)")
    if thumb:
        print(f"thumbnail: {thumb.name}")
    else:
        print(f"thumbnail: (none — none of {THUMB_NAMES} found in slug folder)")
    print(f"privacy: {args['privacy']}")
    print(f"category_id: {args['category_id']}")
    if args["no_pinned_comment"]:
        print("pinned comment: SUPPRESSED (--no-pinned-comment)")

    if args["dry_run"]:
        print("\n--dry-run: not uploading. exit 0.")
        return 0

    print("\nAuthenticating with YouTube…")
    youtube = get_youtube_service()

    print(f"\nUploading {video.name}…")
    try:
        video_id = upload_video(
            youtube,
            video,
            meta,
            privacy=args["privacy"],
            category_id=args["category_id"],
        )
    except Exception as e:
        sys.stderr.write(f"upload failed: {e}\n")
        return 1

    video_url = f"https://www.youtube.com/watch?v={video_id}"
    studio_url = f"https://studio.youtube.com/video/{video_id}/edit"
    print(f"\n✓ Uploaded: {video_url}")
    print(f"  Studio:   {studio_url}")

    if thumb:
        try:
            set_thumbnail(youtube, video_id, thumb)
            print(f"✓ Thumbnail set ({thumb.name})")
        except Exception as e:
            sys.stderr.write(f"warning: thumbnail upload failed: {e}\n")

    if meta["pinned_comment"] and not args["no_pinned_comment"]:
        if args["privacy"] == "private":
            # YouTube API blocks `commentThreads.insert` on private videos
            # (returns 403 forbidden). Comments are public-facing surface;
            # the API enforces "video must be public/unlisted before a
            # comment can be posted." Don't try; print the text inline so
            # the human can copy-paste it into Studio after flipping public.
            print(
                "\n(pinned-comment NOT posted — YouTube API blocks comments "
                "on private videos. Once you flip privacy to public/unlisted "
                "in Studio, post + pin this text manually:)\n"
            )
            print("─── pinned comment text ───")
            print(meta["pinned_comment"])
            print("───────────────────────────")
            print(f"\nStudio comments page: {studio_url}/comments")
        else:
            try:
                cid = post_top_level_comment(youtube, video_id, meta["pinned_comment"])
                print(f"✓ Posted pinned-comment text (comment id {cid})")
                print(
                    "  NOTE: YouTube API has no 'pin' endpoint. Click the Pin button "
                    "in Studio:"
                )
                print(f"  {studio_url}/comments")
            except Exception as e:
                sys.stderr.write(f"warning: comment post failed: {e}\n")

    print(
        f"\nNext: open Studio, QC, flip privacy → public when ready, "
        f"then update pipeline.json:"
    )
    print(f"  python3 -c \"...\" or hand-edit notes URL = {video_url}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
