#!/usr/bin/env python3
"""Re-authenticate the YouTube *upload* token (run when it's revoked, e.g. after a
Google account switch). Backs up the dead token, launches the browser consent flow,
writes a fresh token.json, and prints which channel you authed.

MUST be run in your own terminal (it opens a browser + a localhost redirect).
In Claude Code, run it with the `!` prefix:  ! python3 yt_reauth.py
"""
import sys
from pathlib import Path
from datetime import date

CRED = Path.home() / ".config" / "youtube-upload"
# Optional arg: token filename (e.g. token_newchannel.json) to mint a token for a
# DIFFERENT channel — select that channel/brand during the browser consent.
TOKEN = CRED / (sys.argv[1] if len(sys.argv) > 1 else "token.json")
CLIENT_SECRET = CRED / "client_secret.json"
SCOPES = [
    "https://www.googleapis.com/auth/youtube.upload",
    "https://www.googleapis.com/auth/youtube.force-ssl",
]

from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

if not CLIENT_SECRET.exists():
    sys.exit(f"missing OAuth client secret at {CLIENT_SECRET}")

# 1. move the revoked token aside (so the flow doesn't try to refresh it)
if TOKEN.exists():
    bak = CRED / f"{TOKEN.name}.revoked.{date.today().isoformat()}.bak"
    i = 1
    while bak.exists():
        bak = CRED / f"{TOKEN.name}.revoked.{date.today().isoformat()}.{i}.bak"
        i += 1
    TOKEN.rename(bak)
    print(f"backed up revoked token -> {bak.name}")

# 2. interactive consent (opens your browser). Pick the account that owns @disclosedch.
print("opening browser for consent — choose the @disclosedch (Nuielo) Google account...")
flow = InstalledAppFlow.from_client_secrets_file(str(CLIENT_SECRET), SCOPES)
creds = flow.run_local_server(port=0)
TOKEN.write_text(creds.to_json())

# 3. confirm
yt = build("youtube", "v3", credentials=creds)
me = yt.channels().list(part="snippet", mine=True).execute()["items"][0]["snippet"]["title"]
print(f"\nAUTH OK — fresh token.json written. Authenticated channel: {me}")
print("If that is NOT @disclosedch, delete token.json and re-run, selecting the correct account.")
