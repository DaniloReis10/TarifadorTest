#!/usr/bin/env bash
set -euo pipefail

if [[ -d .venv ]]; then
  # shellcheck disable=SC1091
  source .venv/bin/activate || true
fi

if [[ -f .env ]]; then
  export $(grep -v '^#' .env | xargs)
fi

python task_sbc_standalone.py       --dsn "host=${DB_HOST} port=${DB_PORT} dbname=${DB_NAME} user=${DB_USER} password=${DB_PASS}"       --ranges-only --quiet-missing-clients       --log-file sbc_debug.log --log-sql-level INFO       analysis
