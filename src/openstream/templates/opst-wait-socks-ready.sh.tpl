#!/bin/sh
set -eu

TARGET_IP="${NS_BIND_IP}"
PORT="${PROXY_PORT}"

i=0
while [ "$i" -lt 60 ]; do
  if /usr/bin/socat -T1 - TCP4:"$TARGET_IP":"$PORT",connect-timeout=1 </dev/null >/dev/null 2>&1; then
    exit 0
  fi
  i=$((i + 1))
  sleep 1
done

echo "SOCKS target $TARGET_IP:$PORT did not become ready" >&2
exit 1
