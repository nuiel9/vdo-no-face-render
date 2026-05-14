#!/usr/bin/env python3
"""youtube_analytics_auth.py — one-time OAuth flow to mint a token with the
YouTube Analytics read scope.

The youtube_upload.py token (~/.config/youtube-upload/token.json) only carries
youtube.upload + youtube.force-ssl. The YouTube Analytics API v2 (watch time,
traffic sources, impressions, CTR, retention) needs yt-analytics.readonly,
which is a separate scope.

This script mints a SEPARATE token file so youtube_upload.py's token is never
touched. Run it once; the analytics report script reuses the cached token.

Usage:
  python3 youtube_analytics_auth.py

It opens a browser for Google consent. Pick the same channel account that
owns @disclosedch. On success it writes:
  ~/.config/youtube-upload/token_analytics.json
"""
from pathlib import Path
from google_auth_oauthlib.flow import InstalledAppFlow

CRED_HOME = Path.home() / ".config" / "youtube-upload"
CLIENT_SECRET = CRED_HOME / "client_secret.json"
TOKEN_ANALYTICS = CRED_HOME / "token_analytics.json"

SCOPES = [
    "https://www.googleapis.com/auth/youtube.readonly",
    "https://www.googleapis.com/auth/yt-analytics.readonly",
]


def main() -> None:
    if not CLIENT_SECRET.exists():
        raise SystemExit(f"missing {CLIENT_SECRET}")
    flow = InstalledAppFlow.from_client_secrets_file(str(CLIENT_SECRET), SCOPES)
    creds = flow.run_local_server(port=0)
    TOKEN_ANALYTICS.write_text(creds.to_json())
    print(f"\n✓ Wrote {TOKEN_ANALYTICS}")
    print("  Scopes:", ", ".join(SCOPES))
    print("  youtube_analytics_report.py can now run.")


if __name__ == "__main__":
    main()
