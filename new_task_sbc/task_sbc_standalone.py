#!/usr/bin/env python3
"""
task_sbc_standalone.py — processa registros da SBC sem Django (psycopg + SQL puro)

- Classifica chamadas usando números controlados (tabela controlled_number_ranges
  e, opcionalmente, controlled_number_clients).
- Insere em phonecalls_phonecall preenchendo automaticamente colunas NOT NULL sem default.
- Modo de debug com logs detalhados e controle de verbosidade no console/arquivo.
- Controle de log de SQL (OFF/DEBUG/INFO) e opção de amostragem por lote (--sample).
- Deduplicação em lote de md_phonecall_id (remove SELECT 1 por registro).

Uso:
  python task_sbc_standalone.py --dsn "host=127.0.0.1 port=5432 dbname=test_db user=usr password=pwd" analysis
  python task_sbc_standalone.py --dsn "..." --debug --log-file sbc_debug.log analysis
  python task_sbc_standalone.py --dsn "..." --ranges-only --quiet-missing-clients --dry-run analysis
  python task_sbc_standalone.py --dsn "..." analysis-with-date 2025-10-20 2025-10-21

Requisitos:
  pip install "psycopg[binary]~=3.2"
"""

from __future__ import annotations

import argparse
import logging
import re
import sys
from typing import Iterable, List, Tuple, Dict, Any

import psycopg
from psycopg.errors import Error as PsyError

# Configuração global controlada pelo argparse
CONFIG = {
    'log_sql_level': 'DEBUG',   # OFF|DEBUG|INFO
    'log_params': True,
    'no_console': False,
}

# ------------------------------
# Logging
# ------------------------------
def setup_logging(debug: bool, log_file: str | None, console_level: str | None = None, no_console: bool = False):
    root = logging.getLogger()
    for h in list(root.handlers):
        root.removeHandler(h)
    root.setLevel(logging.DEBUG)

    if console_level:
        cons_level = getattr(logging, console_level.upper(), logging.INFO)
    else:
        cons_level = logging.WARNING if log_file else logging.INFO

    fmt = logging.Formatter("%(asctime)s | %(levelname)s | %(message)s")

    if not no_console:
        ch = logging.StreamHandler(sys.stdout)
        ch.setLevel(cons_level)
        ch.setFormatter(fmt)
        root.addHandler(ch)

    if log_file:
        fh = logging.FileHandler(log_file, encoding="utf-8")
        fh.setLevel(logging.DEBUG if debug else logging.INFO)
        fh.setFormatter(fmt)
        root.addHandler(fh)

    logging.debug("Logging iniciado (debug=%s, log_file=%s, console_level=%s, no_console=%s)",
                  debug, log_file, logging.getLevelName(cons_level) if not no_console else "OFF", no_console)

def safe_preview(val: Any, maxlen: int = 200) -> str:
    s = repr(val)
    return (s[:maxlen] + "...") if len(s) > maxlen else s

def log_sql(sql: str, params: list[Any] | tuple[Any, ...] | None) -> None:
    lvl = str(CONFIG.get('log_sql_level', 'DEBUG')).upper()
    if lvl == 'OFF':
        return
    level_num = logging.DEBUG if lvl == 'DEBUG' else logging.INFO
    if params is None or not CONFIG.get('log_params', True):
        logging.log(level_num, "SQL: %s", sql)
        return
    pv = ", ".join(safe_preview(p) for p in params)
    logging.log(level_num, "SQL: %s | params=[%s]", sql, pv)
    return

# ------------------------------
# Constantes mínimas de PABX
# ------------------------------
IN_CALL, OUT_CALL, INTERNAL, UNCLASSIFIED = 1, 2, 3, 99
FREE = 0
DDD_LEN = 2  # DDD de 2 dígitos

# Colunas de timestamp comuns para auto-preenchimento com CURRENT_TIMESTAMP
AUTO_TS_COLUMNS = {"created", "created_at", "modified", "modified_at", "updated", "updated_at", "created_on", "updated_on"}

# ------------------------------
# Utilidades de número
# ------------------------------
def norm(num: str) -> str:
    """Mantém apenas dígitos."""
    return re.sub(r"\D+", "", num or "")

def split_ddd_local(n: str) -> Tuple[str, str]:
    """Separa DDD (2 dígitos) e parte local."""
    n = norm(n)
    if len(n) <= DDD_LEN:
        return "", n
    return n[:DDD_LEN], n[DDD_LEN:]

# ------------------------------
# Coerção de valores para NOT NULL
# ------------------------------
def _coerce_required_value(dtype: str):
    dt = (dtype or "").lower()
    if "timestamp" in dt:
        return ("__CURRENT_TIMESTAMP__",)
    if dt == "date":
        return ("__CURRENT_DATE__",)
    if "time" in dt:
        return ("__CURRENT_TIME__",)
    if "boolean" in dt:
        return False
    if any(k in dt for k in ("integer", "numeric", "double", "real", "bigint", "smallint", "decimal")):
        return 0
    return ""  # texto/json/etc.

# ------------------------------
# Fonte dos números controlados
# ------------------------------
def load_controlled(conn: psycopg.Connection, ranges_only: bool = False, quiet_missing_clients: bool = False) -> Tuple[set[str], list[Tuple[str, int, int]]]:
    nums: set[str] = set()
    ranges: list[Tuple[str, int, int]] = []

    with conn.cursor() as cur:
        # Números diretos (opcional)
        if not ranges_only:
            try:
                sql = "SELECT ddd, number_local FROM controlled_number_clients"
                log_sql(sql, None)
                cur.execute(sql)
                rows = cur.fetchall()
                logging.debug("controlled_number_clients (ddd, number_local): %d linhas", len(rows))
                for ddd, local in rows:
                    d = norm(str(ddd))
                    l = norm(str(local))
                    if d and l:
                        nums.add(d + l)
            except Exception as e:
                logging.debug("Falha ao ler (ddd, number_local): %s", e)
                try:
                    sql = "SELECT full_number FROM controlled_number_clients"
                    log_sql(sql, None)
                    cur.execute(sql)
                    rows = cur.fetchall()
                    logging.debug("controlled_number_clients (full_number): %d linhas", len(rows))
                    for (full,) in rows:
                        f = norm(str(full))
                        if f:
                            nums.add(f)
                except Exception as e2:
                    if not quiet_missing_clients:
                        logging.debug("Não foi possível ler controlled_number_clients (%s)", e2)

        # Faixas
        try:
            sql = "SELECT ddd, start_local, end_local FROM controlled_number_ranges"
            log_sql(sql, None)
            cur.execute(sql)
            rows = cur.fetchall()
            logging.debug("controlled_number_ranges: %d linhas", len(rows))
            for ddd, s, e in rows:
                d = norm(str(ddd))
                try:
                    s = int(norm(str(s))); e = int(norm(str(e)))
                except ValueError:
                    logging.warning("Faixa inválida ignorada: ddd=%s, start=%r, end=%r", ddd, s, e)
                    continue
                if d and s <= e:
                    ranges.append((d, s, e))
        except Exception as e:
            logging.warning("Não foi possível ler controlled_number_ranges (%s)", e)

    logging.info("Números controlados carregados: %d diretos, %d faixas", len(nums), len(ranges))
    return nums, ranges

def is_in_ranges(n: str, ranges: list[Tuple[str, int, int]]) -> bool:
    ddd, local = split_ddd_local(n)
    if not (ddd and local.isdigit()):
        return False
    x = int(local)
    for rddd, s, e in ranges:
        if rddd == ddd and s <= x <= e:
            return True
    return False

def is_controlled(n: str, nums: set[str], ranges: list[Tuple[str, int, int]]) -> bool:
    n = norm(n)
    return bool(n) and ((n in nums) or is_in_ranges(n, ranges))

def classify_by_controlled(charged: str, dialed: str, nums: set[str], ranges: list[Tuple[str, int, int]]):
    c = is_controlled(charged, nums, ranges)
    d = is_controlled(dialed,  nums, ranges)
    if c and not d:
        return OUT_CALL, False, "fallback: charged ∈ controlados, dialed ∉ controlados — OUT_CALL"
    if d and not c:
        return IN_CALL, True,  "fallback: dialed ∈ controlados, charged ∉ controlados — IN_CALL"
    if c and d:
        return INTERNAL, None, "fallback: ambos controlados — INTERNAL"
    return UNCLASSIFIED, None, "fallback: nenhum controlado — UNCLASSIFIED"

# ------------------------------
# Metadados do schema alvo
# ------------------------------
def get_table_columns(conn: psycopg.Connection, table: str) -> set[str]:
    with conn.cursor() as cur:
        sql = """
            SELECT c.column_name
            FROM information_schema.columns c
            WHERE c.table_name = %s
              AND c.table_schema = ANY (current_schemas(true))
        """
        log_sql(sql, (table,))
        cur.execute(sql, (table,))
        cols = {r[0] for r in cur.fetchall()}
        if not cols:
            sql2 = "SELECT c.column_name FROM information_schema.columns c WHERE c.table_name = %s"
            log_sql(sql2, (table,))
            cur.execute(sql2, (table,))
            cols = {r[0] for r in cur.fetchall()}
        logging.info("Colunas em %s: %s", table, sorted(cols))
        return cols

def get_required_columns(conn: psycopg.Connection, table: str) -> Dict[str, str]:
    with conn.cursor() as cur:
        sql = """
            SELECT c.column_name, c.data_type, c.is_nullable, c.column_default
            FROM information_schema.columns c
            WHERE c.table_name = %s
              AND c.table_schema = ANY (current_schemas(true))
        """
        log_sql(sql, (table,))
        cur.execute(sql, (table,))
        required: Dict[str, str] = {}
        for name, dtype, is_nullable, default in cur.fetchall():
            if is_nullable == "NO" and default is None:
                required[name] = dtype or ""
        logging.info("Colunas NOT NULL sem default em %s: %s", table, sorted(required.items()))
        return required

# ------------------------------
# Seleção de pendências
# ------------------------------
def pending_ids(conn: psycopg.Connection, src_table: str, dst_table: str, event_type: str, limit: int, negate_md: bool) -> list[int]:
    with conn.cursor() as cur:
        if negate_md:
            sql = f"""
                SELECT s.id
                FROM {src_table} s
                WHERE s.event_type = %s
                  AND NOT EXISTS (
                      SELECT 1 FROM {dst_table} p
                      WHERE p.md_phonecall_id = -s.id
                  )
                ORDER BY s.id
                LIMIT %s
            """
        else:
            sql = f"""
                SELECT s.id
                FROM {src_table} s
                WHERE s.event_type = %s
                  AND NOT EXISTS (
                      SELECT 1 FROM {dst_table} p
                      WHERE p.md_phonecall_id = s.id
                  )
                ORDER BY s.id
                LIMIT %s
            """
        log_sql(sql, (event_type, limit))
        cur.execute(sql, (event_type, limit))
        out = [r[0] for r in cur.fetchall()]
        logging.info("pending_ids: %d", len(out))
        return out

def pending_ids_by_date(conn: psycopg.Connection, src_table: str, dst_table: str, event_type: str, dates: Iterable[str], limit: int, negate_md: bool) -> list[int]:
    with conn.cursor() as cur:
        if negate_md:
            sql = f"""
                SELECT s.id
                FROM {src_table} s
                WHERE s.event_type = %s
                  AND s.startdate = ANY(%s)
                  AND NOT EXISTS (
                      SELECT 1 FROM {dst_table} p
                      WHERE p.md_phonecall_id = -s.id
                  )
                ORDER BY s.id
                LIMIT %s
            """
        else:
            sql = f"""
                SELECT s.id
                FROM {src_table} s
                WHERE s.event_type = %s
                  AND s.startdate = ANY(%s)
                  AND NOT EXISTS (
                      SELECT 1 FROM {dst_table} p
                      WHERE p.md_phonecall_id = s.id
                  )
                ORDER BY s.id
                LIMIT %s
            """
        log_sql(sql, (event_type, list(dates), limit))
        cur.execute(sql, (event_type, list(dates), limit))
        out = [r[0] for r in cur.fetchall()]
        logging.info("pending_ids_by_date: %d", len(out))
        return out

# ------------------------------
# Processamento (INSERT dinâmico)
# ------------------------------
def process_batch(
    conn: psycopg.Connection,
    src_table: str,
    dst_table: str,
    ids: list[int],
    nums: set[str],
    ranges: list[Tuple[str, int, int]],
    dest_cols: set[str],
    negate_md: bool,
    dry_run: bool = False,
) -> int:
    if not ids:
        return 0

    required = get_required_columns(conn, dst_table)

    with conn.cursor() as cur:
        sql = f"""
            SELECT id, hostid, startdate, starttime, stopdate, stoptime,
                   COALESCE(duration,0),
                   COALESCE(dialednumber,''), COALESCE(connectednumber,''),
                   COALESCE(chargednumber, COALESCE(connectednumber,'')),
                   COALESCE(conditioncode,0),
                   COALESCE(callcasedata,0), COALESCE(seqnumber,0), COALESCE(seqlim,0),
                   COALESCE(callid,''), COALESCE(callidass1,''), COALESCE(callidass2,'')
            FROM {src_table}
            WHERE id = ANY(%s) AND event_type = 'CALL_END'
            ORDER BY id
        """
        log_sql(sql, (ids,))
        cur.execute(sql, (ids,))
        rows = cur.fetchall()
        logging.info("Lote SBC carregado: %d linhas", len(rows))

        # Deduplicação em lote por md_phonecall_id
        md_ids = [(-r[0] if negate_md else r[0]) for r in rows]
        if md_ids:
            sql_seen = f"SELECT md_phonecall_id FROM {dst_table} WHERE md_phonecall_id = ANY(%s)"
            log_sql(sql_seen, (md_ids,))
            cur.execute(sql_seen, (md_ids,))
            seen = {r[0] for r in cur.fetchall()}
            rows = [r for r in rows if ((-r[0] if negate_md else r[0]) not in seen)]
            logging.info("Deduplicados por md_phonecall_id: %d restantes", len(rows))

        # Sample opcional
        try:
            from types import SimpleNamespace
            args_ref = globals().get('_ARGS_REF', None)
            sample_n = getattr(args_ref, 'sample', 0) if args_ref else 0
        except Exception:
            sample_n = 0

        if sample_n and len(rows) > sample_n:
            logging.info("Sampleando %d de %d registros do lote", sample_n, len(rows))
            rows = rows[:sample_n]

        inserted = 0
        for (
            sid,
            hostid,
            sdate,
            stime,
            edate,
            etime,
            duration,
            dialed,
            connected,
            charged,
            cc,
            callcasedata,
            seqnumber,
            seqlim,
            callid,
            callidass1,
            callidass2,
        ) in rows:

            md_id = -sid if negate_md else sid

            # Classificação por números controlados (fallback)
            pabx, inbound, why = classify_by_controlled(charged, dialed, nums, ranges)
            desc = f"Ainda não implementado por cc: {cc} — {why}"
            logging.debug("Classificação id=%s | pabx=%s inbound=%s | charged=%s dialed=%s | %s",
                          sid, pabx, inbound, charged, dialed, why)

            # Monta campos dinamicamente
            row = {
                "id": md_id,
                "md_phonecall_id": md_id,
                "startdate": sdate,
                "starttime": stime,
                "stopdate": edate,
                "stoptime": etime,
                "duration": duration,
                "dialednumber": dialed,
                "connectednumber": connected,
                "chargednumber": charged,
                "conditioncode": cc,
                "callcasedata": callcasedata,
                "seqnumber": seqnumber,
                "seqlim": seqlim,
                "callid": callid,
                "callidass1": callidass1,
                "callidass2": callidass2,
                "pabx": pabx,
            }

            if "hostid_id" in dest_cols:
                row["hostid_id"] = hostid
            elif "hostid" in dest_cols:
                row["hostid"] = hostid

            if "inbound" in dest_cols:
                row["inbound"] = inbound if inbound is not None else False
            if "calltype" in dest_cols:
                row["calltype"] = FREE
            if "description" in dest_cols:
                row["description"] = desc

            # row.pop("id", None)  # keep id filled with md_id

            for ts in AUTO_TS_COLUMNS:
                if ts in dest_cols and ts not in row:
                    row[ts] = None  # CURRENT_TIMESTAMP

            for col, dtype in required.items():
                if col not in dest_cols:
                    continue
                if col in AUTO_TS_COLUMNS:
                    if col not in row:
                        row[col] = None  # CURRENT_TIMESTAMP
                    continue
                if col == "id" and ("id" in row):
                    pass
                elif col not in row or row[col] is None:
                    row[col] = _coerce_required_value(dtype)

            # Garante 'id' preenchido conforme estratégia solicitada: id = -sid (ou sid)
            if ("id" in required) and ("id" in dest_cols) and ("id" not in row):
                row["id"] = -sid if negate_md else sid

            cols = [c for c in row.keys() if c in dest_cols]
            if not cols:
                logging.warning("Nenhuma coluna de destino aplicável para id=%s", sid)
                continue

            values_sql: list[str] = []
            params: list[object] = []
            for c in cols:
                v = row[c]
                if (c in AUTO_TS_COLUMNS and v is None) or v == ("__CURRENT_TIMESTAMP__",):
                    values_sql.append("CURRENT_TIMESTAMP")
                elif v == ("__CURRENT_DATE__",):
                    values_sql.append("CURRENT_DATE")
                elif v == ("__CURRENT_TIME__",):
                    values_sql.append("CURRENT_TIME")
                else:
                    values_sql.append("%s")
                    params.append(v)

            collist = ", ".join(cols)
            placeholders = ", ".join(values_sql)
            sql_insert = f"INSERT INTO {dst_table} ({collist}) VALUES ({placeholders})"

            # DRY-RUN logging: params bonitos
            params_display = []
            for pval in params:
                try:
                    iso = getattr(pval, "isoformat", None)
                    params_display.append(iso() if callable(iso) else pval)
                except Exception:
                    params_display.append(pval)

            try:
                args_ref = globals().get('_ARGS_REF', None)
                dry_run_flag = getattr(args_ref, 'dry_run', dry_run) if args_ref else dry_run
            except Exception:
                dry_run_flag = dry_run

            if dry_run_flag:
                logging.info("[DRY-RUN] id=%s -> %s | params=%s", sid, sql_insert, params_display)
                inserted += 1
                continue

            try:
                log_sql(sql_insert, params)
                cur.execute(sql_insert, params)
                inserted += 1
            except PsyError as e:
                logging.error("Falha INSERT id=%s | erro=%s", sid, e.__class__.__name__)
                logging.error("Detalhe erro: %s", getattr(e, "pgerror", None))
                logging.error("SQLSTATE: %s", getattr(e, "sqlstate", None))
                logging.error("SQL: %s", sql_insert)
                logging.error("PARAMS: %s", [safe_preview(p) for p in params])
                logging.error("ROW CONTEXT: %s", {k: safe_preview(v) for k, v in row.items()})
                continue

        logging.info("Inseridos neste lote: %d", inserted)
        return inserted

# ------------------------------
# CLI
# ------------------------------
def main() -> None:
    ap = argparse.ArgumentParser(description="Processa SBC sem Django (SQL puro)")
    ap.add_argument("--dsn", required=True, help="Ex.: 'host=127.0.0.1 port=5432 dbname=test_db user=usr password=pwd' ou URL postgresql://")
    ap.add_argument("command", choices=["analysis", "analysis-with-date", "reanalysis"], help="Tipo de processamento")
    ap.add_argument("dates", nargs="*", help="YYYY-MM-DD (para analysis-with-date)")

    ap.add_argument("--src-table", default="sbc_phonecall", help="Tabela de origem (default: sbc_phonecall)")
    ap.add_argument("--dst-table", default="phonecalls_phonecall", help="Tabela de destino (default: phonecalls_phonecall)")
    ap.add_argument("--event-type", default="CALL_END", help="Tipo de evento a filtrar na origem (default: CALL_END)")
    ap.add_argument("--batch-size", type=int, default=5000, help="Tamanho do lote (default: 5000)")
    ap.add_argument("--no-negate-md", action="store_true", help="Não negue o md_phonecall_id (use id positivo)")
    ap.add_argument("--dry-run", action="store_true", help="Não insere; apenas simula (loga)")

    # Flags de leitura e logging
    ap.add_argument("--ranges-only", action="store_true", help="Ignore controlled_number_clients e use apenas controlled_number_ranges")
    ap.add_argument("--quiet-missing-clients", action="store_true", help="Suprime logs sobre ausência de controlled_number_clients")
    ap.add_argument("--debug", action="store_true", help="Ativa logs detalhados de debug")
    ap.add_argument("--log-file", default=None, help="Caminho para arquivo de log (opcional)")
    ap.add_argument("--console-level", choices=["DEBUG","INFO","WARNING","ERROR","CRITICAL"],
                    help="Nível de log no console (padrão: INFO; se --log-file, padrão WARNING)")
    ap.add_argument("--no-console", action="store_true", help="Não imprimir nada no console (apenas arquivo, se fornecido)")
    ap.add_argument("--log-sql-level", choices=["OFF","DEBUG","INFO"], help="Nível de log para SQL (OFF/DEBUG/INFO)")
    ap.add_argument("--log-params", action="store_true", help="Logar parâmetros das queries (default: ligado se --debug e sem --no-console)")
    ap.add_argument("--sample", type=int, default=0, help="Processar/logar só N registros por lote (0 = todos)")

    args = ap.parse_args()
    setup_logging(args.debug, args.log_file, args.console_level, args.no_console)

    # CONFIG defaults baseados em flags
    if args.log_sql_level:
        CONFIG['log_sql_level'] = args.log_sql_level
    else:
        CONFIG['log_sql_level'] = 'DEBUG' if args.debug else 'INFO'
        if args.no_console:
            CONFIG['log_sql_level'] = 'OFF'
    CONFIG['log_params'] = True if args.log_params else (bool(args.debug) and not args.no_console)
    CONFIG['no_console'] = bool(args.no_console)

    # expor args para funções (sample/dry-run)
    globals()['_ARGS_REF'] = args

    negate_md = not args.no_negate_md

    logging.info("Iniciando: cmd=%s src=%s dst=%s batch=%d negate_md=%s dry_run=%s",
                 args.command, args.src_table, args.dst_table, args.batch_size, negate_md, args.dry_run)

    with psycopg.connect(args.dsn, autocommit=True) as conn:
        logging.info("Conectado ao Postgres")
        nums, ranges = load_controlled(conn, ranges_only=args.ranges_only, quiet_missing_clients=args.quiet_missing_clients)
        dest_cols = get_table_columns(conn, args.dst_table)

        if args.command == "analysis":
            total = 0
            while True:
                ids = pending_ids(conn, args.src_table, args.dst_table, args.event_type, args.batch_size, negate_md)
                if not ids:
                    break
                total += process_batch(conn, args.src_table, args.dst_table, ids, nums, ranges, dest_cols, negate_md, args.dry_run)
            logging.info("%d SBC analisadas", total)
            if not CONFIG.get('no_console'):
                print(f"{total} SBC analisadas")

        elif args.command == "analysis-with-date":
            if not args.dates:
                raise SystemExit("Forneça ao menos uma data YYYY-MM-DD")
            ids = pending_ids_by_date(conn, args.src_table, args.dst_table, args.event_type, args.dates, 10**7, negate_md)
            total = 0
            for i in range(0, len(ids), args.batch_size):
                total += process_batch(conn, args.src_table, args.dst_table, ids[i:i+args.batch_size], nums, ranges, dest_cols, negate_md, args.dry_run)
            logging.info("%d SBC analisadas (datas: %s)", total, ", ".join(args.dates))
            if not CONFIG.get('no_console'):
                print(f"{total} SBC analisadas (datas: {', '.join(args.dates)})")

        elif args.command == "reanalysis":
            logging.info("Reanálise: personalize o critério no código conforme sua necessidade.")
            if not CONFIG.get('no_console'):
                print("Reanálise: personalize o critério no código conforme sua necessidade.")

if __name__ == "__main__":
    main()
