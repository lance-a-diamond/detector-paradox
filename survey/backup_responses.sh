#!/usr/bin/env bash
# Pull all survey responses from Cloudflare KV via the admin endpoint
# and save a timestamped JSON snapshot. Safe to run daily (or on-demand).
#
# Usage: ./backup_responses.sh
# Cron:  0 7 * * * ./survey/backup_responses.sh >> /tmp/survey_backup.log 2>&1

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
RESPONSES_DIR="$SCRIPT_DIR/responses"
DATE="$(date +%Y-%m-%d)"
OUT="$RESPONSES_DIR/responses_${DATE}.json"
LATEST="$RESPONSES_DIR/responses_latest.json"

# Password via env var to avoid leaking via `ps`.
# Set STUDY_ADMIN_PW in your shell before running (see wrangler.toml.example).
ADMIN_PW="${STUDY_ADMIN_PW:?STUDY_ADMIN_PW env var must be set — see wrangler.toml.example}"

mkdir -p "$RESPONSES_DIR"

# Use -G + --data-urlencode so the password isn't on the ps-visible URL line
HTTP_CODE=$(curl -s -o "$OUT.tmp" -w "%{http_code}" \
  -G "https://study.verovu.ai/api/results" \
  --data-urlencode "pw=$ADMIN_PW")

if [[ "$HTTP_CODE" != "200" ]]; then
  echo "[$(date -Iseconds)] FAIL — HTTP $HTTP_CODE" >&2
  rm -f "$OUT.tmp"
  exit 1
fi

mv "$OUT.tmp" "$OUT"
cp "$OUT" "$LATEST"

COUNT=$(python3 -c "import json,sys;d=json.load(open('$OUT'));print(d.get('count',0))")
MAX=$(python3 -c "import json,sys;d=json.load(open('$OUT'));print(d.get('maxResponses','?'))")
CLOSED=$(python3 -c "import json,sys;d=json.load(open('$OUT'));print(d.get('closed',False))")

echo "[$(date -Iseconds)] OK — ${COUNT}/${MAX} responses (closed=${CLOSED}) -> ${OUT}"
