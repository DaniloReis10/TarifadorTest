#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
syslog_ingestor.py
------------------
Servidor simples de Syslog (UDP e TCP) que ingere mensagens em PostgreSQL.

Recursos:
- Escuta UDP e/ou TCP em host/port configuráveis (env ou flags).
- Fila com worker para inserção no Postgres (batch).
- Criação automática da tabela (se não existir).
- Tratamento de SIGTERM/SIGINT para desligar com graça (systemd friendly).
- Logs claros de status (stdout).

Requisitos:
  pip install psycopg2-binary

Exemplos:
  python3 syslog_ingestor.py
  python3 syslog_ingestor.py --listen-host 0.0.0.0 --udp-port 5514 --tcp-port 5514
  python3 syslog_ingestor.py --no-tcp
  python3 syslog_ingestor.py --no-udp --tcp-port 5515

Variáveis de ambiente úteis (podem ser sobrescritas por flags):
  INGEST_LISTEN_HOST=0.0.0.0
  INGEST_UDP_PORT=5514
  INGEST_TCP_PORT=5514
  INGEST_ENABLE_UDP=1
  INGEST_ENABLE_TCP=1
  PGHOST=localhost
  PGPORT=5432
  PGDATABASE=syslogdb
  PGUSER=sysloguser
  PGPASSWORD=senha

Tabela criada automaticamente (se não existir):
  CREATE TABLE IF NOT EXISTS syslog_events (
      id BIGSERIAL PRIMARY KEY,
      received_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
      transport TEXT NOT NULL,            -- 'udp' ou 'tcp'
      src_addr   TEXT NOT NULL,           -- "ip:porta" de origem
      event_type TEXT,                    -- tentativa de extrair do payload (opcional)
      raw        TEXT NOT NULL            -- mensagem completa
  );
"""
from __future__ import annotations
import argparse
import os
import sys
import socket
import threading
import queue
import time
import signal
from datetime import datetime, timezone
from typing import Optional, Tuple

# ------------------------ Config & Args ------------------------

def env_bool(name: str, default: bool) -> bool:
    val = os.getenv(name, None)
    if val is None:
        return default
    return str(val).lower() not in ("0", "false", "no", "off", "")

def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Syslog ingestor (UDP/TCP -> PostgreSQL)")
    p.add_argument("--listen-host", default=os.getenv("INGEST_LISTEN_HOST", "0.0.0.0"),
                   help="Host para escutar (default: 0.0.0.0)")
    p.add_argument("--udp-port", type=int, default=int(os.getenv("INGEST_UDP_PORT", "5514")),
                   help="Porta UDP (default: 5514)")
    p.add_argument("--tcp-port", type=int, default=int(os.getenv("INGEST_TCP_PORT", "5514")),
                   help="Porta TCP (default: 5514)")
    p.add_argument("--no-udp", action="store_true", help="Desabilita UDP")
    p.add_argument("--no-tcp", action="store_true", help="Desabilita TCP")
    p.add_argument("--batch-size", type=int, default=int(os.getenv("INGEST_BATCH_SIZE", "200")),
                   help="Tamanho do lote para inserir no DB (default: 200)")
    p.add_argument("--batch-wait", type=float, default=float(os.getenv("INGEST_BATCH_WAIT", "0.5")),
                   help="Espera máx em segundos para completar lote (default: 0.5)")
    p.add_argument("--db-schema", default=os.getenv("INGEST_DB_SCHEMA", ""),
                   help="Schema do Postgres (opcional). Ex: public")
    return p.parse_args()

ARGS = parse_args()
ENABLE_UDP = not ARGS.no_udp and env_bool("INGEST_ENABLE_UDP", True)
ENABLE_TCP = not ARGS.no_tcp and env_bool("INGEST_ENABLE_TCP", True)

# ------------------------ DB Helpers ------------------------
try:
    import psycopg2
    from psycopg2.extras import execute_values
except Exception as e:
    print("[FATAL] psycopg2 não está instalado. Rode: pip install psycopg2-binary", file=sys.stderr)
    raise

DB_CFG = {
    "host": os.getenv("PGHOST", "localhost"),
    "port": int(os.getenv("PGPORT", "5432")),
    "dbname": os.getenv("PGDATABASE", "syslogdb"),
    "user": os.getenv("PGUSER", "sysloguser"),
    "password": os.getenv("PGPASSWORD", ""),
}

TABLE_NAME = "syslog_events"
if ARGS.db_schema:
    TABLE_FQN = f"{ARGS.db_schema}.{TABLE_NAME}"
else:
    TABLE_FQN = TABLE_NAME

CREATE_TABLE_SQL = f"""
CREATE TABLE IF NOT EXISTS {TABLE_FQN} (
    id BIGSERIAL PRIMARY KEY,
    received_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    transport TEXT NOT NULL,
    src_addr   TEXT NOT NULL,
    event_type TEXT,
    raw        TEXT NOT NULL
);
"""

INSERT_SQL = f"INSERT INTO {TABLE_FQN} (received_at, transport, src_addr, event_type, raw) VALUES %s"

def db_connect():
    return psycopg2.connect(**DB_CFG)

def db_init():
    conn = db_connect()
    conn.autocommit = True
    with conn, conn.cursor() as cur:
        cur.execute(CREATE_TABLE_SQL)
    conn.close()

# ------------------------ Ingest Queue & Worker ------------------------
Message = Tuple[datetime, str, str, Optional[str], str]  # (ts, transport, src_addr, event_type, raw)

ingest_q: "queue.Queue[Message]" = queue.Queue(maxsize=10000)
shutdown_flag = threading.Event()

def extract_event_type(raw: str) -> Optional[str]:
    # Heurística opcional: capturar um token entre pipes (|TYPE|...) se existir.
    # Ex: "... |MEDIA_END|foo|bar" -> "MEDIA_END"
    try:
        first = raw.split("|", 2)
        if len(first) >= 3 and first[1] and len(first[1]) <= 64:
            return first[1].strip()
    except Exception:
        pass
    return None

def worker_thread():
    batch: list[Message] = []
    batch_size = ARGS.batch_size
    batch_wait = ARGS.batch_wait
    last_flush = time.time()

    conn = None
    cur = None

    def ensure_conn():
        nonlocal conn, cur
        if conn is None or conn.closed != 0:
            conn = db_connect()
            conn.autocommit = True
            cur = conn.cursor()

    while not shutdown_flag.is_set() or not ingest_q.empty():
        try:
            try:
                msg = ingest_q.get(timeout=0.1)
                batch.append(msg)
            except queue.Empty:
                pass

            now = time.time()
            if (batch and len(batch) >= batch_size) or (batch and (now - last_flush) >= batch_wait) or (shutdown_flag.is_set() and batch):
                try:
                    ensure_conn()
                    from psycopg2.extras import execute_values
                    values = [(m[0], m[1], m[2], m[3], m[4]) for m in batch]
                    execute_values(cur, INSERT_SQL, values, page_size=len(values))
                except Exception as e:
                    print(f"[DB] Falha ao inserir lote de {len(batch)}: {e}", file=sys.stderr)
                    try:
                        if conn:
                            conn.close()
                    except Exception:
                        pass
                    conn, cur = None, None
                    # re-enfileirar para tentar novamente
                    for item in batch:
                        try:
                            ingest_q.put_nowait(item)
                        except queue.Full:
                            print("[WARN] Fila cheia ao re-enfileirar após falha no DB.", file=sys.stderr)
                            break
                finally:
                    batch.clear()
                    last_flush = now
        except Exception as e:
            print(f"[WORKER] Erro inesperado: {e}", file=sys.stderr)
            time.sleep(0.1)

    # Flush final
    if batch:
        try:
            ensure_conn()
            values = [(m[0], m[1], m[2], m[3], m[4]) for m in batch]
            execute_values(cur, INSERT_SQL, values, page_size=len(values))
        except Exception as e:
            print(f"[DB] Falha no flush final ({len(batch)} msgs): {e}", file=sys.stderr)
        finally:
            try:
                if conn:
                    conn.close()
            except Exception:
                pass

# ------------------------ UDP Server ------------------------
def udp_server(host: str, port: int):
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF, 2**20)
    except Exception:
        pass
    sock.bind((host, port))
    print(f"[OK] UDP syslog listening on {host}:{port}")
    sock.settimeout(0.5)
    while not shutdown_flag.is_set():
        try:
            data, addr = sock.recvfrom(65535)
        except socket.timeout:
            continue
        except Exception as e:
            if not shutdown_flag.is_set():
                print(f"[UDP] Erro ao receber: {e}", file=sys.stderr)
            continue
        try:
            raw = data.decode("utf-8", errors="replace")
            etype = extract_event_type(raw)
            src = f"{addr[0]}:{addr[1]}"
            ts = datetime.now(timezone.utc)
            ingest_q.put_nowait((ts, "udp", src, etype, raw))
        except queue.Full:
            print("[WARN] Fila cheia: descartando mensagem UDP.", file=sys.stderr)
        except Exception as e:
            print(f"[UDP] Erro ao enfileirar: {e}", file=sys.stderr)
    try:
        sock.close()
    except Exception:
        pass
    print("[UDP] Encerrado.")

# ------------------------ TCP Server ------------------------
def tcp_client_handler(conn: socket.socket, addr: Tuple[str, int]):
    conn.settimeout(1.0)
    src = f"{addr[0]}:{addr[1]}"
    buf = b""
    try:
        while not shutdown_flag.is_set():
            try:
                chunk = conn.recv(4096)
                if not chunk:
                    break
                buf += chunk
                while b"\n" in buf:
                    line, buf = buf.split(b"\n", 1)
                    line = line.rstrip(b"\r")
                    if not line:
                        continue
                    raw = line.decode("utf-8", errors="replace")
                    etype = extract_event_type(raw)
                    ts = datetime.now(timezone.utc)
                    try:
                        ingest_q.put_nowait((ts, "tcp", src, etype, raw))
                    except queue.Full:
                        print("[WARN] Fila cheia: descartando mensagem TCP.", file=sys.stderr)
            except socket.timeout:
                continue
            except Exception as e:
                print(f"[TCP] Erro em recv de {src}: {e}", file=sys.stderr)
                break
    finally:
        try:
            conn.close()
        except Exception:
            pass

def tcp_server(host: str, port: int, backlog: int = 200):
    srv = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    srv.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    srv.bind((host, port))
    srv.listen(backlog)
    print(f"[OK] TCP syslog listening on {host}:{port}")
    srv.settimeout(0.5)
    threads: list[threading.Thread] = []
    try:
        while not shutdown_flag.is_set():
            try:
                conn, addr = srv.accept()
            except socket.timeout:
                continue
            except Exception as e:
                if not shutdown_flag.is_set():
                    print(f"[TCP] Erro em accept: {e}", file=sys.stderr)
                continue
            t = threading.Thread(target=tcp_client_handler, args=(conn, addr), daemon=True,
                                 name=f"tcp-client-{addr[0]}:{addr[1]}")
            t.start()
            threads.append(t)
    finally:
        try:
            srv.close()
        except Exception:
            pass
        deadline = time.time() + 2.0
        for t in threads:
            remaining = deadline - time.time()
            if remaining <= 0:
                break
            t.join(timeout=remaining)
        print("[TCP] Encerrado.")

# ------------------------ Main ------------------------
def main():
    if (ENABLE_UDP and ARGS.udp_port < 1024) or (ENABLE_TCP and ARGS.tcp_port < 1024):
        print("[WARN] Escutar em portas <1024 exige privilégios ou setcap no binário do Python.", file=sys.stderr)

    print(f"[BOOT] Iniciando syslog_ingestor | host={ARGS.listen_host} udp={ENABLE_UDP}:{ARGS.udp_port} tcp={ENABLE_TCP}:{ARGS.tcp_port}")
    print(f"[BOOT] Conectando ao PostgreSQL em {DB_CFG['host']}:{DB_CFG['port']} db={DB_CFG['dbname']} user={DB_CFG['user']}")
    try:
        db_init()
        print("[OK] Tabela verificada/criada.")
    except Exception as e:
        print(f"[FATAL] Falha ao preparar DB: {e}", file=sys.stderr)
        sys.exit(2)

    worker = threading.Thread(target=worker_thread, name="db-worker", daemon=True)
    worker.start()

    threads: list[threading.Thread] = []
    if ENABLE_UDP:
        t_udp = threading.Thread(target=udp_server, args=(ARGS.listen_host, ARGS.udp_port), daemon=True, name="udp-server")
        t_udp.start()
        threads.append(t_udp)
    if ENABLE_TCP:
        t_tcp = threading.Thread(target=tcp_server, args=(ARGS.listen_host, ARGS.tcp_port), daemon=True, name="tcp-server")
        t_tcp.start()
        threads.append(t_tcp)

    def handle_signal(signum, frame):
        print(f"[SHUTDOWN] Sinal {signum} recebido, encerrando...")
        shutdown_flag.set()
    signal.signal(signal.SIGINT, handle_signal)
    signal.signal(signal.SIGTERM, handle_signal)

    try:
        while any(t.is_alive() for t in threads):
            time.sleep(0.5)
    except KeyboardInterrupt:
        handle_signal(signal.SIGINT, None)

    print("[SHUTDOWN] Aguardando fila drenar...")
    shutdown_flag.set()
    worker.join(timeout=5.0)
    print("[BYE] Encerrado com sucesso.")

if __name__ == "__main__":
    main()
