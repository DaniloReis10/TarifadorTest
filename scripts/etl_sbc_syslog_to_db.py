# etl_sbc_syslog_to_db_v2.py
# -*- coding: utf-8 -*-
"""
ETL para CDR CALL_END do SBC:
- Lê de public.syslog_events (campo raw)
- Extrai campos principais
- Valida dialednumber / connectednumber como somente dígitos
- Insere em public.sbc_phonecall; rejeita em public.sbc_phonecall_rejects quando inválido
"""

import os
import re
import sys
import argparse
from datetime import datetime
from typing import Optional, Tuple, Dict, Any, List

import psycopg2
import psycopg2.extras

# =========================
# Configuração de conexões
# =========================
def make_dsn(prefix: str = "SRC") -> str:
    """
    Monta DSN a partir de variáveis de ambiente.
    prefix=SRC (origem) ou DST (destino). Se não houver, tenta PG*.
    """
    host = os.getenv(f"{prefix}_PGHOST", os.getenv("PGHOST", "127.0.0.1"))
    port = os.getenv(f"{prefix}_PGPORT", os.getenv("PGPORT", "5432"))
    db   = os.getenv(f"{prefix}_PGDATABASE", os.getenv("PGDATABASE", "syslogdb" if prefix=="SRC" else "syslogdb"))
    usr  = os.getenv(f"{prefix}_PGUSER", os.getenv("PGUSER", "sysloguser"))
    pwd  = os.getenv(f"{prefix}_PGPASSWORD", os.getenv("PGPASSWORD", "syslogpass"))
    return f"host={host} port={port} dbname={db} user={usr} password={pwd}"

# =====================================
# DDLs (garantem esquema de destino)
# =====================================
DDL_SBC = """
CREATE TABLE IF NOT EXISTS public.sbc_phonecall (
    id               BIGINT PRIMARY KEY,
    hostid           SMALLINT,
    startdate        DATE,
    starttime        TIME,
    stopdate         DATE,
    stoptime         TIME,
    duration         INTEGER,
    dialednumber     VARCHAR(40),
    connectednumber  VARCHAR(40),
    conditioncode    SMALLINT,
    callcasedata     INTEGER,
    chargednumber    VARCHAR(40),
    seqnumber        INTEGER,
    seqlim           SMALLINT,
    callid           VARCHAR(64),
    callidass1       VARCHAR(64),
    callidass2       VARCHAR(64),
    raw              VARCHAR(600),
    event_type       VARCHAR(16)
);
"""

DDL_REJECTS = """
CREATE TABLE IF NOT EXISTS public.sbc_phonecall_rejects (
    id           BIGSERIAL PRIMARY KEY,
    src_max_id   BIGINT,
    sip_call_id  TEXT,
    session_id   TEXT,
    reason       TEXT NOT NULL,
    raw          TEXT NOT NULL,
    created_at   TIMESTAMPTZ NOT NULL DEFAULT now()
);
"""

DDL_STATE = """
CREATE TABLE IF NOT EXISTS public._etl_state_sbc AS
SELECT 0::bigint AS last_src_id
WHERE FALSE;
"""

UPSERT_ONE = """
INSERT INTO public.sbc_phonecall (
    id, hostid, startdate, starttime, stopdate, stoptime, duration,
    dialednumber, connectednumber, conditioncode, callcasedata, chargednumber,
    seqnumber, seqlim, callid, callidass1, callidass2, raw, event_type
) VALUES (
    %(id)s, %(hostid)s, %(startdate)s, %(starttime)s, %(stopdate)s, %(stoptime)s, %(duration)s,
    %(dialednumber)s, %(connectednumber)s, %(conditioncode)s, %(callcasedata)s, %(chargednumber)s,
    %(seqnumber)s, %(seqlim)s, %(callid)s, %(callidass1)s, %(callidass2)s, %(raw)s, %(event_type)s
)
ON CONFLICT (id) DO UPDATE SET
    hostid=EXCLUDED.hostid,
    startdate=EXCLUDED.startdate,
    starttime=EXCLUDED.starttime,
    stopdate=EXCLUDED.stopdate,
    stoptime=EXCLUDED.stoptime,
    duration=EXCLUDED.duration,
    dialednumber=EXCLUDED.dialednumber,
    connectednumber=EXCLUDED.connectednumber,
    conditioncode=EXCLUDED.conditioncode,
    callcasedata=EXCLUDED.callcasedata,
    chargednumber=EXCLUDED.chargednumber,
    seqnumber=EXCLUDED.seqnumber,
    seqlim=EXCLUDED.seqlim,
    callid=EXCLUDED.callid,
    callidass1=EXCLUDED.callidass1,
    callidass2=EXCLUDED.callidass2,
    raw=EXCLUDED.raw,
    event_type=EXCLUDED.event_type;
"""

INSERT_REJECT = """
INSERT INTO public.sbc_phonecall_rejects (src_max_id, sip_call_id, session_id, reason, raw)
VALUES (%(src_max_id)s, %(sip_call_id)s, %(session_id)s, %(reason)s, %(raw)s);
"""

ENSURE_RAW_600 = "ALTER TABLE public.sbc_phonecall ALTER COLUMN raw TYPE VARCHAR(600);"
ENSURE_EVENT_TYPE = "ALTER TABLE public.sbc_phonecall ADD COLUMN IF NOT EXISTS event_type VARCHAR(16);"

# ==================================================
# Helpers
# ==================================================
_NUMERIC_RE = re.compile(r"^\d+$")

def is_digits_only(s: Optional[str]) -> bool:
    """True se s é None ou contém apenas dígitos [0-9]."""
    if s is None:
        return True
    return bool(_NUMERIC_RE.fullmatch(str(s)))

def clamp_text(text: Optional[str], maxlen: int) -> Optional[str]:
    if text is None:
        return None
    if len(text) <= maxlen:
        return text
    return text[:maxlen]

def safe_int(x: Any, default: Optional[int]=None) -> Optional[int]:
    try:
        return int(x)
    except Exception:
        return default

def parse_sbc_datetime(s: str) -> Tuple[Optional[datetime], Optional[datetime.date], Optional[datetime.time]]:
    """Ex.: '16:41:19.223  UTC Fri Oct 24 2025' -> (datetime, date, time)"""
    if not s or not s.strip():
        return None, None, None
    s = s.replace("  ", " ").strip()
    # formato esperado: "%H:%M:%S.%f UTC %a %b %d %Y"
    try:
        dt = datetime.strptime(s, "%H:%M:%S.%f UTC %a %b %d %Y")
        return dt, dt.date(), dt.time()
    except ValueError:
        try:
            dt = datetime.strptime(s, "%H:%M:%S UTC %a %b %d %Y")
            return dt, dt.date(), dt.time()
        except ValueError:
            return None, None, None

def parse_call_end_raw(raw_line: str) -> Dict[str, Any]:
    """
    Faz o split por '|' e mapeia os índices baseados no CALL_END padrão (conforme exemplos anteriores).
    Ajuste os índices caso seu SBC gere ordem diferente.
    """
    out: Dict[str, Any] = {"raw": raw_line}
    if not raw_line:
        return out

    # Remover prefixo do syslog tipo "<141>[S=11880] " se existir:
    pipe_pos = raw_line.find('|')
    if pipe_pos > 0:
        prefix = raw_line[:pipe_pos]
        # tenta extrair id de sessão do prefixo (opcional)
        m = re.search(r'\[S=(\d+)\]', prefix)
        if m:
            out["session_id"] = m.group(1)

    parts = [p for p in raw_line.split('|')]

    # Protege contra linhas menores que o esperado:
    def get(i: int) -> Optional[str]:
        return parts[i].strip() if i < len(parts) else None

    # Mapeamento base (ajuste se necessário ao seu layout):
    out["cdr_type"]      = get(1)      # CALL_END
    out["endpoint_type"] = get(2)      # SBC
    out["sip_call_id"]   = get(3)      # 2020295436-...@...
    out["session_token"] = get(4)      # b77740:...
    out["orig_side"]     = get(5)      # RMT/LCL
    out["src_ip"]        = get(6)
    out["src_port"]      = get(7)
    out["dst_ip"]        = get(8)
    out["dst_port"]      = get(9)
    out["transport"]     = get(10)     # TLS/UDP/TCP
    out["src_uri"]       = get(11)     # 31259915@172.20.25.6
    out["src_uri_bm"]    = get(12)
    out["dst_uri"]       = get(13)     # 0999918552@172.20.25.6
    out["dst_uri_bm"]    = get(14)
    out["duration"]      = get(15)     # "0"
    out["term_side"]     = get(16)     # RMT/LCL
    out["term_reason"]   = get(17)     # GWAPP_NORMAL_CALL_CLEAR
    out["term_cat"]      = get(18)     # NO_ANSWER
    out["setup_time"]    = get(19)     # "16:41:19.223  UTC Fri Oct 24 2025"
    out["connect_time"]  = get(20)     # pode vir vazio
    out["release_time"]  = get(21)
    out["redirect_reason"]=get(22)     # "-1"

    # Deriva dialed/connected dos URIs (parte antes do @)
    def user_from_uri(uri: Optional[str]) -> Optional[str]:
        if not uri:
            return None
        # remove esquemas sip: caso apareça
        u = uri.strip()
        u = re.sub(r'^\s*sip:\s*', '', u, flags=re.IGNORECASE)
        # pega antes do @
        if '@' in u:
            return u.split('@', 1)[0]
        return u

    out["dialednumber"]    = user_from_uri(out["dst_uri"])
    out["connectednumber"] = user_from_uri(out["src_uri"])

    # Duration
    out["duration_i"] = safe_int(out["duration"], 0)

    # Datas
    setup_dt, setup_d, setup_t = parse_sbc_datetime(out.get("setup_time") or "")
    rel_dt,   rel_d,   rel_t   = parse_sbc_datetime(out.get("release_time") or "")

    out["startdate"] = setup_d
    out["starttime"] = setup_t
    out["stopdate"]  = rel_d
    out["stoptime"]  = rel_t

    return out

# ============================================
# ETL principal
# ============================================
def ensure_schema(conn):
    with conn.cursor() as cur:
        cur.execute(DDL_SBC)
        cur.execute(DDL_REJECTS)
        cur.execute(DDL_STATE)
        cur.execute(ENSURE_EVENT_TYPE)
        cur.execute(ENSURE_RAW_600)
    conn.commit()

def read_source_rows(conn, table: str, limit: Optional[int]=None, since_id: Optional[int]=None) -> List[Dict[str, Any]]:
    """
    Lê linhas de syslog da tabela origem.
    Ajuste a query se sua estrutura for diferente.
    Esperado: colunas (id BIGINT, raw TEXT/VARCHAR, received_at TIMESTAMP opcional)
    """
    q = f"SELECT id, raw FROM {table}"
    params = []
    where = []
    if since_id is not None:
        where.append("id > %s")
        params.append(since_id)
    if where:
        q += " WHERE " + " AND ".join(where)
    q += " ORDER BY id ASC"
    if isinstance(limit, int):
        q += " LIMIT %s"
        params.append(limit)

    with conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as cur:
        cur.execute(q, params)
        rows = cur.fetchall()
        return [dict(r) for r in rows]

def upsert_call(conn, row: Dict[str, Any]):
    with conn.cursor() as cur:
        cur.execute(UPSERT_ONE, row)

def insert_reject(conn, rej: Dict[str, Any]):
    with conn.cursor() as cur:
        cur.execute(INSERT_REJECT, rej)

def run_etl(src_dsn: str, dst_dsn: str, src_table: str, limit: Optional[int], debug: bool, ensure: bool, since_id: Optional[int]):
    src_conn = psycopg2.connect(src_dsn)
    dst_conn = psycopg2.connect(dst_dsn)

    try:
        if ensure:
            ensure_schema(dst_conn)

        src_rows = read_source_rows(src_conn, src_table, limit=limit, since_id=since_id)
        if debug:
            print(f"[etl] lidos {len(src_rows)} registros de {src_table}")

        rejects: List[Dict[str, Any]] = []
        inserted = 0
        src_max_id = None

        for r in src_rows:
            src_max_id = r["id"]
            raw = r.get("raw") or ""
            if not raw or "CALL_END" not in raw:
                # pule outras mensagens que não são do tipo desejado
                continue

            c = parse_call_end_raw(raw)
            # montar registro de destino
            dialed_user    = c.get("dialednumber")
            connected_user = c.get("connectednumber")

            # validações
            reasons = []
            # checagem numérica
            if dialed_user is not None and not is_digits_only(dialed_user):
                reasons.append("dialednumber não numérico")
            if connected_user is not None and not is_digits_only(connected_user):
                reasons.append("connectednumber não numérico")

            # checks básicos de datas
            if c.get("startdate") is None or c.get("starttime") is None:
                reasons.append("start_dt ausente ou inválido")
            if c.get("stopdate") is None or c.get("stoptime") is None:
                reasons.append("stop_dt ausente ou inválido")

            if reasons:
                rejects.append({
                    "src_max_id": src_max_id,
                    "sip_call_id": c.get("sip_call_id"),
                    "session_id": c.get("session_id") or c.get("session_token"),
                    "reason": "; ".join(reasons),
                    "raw": raw,
                })
                continue

            # preencher campos do destino
            dst_row = {
                "id":            src_max_id,                 # usando id da origem como PK (ajuste se necessário)
                "hostid":        1,                          # ajuste conforme sua origem
                "startdate":     c.get("startdate"),
                "starttime":     c.get("starttime"),
                "stopdate":      c.get("stopdate"),
                "stoptime":      c.get("stoptime"),
                "duration":      c.get("duration_i", 0),
                "dialednumber":  dialed_user,
                "connectednumber": connected_user,
                "conditioncode": None,
                "callcasedata":  None,
                "chargednumber": None,
                "seqnumber":     None,
                "seqlim":        None,
                "callid":        c.get("sip_call_id"),
                "callidass1":    None,
                "callidass2":    None,
                "raw":           clamp_text(raw, 600),       # sem truncar pra 128!
                "event_type":    "CALL_END",
            }

            upsert_call(dst_conn, dst_row)
            inserted += 1

        # flush rejeições
        for rej in rejects:
            insert_reject(dst_conn, rej)

        dst_conn.commit()

        if debug:
            print(f"[etl] inseridos/atualizados: {inserted}; rejeitados: {len(rejects)}; src_max_id={src_max_id}")

    finally:
        src_conn.close()
        dst_conn.close()

# =========================
# CLI
# =========================
def main():
    ap = argparse.ArgumentParser(description="ETL SBC CALL_END -> sbc_phonecall")
    ap.add_argument("--table", default="public.syslog_events", help="Tabela de origem com syslog (padrão: public.syslog_events)")
    ap.add_argument("--limit", default=None, help="Limite de linhas da origem (int ou 'all')")
    ap.add_argument("--since-id", type=int, default=None, help="Processar somente id > since-id")
    ap.add_argument("--debug", action="store_true", help="Verbose")
    args = ap.parse_args()

    limit = None
    if args.limit is not None and str(args.limit).lower() != "all":
        try:
            limit = int(args.limit)
        except Exception:
            print("Valor inválido para --limit (use inteiro ou 'all')", file=sys.stderr)
            sys.exit(2)

    src_dsn = make_dsn("SRC")
    dst_dsn = make_dsn("DST")

    if args.debug:
        print(f"[origem]  db={os.getenv('SRC_PGDATABASE', os.getenv('PGDATABASE','syslogdb'))} "
              f"host={os.getenv('SRC_PGHOST', os.getenv('PGHOST','127.0.0.1'))} "
              f"port={os.getenv('SRC_PGPORT', os.getenv('PGPORT','5432'))} "
              f"user={os.getenv('SRC_PGUSER', os.getenv('PGUSER','sysloguser'))}")
        print(f"[destino] db={os.getenv('DST_PGDATABASE', os.getenv('PGDATABASE','syslogdb'))} "
              f"host={os.getenv('DST_PGHOST', os.getenv('PGHOST','127.0.0.1'))} "
              f"port={os.getenv('DST_PGPORT', os.getenv('PGPORT','5432'))} "
              f"user={os.getenv('DST_PGUSER', os.getenv('PGUSER','sysloguser'))}")

    run_etl(src_dsn, dst_dsn, args.table, limit=limit, debug=args.debug, ensure=True, since_id=args.since_id)

if __name__ == "__main__":
    main()
