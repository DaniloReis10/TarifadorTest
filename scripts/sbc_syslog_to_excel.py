
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Exporta eventos CALL_END do PostgreSQL (tabela de syslog) para uma planilha Excel
no formato mínimo da tabela phonecalls_phonecall — sem depender de metadados de ramais
ou tabelas de preço.
"""
import argparse
import datetime as dt
import re
from decimal import Decimal
from typing import Optional, Tuple, Iterable

import pandas as pd

try:
    import psycopg
    from psycopg import sql
except Exception as e:
    raise SystemExit(
        "Faltou o driver do PostgreSQL. Instale com:\n"
        "  pip install 'psycopg[binary]'\n"
        "ou\n"
        "  pip install psycopg2-binary\n"
        f"Detalhe do erro: {e}"
    )

# ------------ Regex helpers ---------------------------------------------------

NUM_RE = re.compile(r"(?:(?:sip:|tel:)?)(\+?\d{3,})")
SIP_URI_RE = re.compile(r"(?:sip:)?(?P<num>\+?\d{3,})@[^\s>]*")

# duration=83 (segundos)  |  dur=83s  |  00:01:23  |  1m23s  |  83s
DUR_SECS_RE = re.compile(r"(?:^|\b)(?:duration|dur|len)\s*=\s*(\d+)\b", re.IGNORECASE)
DUR_HHMMSS_RE = re.compile(r"\b(\d{1,2}):(\d{2}):(\d{2})\b")
DUR_M_S_RE = re.compile(r"\b(?:(\d+)m)?\s*(\d+)s\b", re.IGNORECASE)

# ------------ Timezone helpers -----------------------------------------------

def now_tz(tzname: str) -> dt.datetime:
    try:
        import zoneinfo
        tz = zoneinfo.ZoneInfo(tzname)
    except Exception:
        tz = None
    n = dt.datetime.now(dt.timezone.utc)
    return n.astimezone(tz) if tz else n

def to_local(ts: dt.datetime, tzname: str) -> dt.datetime:
    if ts.tzinfo is None:
        ts = ts.replace(tzinfo=dt.timezone.utc)
    try:
        import zoneinfo
        tz = zoneinfo.ZoneInfo(tzname)
        return ts.astimezone(tz)
    except Exception:
        return ts.astimezone(dt.timezone(dt.timedelta(hours=-3)))  # fallback -03:00

# ------------ Parsing helpers -------------------------------------------------

def extract_two_numbers(text: str) -> Tuple[Optional[str], Optional[str]]:
    """Extrai (caller, callee) por ordem de aparecimento no raw.
    1) URIs SIP (sip:<num>@...)  2) números longos (>=3 dígitos).
    """
    if not text:
        return None, None

    uris = SIP_URI_RE.findall(text)
    if len(uris) >= 2:
        return uris[0], uris[1]

    nums = NUM_RE.findall(text)
    if len(nums) >= 2:
        return nums[0], nums[1]
    if len(nums) == 1:
        return nums[0], None
    return None, None

def guess_direction(caller: Optional[str], callee: Optional[str]) -> Tuple[int, int]:
    """Heurística simples -> (inbound, internal)"""
    def is_internal(n: Optional[str]) -> bool:
        return bool(n and n.isdigit() and 3 <= len(n) <= 6)
    def is_external(n: Optional[str]) -> bool:
        return bool(n and (n.startswith("+") or len(n) >= 8))

    internal = 1 if is_internal(caller) and is_internal(callee) else 0
    inbound = 1 if is_external(caller) and not internal else 0
    return inbound, internal

def parse_duration_seconds(text: str) -> int:
    """Tenta extrair duração em segundos do raw. Retorna 0 se não encontrado."""
    if not text:
        return 0
    # duration=83
    m = DUR_SECS_RE.search(text)
    if m:
        try:
            return int(m.group(1))
        except Exception:
            pass
    # 00:01:23
    m = DUR_HHMMSS_RE.search(text)
    if m:
        h, mnt, s = map(int, m.groups())
        return h * 3600 + mnt * 60 + s
    # 1m23s  ou  83s
    m = DUR_M_S_RE.search(text)
    if m:
        mm = m.group(1)
        ss = m.group(2)
        total = 0
        if mm:
            total += int(mm) * 60
        total += int(ss)
        return total
    return 0

# ------------ DB fetch --------------------------------------------------------

def fetch_syslog_rows(conn, table: str, min_id: int, limit: int):
    """Consulta segura com placeholders e Identifier para o nome da tabela."""
    q = sql.SQL("""
        SELECT id, received_at, raw
        FROM {table}
        WHERE raw ILIKE %s
          AND id >= %s
        ORDER BY id ASC
        LIMIT %s
    """).format(table=sql.Identifier(table))

    like_pattern = "%CALL_END%"
    with conn.cursor() as cur:
        cur.execute(q, (like_pattern, min_id, limit))
        for row in cur.fetchall():
            yield row  # (id, received_at, raw)

# ------------ Frame builder ---------------------------------------------------

def build_dataframe(rows, tzname: str) -> pd.DataFrame:
    """Mapeia syslog -> colunas mínimas do phonecalls_phonecall."""
    out = []
    now = now_tz(tzname)

    for rid, received_at, raw in rows:
        start_local = to_local(received_at, tzname) if received_at else now
        duration = parse_duration_seconds(raw or "")
        end_local = start_local + dt.timedelta(seconds=duration)

        caller, callee = extract_two_numbers(raw or "")
        inbound, internal = guess_direction(caller, callee)

        row = {
            "created": now.strftime("%Y-%m-%d %H:%M:%S"),
            "modified": now.strftime("%Y-%m-%d %H:%M:%S"),
            "pabx": 1,
            "inbound": inbound,
            "internal": internal,
            "calltype": 0,
            "service": None,
            "description": f"IMPORT syslog id={rid}",
            "price": Decimal("0.00"),
            "org_price": Decimal("0.00"),
            "billedamount": Decimal("0.00"),
            "org_billedamount": Decimal("0.00"),
            "billedtime": 0,
            "startdate": start_local.date().isoformat(),
            "starttime": start_local.time().isoformat(timespec="seconds"),
            "stopdate": end_local.date().isoformat(),
            "stoptime": end_local.time().isoformat(timespec="seconds"),
            "duration": int(duration),
            "chargednumber": caller or "",
            "connectednumber": callee or "",
            "dialednumber": callee or "",
            "conditioncode": 0,
            "center_id": None,
            "company_id": None,
            "extension_id": None,
            "org_price_table_id": None,
            "organization_id": None,
            "price_table_id": None,
            "sector_id": None,
            "_syslog_id": rid,
            "_raw": raw,
        }
        out.append(row)

    cols = [
        "created","modified","pabx","inbound","internal","calltype","service",
        "description","price","org_price","billedamount","org_billedamount",
        "billedtime","startdate","starttime","stopdate","stoptime","duration",
        "chargednumber","connectednumber","dialednumber","conditioncode",
        "center_id","company_id","extension_id","org_price_table_id",
        "organization_id","price_table_id","sector_id",
        "_syslog_id","_raw",
    ]
    return pd.DataFrame(out, columns=cols)

# ------------ Main ------------------------------------------------------------

def main():
    p = argparse.ArgumentParser(
        description="Exporta CALL_END do PostgreSQL para Excel no formato phonecalls_phonecall.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    p.add_argument("--pg-host", default="127.0.0.1")
    p.add_argument("--pg-port", type=int, default=5432)
    p.add_argument("--pg-database", required=True)
    p.add_argument("--pg-user", required=True)
    p.add_argument("--pg-password", required=True)
    p.add_argument("--pg-table", default="syslog_events")
    p.add_argument("--pg-min-id", type=int, default=0)
    p.add_argument("--pg-limit", type=int, default=10000)
    p.add_argument("--timezone", default="America/Fortaleza")
    p.add_argument("--excel-out", default="./phonecalls_export.xlsx")
    args = p.parse_args()

    conn_str = (
        f"host={args.pg_host} port={args.pg_port} dbname={args.pg_database} "
        f"user={args.pg_user} password={args.pg_password} connect_timeout=10"
    )
    with psycopg.connect(conn_str) as conn:
        rows = list(fetch_syslog_rows(conn, args.pg_table, args.pg_min_id, args.pg_limit))
        df = build_dataframe(rows, args.timezone)
        df.to_excel(args.excel_out, index=False)
        print(f"Exportadas {len(df)} linhas para {args.excel_out}")

if __name__ == "__main__":
    main()
