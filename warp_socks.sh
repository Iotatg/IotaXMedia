#!/bin/bash
# Authored By Iota Coders © 2025-2026
# SPDX-License-Identifier: MIT
# Best-effort Cloudflare WARP SOCKS5 proxy for YouTube unblocking.
# Prints "socks5://<ip>:<port>" on success, nothing on failure.
# Safe: never changes the host default route. Only traffic sourced from the
# WARP interface (the SOCKS server's own outbound) is routed through WARP.
set -uo pipefail

PORT=9092
WORK=/tmp/warp
mkdir -p "$WORK"
cd "$WORK"

log() { echo "[warp] $*"; }

if [ ! -c /dev/net/tun ]; then
  log "no /dev/net/tun -> WARP unavailable"
  exit 1
fi
if ! command -v ip >/dev/null 2>&1; then
  log "iproute2 missing -> WARP unavailable"
  exit 1
fi

fetch() {
  [ -x "$2" ] && return 0
  curl -fsSL --max-time 90 "$1" -o "$2" && chmod +x "$2" || { log "download failed: $1"; exit 1; }
}

fetch "https://github.com/ViRb3/wgcf/releases/download/v2.2.3/wgcf_2.2.3_linux_amd64" wgcf
fetch "https://github.com/WireGuard/wireguard-go/releases/download/v0.0.20220316/wireguard-go_linux_amd64" wireguard-go
fetch "https://github.com/go-gost/gost/releases/download/v2.11.2/gost_2.11.2_linux_amd64.tar.gz" gost.tar.gz
if [ ! -x gost ]; then
  tar xzf gost.tar.gz 2>/dev/null && mv gost_*/gost . 2>/dev/null || { log "gost extract failed"; exit 1; }
fi

if [ ! -f wgcf-account.toml ]; then
  ./wgcf register --accept-tos || { log "wgcf register failed"; exit 1; }
fi
[ -f wgcf-profile.conf ] || ./wgcf generate || { log "wgcf generate failed"; exit 1; }

WG_IP=$(grep -oP 'Address\s*=\s*\K[0-9.]+' wgcf-profile.conf | head -1)
[ -n "$WG_IP" ] || { log "could not parse WARP address"; exit 1; }

./wireguard-go wg0 >/tmp/wireguard.log 2>&1 &
WG_PID=$!
sleep 3
if ! ip link show wg0 >/dev/null 2>&1; then
  log "wg0 interface did not come up"; kill $WG_PID 2>/dev/null; exit 1
fi
ip addr add "${WG_IP}/32" dev wg0 2>/dev/null || true
wg setconf wg0 wgcf-profile.conf 2>/dev/null || true
ip link set wg0 up 2>/dev/null || true

ip route add default dev wg0 table 51820 2>/dev/null || true
ip rule add from "$WG_IP" lookup 51820 2>/dev/null || true

./gost -L "socks5://${WG_IP}:${PORT}" >/tmp/gost.log 2>&1 &
sleep 2
if ! curl -s -x "socks5://${WG_IP}:${PORT}" --max-time 10 -o /dev/null "https://www.youtube.com" 2>/dev/null; then
  log "gost SOCKS not usable"; exit 1
fi

log "WARP SOCKS ready at socks5://${WG_IP}:${PORT}"
echo "socks5://${WG_IP}:${PORT}"
