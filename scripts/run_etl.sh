#!/usr/bin/env bash
set -euo pipefail

if [[ -d .venv ]]; then
  # shellcheck disable=SC1091
  source .venv/bin/activate || true
fi

if [[ -f .env ]]; then
  export $(grep -v '^#' .env | xargs)
fi

python etl_sbc_syslog_to_db.py       --table public.syslog_events       --limit 1000       --since-id 0       --debug
