#!/bin/sh
set -eu

LISTEN_IP="${NS_BIND_IP}"
PORT="${PROXY_PORT}"
TUN_DEV="${TUN_DEV}"

i=0
VPNIP=""
while [ "$i" -lt 90 ]; do
  VPNIP="$(ip -4 -o addr show dev "$TUN_DEV" 2>/dev/null | awk '{split($4,a,"/"); print a[1]; exit}')"
  if [ -n "$VPNIP" ]; then
    break
  fi
  i=$((i + 1))
  sleep 1
done

[ -n "$VPNIP" ] || {
  echo "$TUN_DEV did not get an IPv4 address" >&2
  exit 1
}

exec /usr/bin/microsocks -q -i "$LISTEN_IP" -p "$PORT" -b "$VPNIP"
