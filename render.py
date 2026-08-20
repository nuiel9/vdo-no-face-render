#!/usr/bin/env python3
"""
aivdo-render: submit 2 /api/generate jobs (Path B), poll, stitch into final.mp4.
Usage: python render.py "<slug_dir>"  (e.g. Daily/2026-04-23_3_theranos-fake-scope/)

State file: writes <slug_dir>/.render_state.json after each submit so a
crashed run (DNS hiccup, network blip, ctrl-C) can be RESUMED on the next
invocation instead of re-submitting fresh jobs and burning ~$0.66 OpenAI
on the duplicate. The file is deleted automatically once final.mp4 lands.
Manually delete it if you want a clean re-submit.

Network: uses a urllib3 Retry policy on 5xx + connection-reset, plus an
explicit per-poll try/except around DNS / timeout errors so a transient
network blip doesn't kill an in-flight render job tracked on AIVDO's side.
"""
import json, os, sys, time, subprocess
from pathlib import Path
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

AIVDO_URL        = os.environ["AIVDO_URL"].rstrip("/")
AIVDO_API_KEY    = os.environ["AIVDO_API_KEY"]
POLL_S           = int(os.environ.get("AIVDO_POLL_S", "30"))
MAX_WAIT_MIN     = int(os.environ.get("AIVDO_MAX_WAIT_MIN", "130"))   # 120 stuck-job + 10 buffer
XFADE_S          = float(os.environ.get("AIVDO_XFADE_S", "0.5"))      # 0 = hard-cut concat
STRICT_FALLBACK  = os.environ.get("AIVDO_STRICT_FALLBACK", "0") == "1"  # 1 = abort if Part's engine isn't in EXPECTED_ENGINES for its requested_mode

H = {"X-API-Key": AIVDO_API_KEY, "Content-Type": "application/json"}

# Session with urllib3 retry on 5xx + connection-reset. Catches the
# transient class of failures BELOW the application layer. DNS-resolution
# failures still raise ConnectionError up to the caller — handled
# explicitly inside poll().
SESSION = requests.Session()
SESSION.headers.update(H)
_retry = Retry(
    total=4,
    backoff_factor=1.0,
    status_forcelist=[500, 502, 503, 504],
    allowed_methods=frozenset(["HEAD", "GET", "POST"]),
    raise_on_status=False,
)
SESSION.mount("https://", HTTPAdapter(max_retries=_retry))
SESSION.mount("http://", HTTPAdapter(max_retries=_retry))


# ─── State file (resume across crashes) ──────────────────────────────

STATE_FILENAME = ".render_state.json"


def _state_path(base: Path) -> Path:
    return base / STATE_FILENAME


def _load_state(base: Path) -> dict:
    p = _state_path(base)
    if not p.exists():
        return {}
    try:
        return json.loads(p.read_text())
    except json.JSONDecodeError:
        return {}


def _save_job_id(base: Path, part_n: int, job_id: str) -> None:
    state = _load_state(base)
    state[f"part{part_n}_job_id"] = job_id
    state[f"part{part_n}_submitted_at"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    _state_path(base).write_text(json.dumps(state, indent=2) + "\n")


def _clear_state(base: Path) -> None:
    p = _state_path(base)
    if p.exists():
        p.unlink()


def submit(req: dict) -> str:
    r = SESSION.post(f"{AIVDO_URL}/api/generate", json=req, timeout=60)
    r.raise_for_status()
    return r.json()["job_id"]


def poll(job_id: str) -> str:
    """Poll AIVDO until the job hits a terminal state. Survives transient
    DNS / connection / timeout errors during a poll iteration — only the
    deadline or a real `status=failed` from AIVDO bails out.
    """
    deadline = time.time() + MAX_WAIT_MIN * 60
    last = ""
    while time.time() < deadline:
        try:
            r = SESSION.get(f"{AIVDO_URL}/api/jobs/{job_id}", timeout=30)
            r.raise_for_status()
            b = r.json()
        except (
            requests.exceptions.ConnectionError,
            requests.exceptions.Timeout,
        ) as e:
            # DNS hiccup, transient network blip, or AIVDO 5xx that
            # exhausted the urllib3 retry budget. Job is still running on
            # AIVDO's side; we just couldn't reach it this poll. Wait and
            # try again.
            print(f"  {job_id[:8]} transient {type(e).__name__} — retrying in {POLL_S}s")
            time.sleep(POLL_S)
            continue
        line = f"  {job_id[:8]} {b['status']} {b.get('progress',0)}% — {b.get('current_stage','')}"
        if line != last:
            print(line); last = line
        if b["status"] == "completed":
            return b["output_url"]
        if b["status"] == "failed":
            raise RuntimeError(f"Job {job_id} failed: {b.get('error')}")
        time.sleep(POLL_S)
    raise TimeoutError(f"Job {job_id} exceeded {MAX_WAIT_MIN}min")


def fetch_routing_metadata(job_id: str) -> dict:
    """v1.8.5 image-routing fields exposed on GET /api/jobs/{id}."""
    r = SESSION.get(f"{AIVDO_URL}/api/jobs/{job_id}", timeout=30)
    r.raise_for_status()
    b = r.json()
    return {k: b.get(k) for k in (
        "image_engine_actually_used", "scenes_routed_via",
        "fallback_count", "tone_variant_resolved",
    )}


# Which engines legitimately satisfy each render_mode. "fast" is AIVDO's
# Google lane and is what this channel uses (spec §6.1): Gemini only, no
# OpenAI. Every model in AIVDO's DEFAULT_GOOGLE_CHAIN is listed, because a
# fallback hop within the chain is a correct outcome, not a misroute.
EXPECTED_ENGINES: dict[str, set[str]] = {
    "fast": {
        "gemini-3.1-flash-lite-image",
        "gemini-3.1-flash-image",
        "gemini-3-pro-image",
        # Preview aliases, in case the server has not been redeployed yet.
        "gemini-3.1-flash-image-preview",
        "gemini-3-pro-image-preview",
    },
    "cinematic": {"gpt-image-2-2026-04-21", "gpt-image-2"},
}


def engine_is_expected(requested_mode: str, engine: str) -> bool:
    """True if `engine` is a legitimate result for `requested_mode`.

    Unknown modes are permissive: a render already in flight must not be
    hard-failed because this table has not learned a new mode yet.
    """
    allowed = EXPECTED_ENGINES.get(requested_mode)
    if allowed is None:
        return True
    return engine in allowed


def report_routing(part_n: int, requested_mode: str, meta: dict) -> None:
    """Inspect one part's post-render routing metadata and log/raise on misroute.

    `image_engine_actually_used` (web.py:3438) is `sorted(engines_used)` — a
    LIST of every distinct engine that rendered a scene in the job, not a
    single engine name. A bare string is also accepted (backward
    compatibility with any caller that hands one directly, e.g. a test).

    Absent or empty is the NORMAL case for render_mode="fast": that lane's
    job.scene_dna stays NULL, so web.py omits these fields from the response
    entirely (web.py ~3478) rather than sending an empty list. Treat that as
    "no v1.8 routing data available" — informational only, never a misroute,
    never a raise (even under STRICT_FALLBACK). Without this, every single
    Thai render would flag as a misroute.
    """
    raw_engines = meta.get("image_engine_actually_used")
    fallback    = meta.get("fallback_count") or 0
    routed      = meta.get("scenes_routed_via") or {}

    if raw_engines is None:
        engines: list[str] = []
    elif isinstance(raw_engines, str):
        engines = [raw_engines]
    else:
        engines = list(raw_engines)

    if not engines:
        print(f"  · Part {part_n}: no v1.8 routing data available (engine metadata absent)")
        return

    # Correctly routed only if EVERY engine that rendered a scene is in the
    # allowlist for the requested mode.
    fell_back = any(not engine_is_expected(requested_mode, e) for e in engines)

    if fell_back:
        print(f"  ⚠ Part {part_n} FALLBACK: requested={requested_mode!r} actual_engines={engines!r} "
              f"fallback_count={fallback} scenes_routed_via={routed}")
        if STRICT_FALLBACK:
            raise RuntimeError(
                f"Part {part_n} fell back from {requested_mode} to {engines!r}. "
                f"Set AIVDO_STRICT_FALLBACK=0 to allow heterogeneous renders."
            )
    elif fallback:
        # A non-zero fallback_count with every engine still inside
        # EXPECTED_ENGINES is a hop within the chain (e.g. lite -> flash),
        # not a misroute. Worth reporting — it's real information about the
        # render — but it must not gate STRICT_FALLBACK's raise.
        print(f"  ↻ Part {part_n} in-chain fallback: engines={engines!r} "
              f"fallback_count={fallback} scenes_routed_via={routed}")
    else:
        print(f"  ✓ Part {part_n} engines={engines!r} fallback_count={fallback}")


def download(url: str, dest: Path) -> None:
    # Use a fresh session for the GCS signed-URL download — AIVDO's
    # X-API-Key header isn't needed (and shouldn't leak) on storage.googleapis.com.
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


def discover_parts(base: Path) -> list[int]:
    """Return the sorted part numbers present in a slug folder.

    An 8-minute episode was always two parts, so main() used to hardcode
    them. A 15-20 min Thai episode is 4-5 parts, so they are discovered
    instead. Sorted numerically, not lexically, or part 10 stitches
    between 1 and 2.
    """
    numbers = []
    for path in base.glob("REQUEST_PART_*.json"):
        stem = path.stem.removeprefix("REQUEST_PART_")
        if stem.isdigit():
            numbers.append(int(stem))
    if not numbers:
        raise FileNotFoundError(f"no REQUEST_PART_*.json files in {base}")
    numbers.sort()
    expected = list(range(1, len(numbers) + 1))
    if numbers != expected:
        raise ValueError(
            f"gap in parts: found {numbers}, expected {expected}. "
            "A missing part means missing narration — fix the slug folder."
        )
    return numbers


def apply_request_defaults(req: dict) -> dict:
    """Fill in render.py's runtime-controlled fields on a loaded request payload.

    Mutates and returns `req` for convenience.
    """
    # Thai episodes (this pipeline's new lane) default to "fast" -- AIVDO's
    # Google lane, Gemini only, no OpenAI (spec §6.1). "cinematic" would
    # force gpt-image-2. There is no mode that names a single Gemini model,
    # so the model comes from AIVDO's chain head.
    #
    # setdefault, NOT unconditional assignment: every shipped English slug's
    # REQUEST_PART_*.json already carries "render_mode": "cinematic" +
    # "strict_cinematic": true. An unconditional overwrite would silently
    # downgrade a re-render of any shipped English slug (delete partN.mp4,
    # re-run) from its cinematic gpt-image-2 render to the Gemini fast
    # lane -- a shipped video's requested quality/engine must not change
    # just because it's being re-rendered.
    req.setdefault("render_mode", "fast")
    # video_intent activates the faceless_youtube profile, server-enforcing
    # "no faces" + documentary realism per-scene. Unlike render_mode, every
    # shipped request (Thai and English) already used "faceless_youtube" --
    # grep across Daily/*/REQUEST*.json confirms no slug specifies anything
    # else -- so an unconditional assignment here does not clobber a
    # legitimate per-slug choice; it just restates what every slug wants.
    req["video_intent"] = "faceless_youtube"
    return req


def render_part(base: Path, n: int) -> Path:
    mp4 = base / f"part{n}.mp4"
    if mp4.exists():
        print(f"part{n}.mp4: cached, skip")
        return mp4
    req = json.loads((base / f"REQUEST_PART_{n}.json").read_text())
    apply_request_defaults(req)
    # acknowledged_no_editorial silences the soft editorial gate, which exists
    # to prevent publishing fabricated factual claims about real brands. Set
    # ONLY when a human has fact-checked this slug's REVIEW.md + SCRIPT.txt
    # against real primary sources, and committed an empty `.facts_verified`
    # marker file in the slug folder. Until that marker exists, the server's
    # editorial warning fires in logs as intended — the warning IS the safety
    # signal, do not silence by default. (Correction shipped 2026-04-26 after
    # a Tang Hua Seng test render produced plausible-fabricated landmark
    # imagery from un-verified narration.)
    if (base / ".facts_verified").exists():
        req["acknowledged_no_editorial"] = True

    # Resume an in-flight job if a prior run crashed mid-poll. Without this,
    # a DNS hiccup mid-render forces a full re-submit, burning ~$0.66
    # OpenAI on a duplicate AIVDO job. Saved to .render_state.json.
    state = _load_state(base)
    saved_job_id = state.get(f"part{n}_job_id")
    if saved_job_id:
        print(f"Part {n}: resuming saved job {saved_job_id} (from {state.get(f'part{n}_submitted_at', '?')})")
        job_id = saved_job_id
    else:
        print(f"Part {n}: submitting")
        job_id = submit(req)
        _save_job_id(base, n, job_id)
        print(f"Part {n}: job {job_id} — polling every {POLL_S}s (max {MAX_WAIT_MIN}min)")
    url = poll(job_id)
    try:
        report_routing(n, req.get("render_mode", "default"), fetch_routing_metadata(job_id))
    except Exception as e:
        if STRICT_FALLBACK:
            raise
        print(f"  (routing-metadata fetch skipped: {e})")
    print(f"Part {n}: downloading → {mp4.name}")
    download(url, mp4)
    return mp4


def main(slug_dir: str) -> None:
    base  = Path(slug_dir).resolve()
    final = base / "final.mp4"
    if final.exists():
        print(f"{final} exists, skipping render"); return
    started = time.time()
    part_numbers = discover_parts(base)
    print(f"Rendering {len(part_numbers)} part(s): {part_numbers}")
    parts = [render_part(base, n) for n in part_numbers]
    print(f"Stitching {len(parts)} part(s) → {final.name}")
    stitch(parts, final)
    # Run completed; the state file no longer reflects a useful resumable
    # state. Remove it so the next slug-render in the same folder doesn't
    # accidentally try to resume a stale job_id.
    _clear_state(base)
    mins = (time.time() - started) / 60
    print(f"\nDone in {mins:.1f} min. {final}")


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else ".")
