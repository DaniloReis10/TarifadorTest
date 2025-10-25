
-- Minimal placeholder; replace with your real DDL if needed.
CREATE TABLE IF NOT EXISTS syslog_events (
  id BIGSERIAL PRIMARY KEY,
  received_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  transport TEXT NOT NULL,
  raw TEXT NOT NULL
);
