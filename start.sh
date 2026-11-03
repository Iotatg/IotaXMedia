#!/bin/bash
# Authored By Iota Coders © 2025-2026
# SPDX-License-Identifier: MIT
# Starts IotaXMedia bot (local) and keeps it running 24/7.
# If the bot crashes/exits, it is automatically restarted after a short delay.
set -e
cd "$(dirname "$0")"

# --- Cloudflare WARP SOCKS (experimental YouTube unblock) ---
# If YTPROXY_URL is already provided (e.g. a residential proxy), use it directly.
# Otherwise attempt to spin up a local WARP SOCKS proxy and point YTPROXY_URL at it.
# If the WARP setup fails (e.g. sandbox lacks /dev/net/tun), the bot still runs
# without a proxy (no regression).
if [ -z "${YTPROXY_URL:-}" ] && [ "${WARP_SOCKS:-0}" = "1" ]; then
  WARP_URL=$(bash warp_socks.sh 2>/tmp/warp_setup.log) || WARP_URL=""
  if [ -n "$WARP_URL" ]; then
    export YTPROXY_URL="$WARP_URL"
    echo "[$(date)] WARP SOCKS active -> $YTPROXY_URL"
  else
    echo "[$(date)] WARP SOCKS setup failed; running without proxy (see /tmp/warp_setup.log)"
  fi
fi

while true; do
    echo "[$(date)] Starting IotaXMedia..."
    python3 wrapper.py
    echo "[$(date)] Bot exited with code $?. Restarting in 3s..."
    sleep 3
done
