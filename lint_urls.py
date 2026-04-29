#!/usr/bin/env python3
"""lint_urls.py — pre-publish URL linter for VDO No Face slug folders.

Scans the narrative artifacts in a slug folder for http(s) URLs and confirms
each resolves (2xx/3xx). Catches the dead-Variety-URL class of editorial
failure that nearly shipped on the Pentagon ELO slug (2026-04-29). Run this
BEFORE committing `.facts_verified` so a 404 in the YouTube description
or a fabricated citation URL doesn't reach publication.

Files scanned:
  - SCRIPT.txt, REVIEW.md, YOUTUBE.md, THUMBNAIL_PROMPT.txt
  - REQUEST_PART_*.json
  - Or any single file passed directly (e.g. a brief)

Usage:
  python3 lint_urls.py Daily/<slug>/
  python3 lint_urls.py briefs/<brief>.md

Severity tiers:
  PASS  ✓  2xx/3xx                — URL resolves cleanly
  WARN  ⚠  401, 403, 5xx, network — likely real but unverifiable from a
                                    bot UA (gov portals, Cloudflare, etc.).
                                    Human must eyeball in a browser.
  FAIL  ✗  404, 410, 451           — URL definitively does not exist.
                                    Hard ship-blocker; fix or remove.

Exit codes:
  0 — no FAIL-tier issues (warnings still printed for human review)
  1 — at least one FAIL-tier issue
  2 — argument or filesystem error
  Pass `--strict` to promote WARN → FAIL.

Why a Python script and not curl-in-bash:
  Some hosts (Variety, Cloudflare-fronted, YouTube) reject the default
  Python `requests` UA with 403 even though the URL is fine. We send a
  real-browser UA, retry on 5xx, and fall back HEAD→GET when HEAD is
  rejected. Those policies are awkward to encode in a one-liner.

Limitations:
  Some hosts block bots indiscriminately (DoD `esd.whs.mil` 403s any
  non-browser client). The linter will report those as failures; the
  human still has to eyeball whether a 403 is "real bot block on a real
  URL" vs "real 404 dressed as 403." 404 / 410 are unambiguous fails.
"""
from __future__ import annotations

import re
import sys
import time
from collections import defaultdict
from pathlib import Path
from urllib.parse import urlparse

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

UA = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
)
TIMEOUT_S = 10
PER_HOST_DELAY_S = 0.5

# Greedy enough to catch http(s)://… up to whitespace or markdown punctuation.
# Trailing `).,;"'>` is stripped after match — markdown likes to glue those on.
URL_RE = re.compile(r"https?://[^\s<>\"']+")
TRAIL_STRIP = ").,;\"'>"

SLUG_FILES = ("SCRIPT.txt", "REVIEW.md", "YOUTUBE.md", "THUMBNAIL_PROMPT.txt")


def find_files(target: Path) -> list[Path]:
    """Return the list of files to scan. If `target` is a file, scan just that."""
    if target.is_file():
        return [target]
    if not target.is_dir():
        return []
    files: list[Path] = []
    for name in SLUG_FILES:
        p = target / name
        if p.exists():
            files.append(p)
    files.extend(sorted(target.glob("REQUEST_PART_*.json")))
    return files


def extract_urls(files: list[Path]) -> dict[str, list[tuple[Path, int]]]:
    """Map each unique URL → list of (file, line) where it appears."""
    refs: dict[str, list[tuple[Path, int]]] = defaultdict(list)
    for f in files:
        for ln, line in enumerate(f.read_text().splitlines(), start=1):
            for raw in URL_RE.findall(line):
                url = raw.rstrip(TRAIL_STRIP)
                refs[url].append((f, ln))
    return refs


def make_session() -> requests.Session:
    s = requests.Session()
    s.headers["User-Agent"] = UA
    s.headers["Accept"] = "*/*"
    retry = Retry(
        total=2,
        backoff_factor=0.5,
        status_forcelist=[502, 503, 504],
        allowed_methods=frozenset(["HEAD", "GET"]),
    )
    adapter = HTTPAdapter(max_retries=retry)
    s.mount("https://", adapter)
    s.mount("http://", adapter)
    return s


def check_one(session: requests.Session, url: str) -> tuple[int, str]:
    """Return (status_code, note). status_code=0 means request itself failed."""
    try:
        r = session.head(url, allow_redirects=True, timeout=TIMEOUT_S)
        # Many sites reject HEAD with 405 / 403 even when GET would 200.
        if r.status_code in (403, 405) or r.status_code >= 500:
            r = session.get(
                url, allow_redirects=True, timeout=TIMEOUT_S, stream=True
            )
            r.close()
        return (r.status_code, "")
    except requests.exceptions.SSLError as e:
        return (0, f"SSL error: {type(e).__name__}")
    except requests.exceptions.ConnectionError:
        return (0, "connection error (DNS / network)")
    except requests.exceptions.Timeout:
        return (0, f"timeout >{TIMEOUT_S}s")
    except Exception as e:
        return (0, f"{type(e).__name__}: {str(e)[:120]}")


def fmt_path(p: Path) -> str:
    cwd = Path.cwd()
    try:
        return str(p.relative_to(cwd))
    except ValueError:
        return str(p)


FAIL_CODES = {404, 410, 451}  # unambiguous "URL is dead"


def severity(code: int) -> str:
    """Return 'PASS' / 'WARN' / 'FAIL'."""
    if 200 <= code < 400:
        return "PASS"
    if code in FAIL_CODES:
        return "FAIL"
    return "WARN"  # 401, 403, 5xx, 0 (network errors)


def main(target_str: str, strict: bool = False) -> int:
    target = Path(target_str).resolve()
    if not target.exists():
        print(f"error: {target} does not exist", file=sys.stderr)
        return 2

    files = find_files(target)
    if not files:
        print(f"error: no scannable files in {target}", file=sys.stderr)
        return 2

    refs = extract_urls(files)
    if not refs:
        print(f"no URLs found in {len(files)} file(s); nothing to check")
        return 0

    print(
        f"scanning {len(refs)} unique URL(s) across {len(files)} file(s) in "
        f"{fmt_path(target)}\n"
    )

    session = make_session()
    last_host_at: dict[str, float] = {}
    fails: list[tuple[str, int, str, list[tuple[Path, int]]]] = []
    warns: list[tuple[str, int, str, list[tuple[Path, int]]]] = []
    pass_count = 0

    for url, locs in sorted(refs.items()):
        host = urlparse(url).netloc
        prev = last_host_at.get(host)
        if prev is not None:
            elapsed = time.time() - prev
            if elapsed < PER_HOST_DELAY_S:
                time.sleep(PER_HOST_DELAY_S - elapsed)
        last_host_at[host] = time.time()

        code, note = check_one(session, url)
        sev = severity(code)
        marker = {"PASS": "✓", "WARN": "⚠", "FAIL": "✗"}[sev]
        line = f"  {marker} [{code or 'ERR'}] {url}"
        if note:
            line += f"  ({note})"
        print(line)
        if sev == "PASS":
            pass_count += 1
        elif sev == "WARN":
            warns.append((url, code, note, locs))
        else:
            fails.append((url, code, note, locs))

    if strict:
        fails.extend(warns)
        warns = []

    print(
        f"\nresult: {pass_count} pass, {len(warns)} warn, {len(fails)} fail "
        f"(of {len(refs)} unique URLs)"
    )

    if fails:
        print(f"\nFAILS — these are dead URLs and must be fixed before publish:")
        for url, code, note, locs in fails:
            for f, ln in locs:
                tail = f"  ({note})" if note else ""
                print(f"  {fmt_path(f)}:{ln}  [{code or 'ERR'}]  {url}{tail}")

    if warns:
        print(
            f"\nWARNS — likely real URLs that block bots (gov portals, "
            f"Cloudflare, etc.). Eyeball each in a browser; if any returns "
            f"4xx there too, promote to FAIL and fix:"
        )
        for url, code, note, locs in warns:
            for f, ln in locs:
                tail = f"  ({note})" if note else ""
                print(f"  {fmt_path(f)}:{ln}  [{code or 'ERR'}]  {url}{tail}")

    if fails:
        print("\nDO NOT commit .facts_verified until FAILs are resolved.")
        return 1

    if warns:
        print("\nNo hard fails. Safe to commit .facts_verified after eyeballing the WARNs above.")
    else:
        print("\nAll URLs resolve. Safe to commit .facts_verified.")
    return 0


if __name__ == "__main__":
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    flags = [a for a in sys.argv[1:] if a.startswith("--")]
    strict = "--strict" in flags

    if len(args) != 1:
        sys.stderr.write(__doc__ or "")
        sys.exit(2)
    sys.exit(main(args[0], strict=strict))
