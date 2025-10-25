#!/usr/bin/env bash
# setup_port_redirect.sh
# Configure port forwarding between 514 and 5514 on Amazon Linux 2023.
# Defaults: forward external + local traffic FROM 514 TO 5514 using nftables and persist across reboots.
#
# Usage:
#   sudo ./setup_port_redirect.sh [--from 514] [--to 5514] [--method nft|iptables] [--both] [--remove] [--no-local]
#
# Examples:
#   # Default: 514 -> 5514 (external + local), using nftables, persistent
#   sudo ./setup_port_redirect.sh
#
#   # Also create reverse mapping (5514 -> 514)
#   sudo ./setup_port_redirect.sh --both
#
#   # Remove rules (whatever method was used last)
#   sudo ./setup_port_redirect.sh --remove
#
#   # Force iptables-compat mode (not persisted automatically here)
#   sudo ./setup_port_redirect.sh --method iptables
#
set -euo pipefail

FROM_PORT=514
TO_PORT=5514
METHOD="nft"          # nft | iptables
BOTH_DIRS="no"
LOCAL_OUTPUT="yes"    # also redirect traffic generated on the box itself
REMOVE="no"

# Parse args
while [[ $# -gt 0 ]]; do
  case "$1" in
    --from) FROM_PORT="${2:-}"; shift 2;;
    --to)   TO_PORT="${2:-}"; shift 2;;
    --method) METHOD="${2:-}"; shift 2;;
    --both) BOTH_DIRS="yes"; shift;;
    --no-local) LOCAL_OUTPUT="no"; shift;;
    --remove) REMOVE="yes"; shift;;
    -h|--help)
      sed -n '1,60p' "$0"
      exit 0
      ;;
    *)
      echo "Unknown argument: $1" >&2
      exit 2
      ;;
  esac
done

require_root() {
  if [[ $EUID -ne 0 ]]; then
    echo "[FATAL] Run as root (use sudo)." >&2
    exit 1
  fi
}

install_pkg() {
  local pkg="$1"
  if ! rpm -q "$pkg" >/dev/null 2>&1; then
    echo "[INFO] Installing package: $pkg"
    dnf install -y "$pkg"
  else
    echo "[INFO] Package already installed: $pkg"
  fi
}

nft_ensure_inet_nat_table() {
  # Create table/chain if not exists
  if ! nft list table inet portredir_nat >/dev/null 2>&1; then
    nft add table inet portredir_nat
  fi
  if ! nft list chain inet portredir_nat prerouting >/dev/null 2>&1; then
    nft 'add chain inet portredir_nat prerouting { type nat hook prerouting priority -100; }'
  fi
  if [[ "$LOCAL_OUTPUT" == "yes" ]]; then
    if ! nft list chain inet portredir_nat output >/dev/null 2>&1; then
      nft 'add chain inet portredir_nat output { type nat hook output priority -100; }'
    fi
  fi
}

nft_add_redirect() {
  local SRC_PORT="$1"
  local DST_PORT="$2"
  nft add rule inet portredir_nat prerouting tcp dport "$SRC_PORT" redirect to :"$DST_PORT" 2>/dev/null || true
  nft add rule inet portredir_nat prerouting udp dport "$SRC_PORT" redirect to :"$DST_PORT" 2>/dev/null || true
  if [[ "$LOCAL_OUTPUT" == "yes" ]]; then
    nft add rule inet portredir_nat output tcp dport "$SRC_PORT" redirect to :"$DST_PORT" 2>/dev/null || true
    nft add rule inet portredir_nat output udp dport "$SRC_PORT" redirect to :"$DST_PORT" 2>/dev/null || true
  fi
}

nft_del_redirect() {
  local SRC_PORT="$1"
  local DST_PORT="$2"
  # Delete any matching rules (if present). Use grep to find handles.
  local RS
  RS=$(nft -a list ruleset | awk "/table inet portredir_nat/,0" | grep -E "dport ${SRC_PORT} .* redirect to :?${DST_PORT}" || true)
  if [[ -n "$RS" ]]; then
    echo "$RS" | awk '{print $NF}' | while read -r handle; do
      # 'handle' may include 'handle N'; extract the number
      num=$(echo "$handle" | awk '{print $2}')
      if echo "$RS" | grep -q " prerouting .* dport ${SRC_PORT} .*:${DST_PORT} .* handle ${num}"; then
        nft delete rule inet portredir_nat prerouting handle "$num" 2>/dev/null || true
      fi
      if echo "$RS" | grep -q " output .* dport ${SRC_PORT} .*:${DST_PORT} .* handle ${num}"; then
        nft delete rule inet portredir_nat output handle "$num" 2>/dev/null || true
      fi
    done
  fi
}

nft_persist() {
  # Persist current ruleset
  echo "[INFO] Persisting nftables rules to /etc/sysconfig/nftables.conf"
  mkdir -p /etc/sysconfig
  nft list ruleset > /etc/sysconfig/nftables.conf
  systemctl enable --now nftables >/dev/null 2>&1 || true
}

iptables_add_redirect() {
  local SRC_PORT="$1"
  local DST_PORT="$2"
  iptables -t nat -A PREROUTING -p tcp --dport "$SRC_PORT" -j REDIRECT --to-ports "$DST_PORT" 2>/dev/null || true
  iptables -t nat -A PREROUTING -p udp --dport "$SRC_PORT" -j REDIRECT --to-ports "$DST_PORT" 2>/dev/null || true
  if [[ "$LOCAL_OUTPUT" == "yes" ]]; then
    iptables -t nat -A OUTPUT -p tcp --dport "$SRC_PORT" -j REDIRECT --to-ports "$DST_PORT" 2>/dev/null || true
    iptables -t nat -A OUTPUT -p udp --dport "$SRC_PORT" -j REDIRECT --to-ports "$DST_PORT" 2>/dev/null || true
  fi
}

iptables_del_redirect() {
  local SRC_PORT="$1"
  local DST_PORT="$2"
  # Delete by spec; repeat until gone
  while iptables -t nat -C PREROUTING -p tcp --dport "$SRC_PORT" -j REDIRECT --to-ports "$DST_PORT" 2>/dev/null; do
    iptables -t nat -D PREROUTING -p tcp --dport "$SRC_PORT" -j REDIRECT --to-ports "$DST_PORT"
  done
  while iptables -t nat -C PREROUTING -p udp --dport "$SRC_PORT" -j REDIRECT --to-ports "$DST_PORT" 2>/dev/null; do
    iptables -t nat -D PREROUTING -p udp --dport "$SRC_PORT" -j REDIRECT --to-ports "$DST_PORT"
  done
  if [[ "$LOCAL_OUTPUT" == "yes" ]]; then
    while iptables -t nat -C OUTPUT -p tcp --dport "$SRC_PORT" -j REDIRECT --to-ports "$DST_PORT" 2>/dev/null; do
      iptables -t nat -D OUTPUT -p tcp --dport "$SRC_PORT" -j REDIRECT --to-ports "$DST_PORT"
    done
    while iptables -t nat -C OUTPUT -p udp --dport "$SRC_PORT" -j REDIRECT --to-ports "$DST_PORT" 2>/dev/null; do
      iptables -t nat -D OUTPUT -p udp --dport "$SRC_PORT" -j REDIRECT --to-ports "$DST_PORT"
    done
  fi
}

main() {
  require_root

  if [[ "$METHOD" == "nft" ]]; then
    install_pkg nftables
    if [[ "$REMOVE" == "yes" ]]; then
      # Try to delete both directions
      nft_del_redirect "$FROM_PORT" "$TO_PORT"
      if [[ "$BOTH_DIRS" == "yes" ]]; then
        nft_del_redirect "$TO_PORT" "$FROM_PORT"
      fi
      echo "[OK] Removed nftables redirects (if present)."
      nft_persist
      exit 0
    fi
    nft_ensure_inet_nat_table
    nft_add_redirect "$FROM_PORT" "$TO_PORT"
    if [[ "$BOTH_DIRS" == "yes" ]]; then
      nft_add_redirect "$TO_PORT" "$FROM_PORT"
    fi
    echo "[OK] nftables redirect(s) applied."
    nft_persist
    nft list table inet portredir_nat
  elif [[ "$METHOD" == "iptables" ]]; then
    install_pkg iptables-nft
    if [[ "$REMOVE" == "yes" ]]; then
      iptables_del_redirect "$FROM_PORT" "$TO_PORT"
      if [[ "$BOTH_DIRS" == "yes" ]]; then
        iptables_del_redirect "$TO_PORT" "$FROM_PORT"
      fi
      echo "[OK] Removed iptables redirects (if present)."
      echo "[INFO] iptables rules are NOT persisted automatically by this script."
      exit 0
    fi
    iptables_add_redirect "$FROM_PORT" "$TO_PORT"
    if [[ "$BOTH_DIRS" == "yes" ]]; then
      iptables_add_redirect "$TO_PORT" "$FROM_PORT"
    fi
    echo "[OK] iptables redirect(s) applied."
    echo "[WARN] iptables rules are NOT persisted automatically here."
    iptables -t nat -S | egrep 'dport (514|5514)' || true
  else
    echo "[FATAL] Unknown method: $METHOD (use nft or iptables)"
    exit 2
  fi

  echo
  echo "[INFO] Verify listeners and redirects:"
  echo "  ss -lntup | egrep ':514|:5514' || true"
  echo "  ss -lnup  | egrep ':514|:5514' || true"
}

main "$@"
