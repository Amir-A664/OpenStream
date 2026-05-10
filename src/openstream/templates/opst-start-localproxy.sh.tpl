#!/bin/sh
set -eu

LISTEN_IP_FILE="${LISTEN_IP_PATH}"
DEFAULT_LISTEN_IP="${LOCAL_LISTEN_IP}"
LAN_LISTEN_IP="${LAN_LISTEN_IP}"
TARGET_IP="${NS_BIND_IP}"
PORT="${PROXY_PORT}"
WAIT_SCRIPT="${LIBEXEC_DIR}/opst-wait-socks-ready.sh"

if [ -r "$LISTEN_IP_FILE" ]; then
  LISTEN_IP="$(head -n 1 "$LISTEN_IP_FILE" | tr -d '[:space:]')"
else
  LISTEN_IP="$DEFAULT_LISTEN_IP"
fi

case "$LISTEN_IP" in
  "$DEFAULT_LISTEN_IP"|"$LAN_LISTEN_IP") ;;
  *)
    echo "Invalid listen IP in $LISTEN_IP_FILE: $LISTEN_IP" >&2
    exit 1
    ;;
esac

"$WAIT_SCRIPT"
exec /usr/bin/socat TCP4-LISTEN:"$PORT",bind="$LISTEN_IP",reuseaddr,fork TCP4:"$TARGET_IP":"$PORT"
