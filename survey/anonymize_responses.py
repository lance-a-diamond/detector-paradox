#!/usr/bin/env python3
"""Strip Prolific PIDs and browser/IP fingerprints from survey responses.

Produces a public-release-safe JSON file that preserves the scientific content
(session ID, submission order, passage answers, Likert ratings, demographics,
free-text reasoning) while removing identifying metadata.

Fields removed:
    prolific.pid, prolific.studyId, prolific.sessionId  -- Prolific identifiers
    _meta.ip                                            -- IP-derived (was already "unknown" for most)
    _meta.ua                                            -- User-Agent browser fingerprint
    _meta.key                                           -- internal KV key (timestamp-bearing)

Fields retained:
    sessionId                 -- random per-session UUID, no cross-reference to PID
    startedAt, completedAt    -- anonymized timestamps (second-level precision is fine)
    passageOrder              -- scientific interest
    demographics              -- self-report, no PII
    passages                  -- the actual survey data
    debrief                   -- free-text reasoning
    _meta.country             -- 2-letter country code (aggregate, non-identifying)
    _meta.submittedAt         -- aggregate timestamp
    _meta.responseNumber      -- sequential count for tracking

Usage:
    python3 anonymize_responses.py input.json output.json
    python3 anonymize_responses.py                # defaults to responses/responses_latest.json -> responses_anonymized.json
"""
import argparse
import json
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
DEFAULT_INPUT = SCRIPT_DIR / "responses" / "responses_latest.json"
DEFAULT_OUTPUT = SCRIPT_DIR / "responses" / "responses_anonymized.json"


def anonymize(record: dict) -> dict:
    r = dict(record)
    r.pop("prolific", None)
    meta = dict(r.get("_meta", {}))
    meta.pop("ip", None)
    meta.pop("ua", None)
    meta.pop("key", None)
    r["_meta"] = meta
    return r


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("input", nargs="?", default=str(DEFAULT_INPUT))
    p.add_argument("output", nargs="?", default=str(DEFAULT_OUTPUT))
    args = p.parse_args()

    data = json.loads(Path(args.input).read_text())
    cleaned = {
        "count": data.get("count"),
        "submissionCounter": data.get("submissionCounter"),
        "maxResponses": data.get("maxResponses"),
        "closed": data.get("closed"),
        "responses": [anonymize(r) for r in data.get("responses", [])],
        "anonymization_note": (
            "Prolific identifiers (PID, studyId, sessionId) and browser fingerprints "
            "(IP, User-Agent, internal KV key) have been stripped. The random per-session "
            "UUID in each record's `sessionId` field is retained as the only per-response "
            "identifier. This field cannot be traced back to Prolific participant identity."
        ),
    }

    # Verify: no Prolific identifiers remain in response records. The
    # `anonymization_note` field legitimately says "Prolific", so check responses only.
    responses_serialized = json.dumps(cleaned["responses"])
    for banned in ["PROLIFIC_PID", "prolific", "Prolific"]:
        assert banned not in responses_serialized, (
            f"Residual '{banned}' in responses — anonymization incomplete"
        )

    Path(args.output).write_text(json.dumps(cleaned, indent=2))
    print(f"Wrote {args.output} — {cleaned['count']} responses, anonymized.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
