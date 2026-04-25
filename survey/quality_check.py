#!/usr/bin/env python3
"""
Quality-check survey responses. Flags likely low-quality submissions based on
duration, per-passage time, Likert variance, reasoning engagement, and
response-pattern diversity.

Usage:
    python3 quality_check.py                        # reads responses/responses_latest.json
    python3 quality_check.py path/to/responses.json
    python3 quality_check.py --verbose              # full per-passage detail
    python3 quality_check.py --only-flagged         # show only FLAG/FAIL rows

Verdicts:
    PASS  — 0 flags
    FLAG  — 1-2 flags, warrants manual review
    FAIL  — 3+ flags, likely reject
"""
from __future__ import annotations
import argparse
import json
import statistics
import sys
from datetime import datetime
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
DEFAULT_PATH = SCRIPT_DIR / "responses" / "responses_latest.json"

LIKERT_DIMENSIONS = ["confidence", "naturalness", "clarity", "engagement", "authority", "quality"]

# Thresholds — adjust based on observed distributions
MIN_DURATION_MIN = 15          # total study duration
MIN_PASSAGE_TIME_SEC = 60      # per-passage reading time
MAX_SHORT_PASSAGES = 2         # flag if more than N passages were under MIN_PASSAGE_TIME_SEC
MIN_LIKERT_STD = 0.5           # mean per-passage std across 6 dimensions; below = straight-line
MIN_REASONING_CHARS = 10       # reasoning field counts as "filled" if >= N chars
MIN_REASONING_FILLED = 3       # need at least N of 8 filled to not flag
REQUIRE_ORIGIN_SPREAD = True   # flag if all 8 origin guesses are the same


def parse_iso(s: str) -> datetime:
    return datetime.fromisoformat(s.replace("Z", "+00:00"))


def assess(response: dict) -> dict:
    meta = response.get("_meta", {})
    prolific = response.get("prolific") or {}
    passages = response.get("passages", {}) or {}
    flags: list[str] = []

    # Duration
    try:
        started = parse_iso(response["startedAt"])
        completed = parse_iso(response["completedAt"])
        duration_sec = (completed - started).total_seconds()
    except Exception:
        duration_sec = 0
    duration_min = duration_sec / 60

    if duration_min < MIN_DURATION_MIN:
        flags.append(f"rushed (duration={duration_min:.1f}m < {MIN_DURATION_MIN}m)")

    # Per-passage time
    passage_times = [p.get("timeOnPage", 0) or 0 for p in passages.values()]
    short_passages = sum(1 for t in passage_times if t < MIN_PASSAGE_TIME_SEC)
    passage_avg = statistics.mean(passage_times) if passage_times else 0

    if short_passages > MAX_SHORT_PASSAGES:
        flags.append(f"{short_passages}/8 passages read in <{MIN_PASSAGE_TIME_SEC}s")

    # Likert variance (straight-lining)
    per_passage_stds = []
    for p in passages.values():
        values = [p.get(d) for d in LIKERT_DIMENSIONS if isinstance(p.get(d), (int, float))]
        if len(values) >= 2:
            per_passage_stds.append(statistics.stdev(values))
    mean_likert_std = statistics.mean(per_passage_stds) if per_passage_stds else 0

    if per_passage_stds and mean_likert_std < MIN_LIKERT_STD:
        flags.append(f"straight-line Likert (mean std={mean_likert_std:.2f})")

    # Reasoning engagement
    reasoning_filled = sum(
        1 for p in passages.values()
        if len((p.get("reasoning") or "").strip()) >= MIN_REASONING_CHARS
    )
    if reasoning_filled < MIN_REASONING_FILLED:
        flags.append(f"low engagement (reasoning filled {reasoning_filled}/8)")

    # Origin spread
    origins = [p.get("origin") for p in passages.values() if p.get("origin")]
    unique_origins = set(origins)
    if REQUIRE_ORIGIN_SPREAD and len(origins) == 8 and len(unique_origins) < 2:
        flags.append(f"uniform origin guesses ({len(origins)}x {origins[0] if origins else '?'})")

    origin_counts = {"human": origins.count("human"), "ai": origins.count("ai")}

    # Verdict
    n = len(flags)
    if n == 0:
        verdict = "PASS"
    elif n <= 2:
        verdict = "FLAG"
    else:
        verdict = "FAIL"

    return {
        "response_number": meta.get("responseNumber"),
        "key": meta.get("key"),
        "submitted_at": meta.get("submittedAt"),
        "prolific_pid": prolific.get("pid"),
        "duration_min": round(duration_min, 1),
        "passage_avg_sec": round(passage_avg, 0),
        "short_passages": short_passages,
        "likert_std": round(mean_likert_std, 2),
        "reasoning_filled": reasoning_filled,
        "origin_counts": origin_counts,
        "flags": flags,
        "verdict": verdict,
    }


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("path", nargs="?", default=str(DEFAULT_PATH))
    p.add_argument("--verbose", action="store_true", help="show per-passage detail")
    p.add_argument("--only-flagged", action="store_true", help="show only FLAG/FAIL rows")
    p.add_argument("--json", action="store_true", help="emit JSON instead of human-readable")
    args = p.parse_args()

    path = Path(args.path)
    if not path.exists():
        print(f"error: {path} does not exist — run backup_responses.sh first", file=sys.stderr)
        return 1

    data = json.loads(path.read_text())
    responses = data.get("responses", [])

    assessments = [assess(r) for r in responses]

    if args.json:
        print(json.dumps(assessments, indent=2, default=str))
        return 0

    verdicts = {"PASS": 0, "FLAG": 0, "FAIL": 0}
    for a in assessments:
        verdicts[a["verdict"]] += 1

    print(f"{'=' * 78}")
    print(f"  Quality check — {path.name}")
    print(f"  Total: {len(assessments)}    PASS: {verdicts['PASS']}    FLAG: {verdicts['FLAG']}    FAIL: {verdicts['FAIL']}")
    print(f"{'=' * 78}\n")

    for a in assessments:
        if args.only_flagged and a["verdict"] == "PASS":
            continue
        pid = a["prolific_pid"] or "-"
        oc = a["origin_counts"]
        print(f"#{a['response_number']}  {a['verdict']:4}  pid={pid:<20}  {a['submitted_at']}")
        print(f"       duration={a['duration_min']}m  avg/passage={a['passage_avg_sec']}s  "
              f"likert_std={a['likert_std']}  reasoning={a['reasoning_filled']}/8  "
              f"origins={oc['human']}H/{oc['ai']}AI")
        if a["flags"]:
            for f in a["flags"]:
                print(f"       \u26A0  {f}")
        print()

    if verdicts["FAIL"] > 0:
        print(f"\n  Recommend REJECTING {verdicts['FAIL']} submission(s) on Prolific (FAIL verdict).")
    if verdicts["FLAG"] > 0:
        print(f"  Review {verdicts['FLAG']} submission(s) manually (FLAG verdict — borderline).")

    return 0


if __name__ == "__main__":
    sys.exit(main())
