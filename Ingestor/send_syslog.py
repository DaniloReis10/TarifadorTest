#!/usr/bin/env python3
"""
send_syslog.py
Replay de um arquivo de syslog: envia cada linha para um host:port via UDP ou TCP.

Exemplos (no macOS):
  python3 send_syslog.py syslog.txt --transport udp --host 203.0.113.42 --port 5514 --rate 200 --tty
  python3 send_syslog.py syslog.txt --transport tcp --host 203.0.113.42 --port 5514 --delay 0.01 --tty
  python3 send_syslog.py syslog.txt --loop --rate 100

Observações:
- UDP: envia cada linha como um datagrama separado.
- TCP: abre conexão, envia linha + \n, mantém ou reabre em caso de erro.
- Use --rate ou --delay para controlar a velocidade de envio (não use ambos).
"""
from __future__ import annotations
import argparse
import socket
import time
import sys
import os
from typing import Optional

def send_udp_line(sock: socket.socket, addr, line: bytes) -> None:
    sock.sendto(line, addr)

def send_tcp_line(sock: socket.socket, addr, line: bytes, reconnect: bool = True) -> socket.socket:
    try:
        sock.sendall(line + b"\n")
        return sock
    except (BrokenPipeError, ConnectionResetError, OSError):
        if not reconnect:
            raise
        # reconectar
        try:
            sock.close()
        except Exception:
            pass
        new = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        new.settimeout(5)
        new.connect(addr)
        new.sendall(line + b"\n")
        return new

def open_tcp(addr, timeout=5) -> socket.socket:
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.settimeout(timeout)
    s.connect(addr)
    return s

def main():
    p = argparse.ArgumentParser(description="Replay syslog file to UDP/TCP host:port")
    p.add_argument("file", nargs="?", default="syslog.txt", help="Arquivo de syslog a ser enviado")
    p.add_argument("--host", default="127.0.0.1", help="Host destino (IP público da EC2, por ex.)")
    p.add_argument("--port", type=int, default=5514, help="Porta destino (padrão 5514)")
    p.add_argument("--transport", choices=("udp","tcp"), default="udp", help="Protocolo (udp/tcp)")
    p.add_argument("--rate", type=float, default=0.0, help="Linhas por segundo (0 = desativado)")
    p.add_argument("--delay", type=float, default=0.0, help="Delay fixo entre linhas em segundos (0 = desativado)")
    p.add_argument("--loop", action="store_true", help="Repetir o envio indefinidamente")
    p.add_argument("--once", dest="once", action="store_true", help="Enviar o arquivo apenas uma vez (default)")
    p.add_argument("--tty", action="store_true", help="Mostrar progresso no terminal")
    args = p.parse_args()

    path = args.file
    if not os.path.isfile(path):
        print(f"Arquivo não encontrado: {path}", file=sys.stderr)
        sys.exit(2)

    addr = (args.host, args.port)
    delay = args.delay
    if args.rate > 0:
        delay = 1.0 / args.rate

    if args.transport == "udp":
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        try:
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_SNDBUF, 2**20)
        except Exception:
            pass
    else:
        sock = None

    try:
        while True:
            with open(path, "rb") as fh:
                line_num = 0
                for raw in fh:
                    line_num += 1
                    line = raw.rstrip(b"\r\n")
                    if not line:
                        continue

                    try:
                        if args.transport == "udp":
                            send_udp_line(sock, addr, line)
                        else:
                            if sock is None:
                                try:
                                    sock = open_tcp(addr)
                                except Exception as e:
                                    print(f"[TCP] falha ao conectar {addr}: {e}", file=sys.stderr)
                                    time.sleep(1.0)
                                    continue
                            try:
                                sock = send_tcp_line(sock, addr, line, reconnect=True)
                            except Exception as e:
                                print(f"[TCP] erro ao enviar: {e}", file=sys.stderr)
                                try:
                                    sock.close()
                                except Exception:
                                    pass
                                sock = None
                                time.sleep(0.5)
                                continue

                    except Exception as ex:
                        print(f"[ERRO] linha {line_num}: {ex}", file=sys.stderr)

                    if args.tty:
                        print(f"\r-> enviado linha {line_num}", end="", flush=True)

                    if delay > 0:
                        time.sleep(delay)

                if args.tty:
                    print("", flush=True)

            if args.loop:
                time.sleep(0.5)
                continue
            else:
                break

    finally:
        if sock:
            try:
                sock.close()
            except Exception:
                pass

if __name__ == "__main__":
    main()
