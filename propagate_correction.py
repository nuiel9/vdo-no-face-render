#!/usr/bin/env python3
"""propagate_correction.py — apply a single correction across all narrative
artifacts in a slug folder atomically.

The routine generates 5+ artifacts per slug (SCRIPT.txt, REVIEW.md,
REQUEST_PART_1/2.json, YOUTUBE.md, sometimes THUMBNAIL_PROMPT.txt) where the
SAME wording is duplicated 3-10 times — same sentence appears in:
  - Top-level "text" field of REQUEST_PART_*.json (used for narration)
  - "source_text" field of REQUEST_PART_*.json (TTS source)
  - Per-scene "text" blocks inside REQUEST_PART_*.json (subtitle anchors)
  - SCRIPT.txt (record-keeping)
  - REVIEW.md (editorial review)
  - YOUTUBE.md (description / pinned comment)

A fact-check correction (e.g. "Special Assistant" → "Director of Entertainment
Media") must propagate to ALL of those locations. Forgetting one of the JSON
files = wrong narration in the rendered MP4. Forgetting YOUTUBE.md = wrong
description on the public video. The Pentagon ELO ship 2026-04-29 had to do
this propagation manually — and YOUTUBE.md was nearly missed.

This script does the propagation in one shot, with a preview-first workflow
so a typo in the OLD phrase doesn't quietly destroy content.

Usage:
  python3 propagate_correction.py Daily/<slug>/ "<old phrase>" "<new phrase>"
  python3 propagate_correction.py Daily/<slug>/ "<old>" "<new>" --apply

  # Single-file mode (e.g. fix only the brief, not the slug)
  python3 propagate_correction.py briefs/foo.md "<old>" "<new>" --apply

Behavior:
  - Default (no --apply): preview only. Shows file:line + before/after context
    and total count. No file is modified.
  - --apply: writes changes. Re-parses each modified JSON file to ensure the
    replacement didn't break JSON validity (e.g., introduced an unescaped
    quote). Aborts and reverts if validation fails.
  - Case-sensitive literal match by default. Pass --regex to use the OLD arg
    as a Python regex pattern. Pass --ignore-case for case-insensitive match.

Exit codes:
  0 — preview ran successfully, OR --apply succeeded
  1 — old phrase not found in any file
  2 — argument or filesystem error
  3 — --apply broke JSON validity in one or more REQUEST_PART_*.json files
       (changes were reverted; nothing was written)
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

SLUG_FILES = (
    "SCRIPT.txt",
    "REVIEW.md",
    "YOUTUBE.md",
    "THUMBNAIL_PROMPT.txt",
)
JSON_GLOB = "REQUEST_PART_*.json"

# How many chars on either side of a match to show in the preview.
CONTEXT_CHARS = 40


def find_files(target: Path) -> list[Path]:
    if target.is_file():
        return [target]
    if not target.is_dir():
        return []
    files: list[Path] = []
    for name in SLUG_FILES:
        p = target / name
        if p.exists():
            files.append(p)
    files.extend(sorted(target.glob(JSON_GLOB)))
    return files


def fmt_path(p: Path) -> str:
    cwd = Path.cwd()
    try:
        return str(p.relative_to(cwd))
    except ValueError:
        return str(p)


def preview_match(text: str, span: tuple[int, int]) -> tuple[int, str, str]:
    """Return (line_number_1based, before_context, after_context) for a match."""
    start, end = span
    line_no = text.count("\n", 0, start) + 1
    line_start = text.rfind("\n", 0, start) + 1  # 0 if no \n found
    line_end = text.find("\n", end)
    if line_end == -1:
        line_end = len(text)
    line = text[line_start:line_end]

    rel_start = start - line_start
    rel_end = end - line_start
    before = line[max(0, rel_start - CONTEXT_CHARS) : rel_start]
    after = line[rel_end : min(len(line), rel_end + CONTEXT_CHARS)]
    if rel_start > CONTEXT_CHARS:
        before = "…" + before
    if rel_end + CONTEXT_CHARS < len(line):
        after = after + "…"
    return (line_no, before, after)


def scan_file(
    path: Path,
    pattern: re.Pattern[str],
) -> list[tuple[int, str, str]]:
    """Return list of (line_no, before, after) for each match in the file."""
    text = path.read_text()
    return [preview_match(text, m.span()) for m in pattern.finditer(text)]


def apply_to_file(
    path: Path,
    pattern: re.Pattern[str],
    new: str,
) -> tuple[int, str, str]:
    """Return (count, original_text, new_text). Does NOT write."""
    original = path.read_text()
    new_text, count = pattern.subn(new, original)
    return (count, original, new_text)


def main(argv: list[str]) -> int:
    args = [a for a in argv if not a.startswith("--")]
    flags = [a for a in argv if a.startswith("--")]

    if len(args) != 3:
        sys.stderr.write(__doc__ or "")
        return 2

    target_str, old_phrase, new_phrase = args
    apply_changes = "--apply" in flags
    use_regex = "--regex" in flags
    ignore_case = "--ignore-case" in flags

    target = Path(target_str).resolve()
    if not target.exists():
        print(f"error: {target} does not exist", file=sys.stderr)
        return 2

    files = find_files(target)
    if not files:
        print(f"error: no scannable files in {target}", file=sys.stderr)
        return 2

    flags_re = re.MULTILINE | re.DOTALL
    if ignore_case:
        flags_re |= re.IGNORECASE
    pattern_str = old_phrase if use_regex else re.escape(old_phrase)
    try:
        pattern = re.compile(pattern_str, flags_re)
    except re.error as e:
        print(f"error: invalid regex: {e}", file=sys.stderr)
        return 2

    print(
        f"{'APPLY' if apply_changes else 'DRY-RUN'}: replace "
        f"{old_phrase!r} → {new_phrase!r}"
        f"{' [regex]' if use_regex else ''}"
        f"{' [ignore-case]' if ignore_case else ''}"
        f" across {len(files)} file(s) in {fmt_path(target)}\n"
    )

    total = 0
    per_file_counts: dict[Path, int] = {}
    for f in files:
        matches = scan_file(f, pattern)
        if not matches:
            continue
        per_file_counts[f] = len(matches)
        total += len(matches)
        print(f"  {fmt_path(f)}  ({len(matches)} match{'es' if len(matches) > 1 else ''}):")
        for line_no, before, after in matches:
            print(
                f"    line {line_no}:  {before}[{old_phrase}]{after}"
            )
            print(
                f"    {' ' * (len(str(line_no)) + 6)}→ {before}[{new_phrase}]{after}"
            )
        print()

    if total == 0:
        print(f"no matches found for {old_phrase!r}.")
        return 1

    print(
        f"total: {total} match{'es' if total > 1 else ''} across "
        f"{len(per_file_counts)} file(s)"
    )

    if not apply_changes:
        print("\n(dry-run; no changes written. re-run with --apply to commit.)")
        return 0

    # Apply phase: write each file, then validate JSON files.
    backups: dict[Path, str] = {}
    for f in per_file_counts:
        count, original, new_text = apply_to_file(f, pattern, new_phrase)
        if count == 0:
            continue
        backups[f] = original
        f.write_text(new_text)

    # Validate JSON files. If any broke, revert all changes.
    json_invalid: list[tuple[Path, str]] = []
    for f in backups:
        if f.suffix != ".json":
            continue
        try:
            json.loads(f.read_text())
        except json.JSONDecodeError as e:
            json_invalid.append((f, f"line {e.lineno} col {e.colno}: {e.msg}"))

    if json_invalid:
        print("\nERROR: replacement broke JSON validity. Reverting all changes:")
        for f, reason in json_invalid:
            print(f"  {fmt_path(f)} — {reason}")
        for f, original in backups.items():
            f.write_text(original)
        print(f"\nReverted {len(backups)} file(s). Nothing written.")
        return 3

    print(f"\nApplied {total} replacement(s) across {len(backups)} file(s):")
    for f, count in per_file_counts.items():
        print(f"  ✓ {fmt_path(f)}  ({count})")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
