#!/bin/sh
set -eu

NS="${NS_NAME}"
HOST_IF="${HOST_IF}"
NS_IF="${NS_IF}"
HOST_IP="${HOST_IP_CIDR}"
NS_IP="${NS_IP_CIDR}"
NS_GW="${NS_HOST_IP}"
NS_BIND_IP="${NS_BIND_IP}"
TUN_DEV="${TUN_DEV}"
PROXY_PORT="${PROXY_PORT}"
CURRENT_CONF="${CURRENT_OVPN}"
STATE_DIR="${STATE_DIR}"

get_wan_if() {
  ip -4 route show default | awk '/default/ {print $5; exit}'
}

get_proto() {
  awk '
    $1=="proto" {print $2; exit}
    $1=="remote" && NF>=4 {print $4; exit}
  ' "$CURRENT_CONF" 2>/dev/null || true
}

get_port() {
  awk '
    $1=="port" {print $2; exit}
    $1=="remote" && NF>=3 {print $3; exit}
  ' "$CURRENT_CONF" 2>/dev/null || true
}

host_rule_add() {
  table="$1"; shift
  if ! iptables -w -t "$table" -C "$@" 2>/dev/null; then
    iptables -w -t "$table" -A "$@"
  fi
}

host_rule_del() {
  table="$1"; shift
  while iptables -w -t "$table" -C "$@" 2>/dev/null; do
    iptables -w -t "$table" -D "$@"
  done
}

ns_ipt() {
  ip netns exec "$NS" iptables -w "$@"
}

ns_rule_add() {
  if ! ns_ipt -C "$@" 2>/dev/null; then
    ns_ipt -A "$@"
  fi
}

ns_reset_firewall() {
  ns_ipt -F || true
  ns_ipt -t nat -F || true
  ns_ipt -X || true
  ns_ipt -P INPUT DROP
  ns_ipt -P FORWARD DROP
  ns_ipt -P OUTPUT DROP

  ns_rule_add INPUT -i lo -j ACCEPT
  ns_rule_add OUTPUT -o lo -j ACCEPT
  ns_rule_add INPUT -m conntrack --ctstate ESTABLISHED,RELATED -j ACCEPT
  ns_rule_add OUTPUT -m conntrack --ctstate ESTABLISHED,RELATED -j ACCEPT

  ns_rule_add INPUT -i "$NS_IF" -s "$NS_GW" -d "$NS_BIND_IP" -p tcp --dport "$PROXY_PORT" -j ACCEPT
  ns_rule_add INPUT -i "$NS_IF" -s "$NS_GW" -p icmp -j ACCEPT
  ns_rule_add OUTPUT -o "$NS_IF" -d "$NS_GW" -p icmp -j ACCEPT
  ns_rule_add OUTPUT -o "$NS_IF" -p udp --dport 53 -j ACCEPT
  ns_rule_add OUTPUT -o "$NS_IF" -p tcp --dport 53 -j ACCEPT

  proto="$(get_proto)"
  port="$(get_port)"
  [ -n "$port" ] || port="1194"
  case "$proto" in
    udp|udp4|udp6)
      ns_rule_add OUTPUT -o "$NS_IF" -p udp --dport "$port" -j ACCEPT
      ;;
    tcp|tcp4|tcp6|tcp-client)
      ns_rule_add OUTPUT -o "$NS_IF" -p tcp --dport "$port" -j ACCEPT
      ;;
    *)
      ns_rule_add OUTPUT -o "$NS_IF" -p udp --dport "$port" -j ACCEPT
      ns_rule_add OUTPUT -o "$NS_IF" -p tcp --dport "$port" -j ACCEPT
      ;;
  esac

  ns_rule_add INPUT -i "$TUN_DEV" -j ACCEPT
  ns_rule_add OUTPUT -o "$TUN_DEV" -j ACCEPT
}

up() {
  mkdir -p "$STATE_DIR"
  WAN_IF="$(get_wan_if)"
  [ -n "$WAN_IF" ] || { echo "Could not detect WAN interface" >&2; exit 1; }

  if [ ! -f "$STATE_DIR/ip_forward.before" ]; then
    cat /proc/sys/net/ipv4/ip_forward > "$STATE_DIR/ip_forward.before"
  fi

  ip netns list | grep -qw "$NS" || ip netns add "$NS"

  if ! ip link show "$HOST_IF" >/dev/null 2>&1; then
    ip link add "$HOST_IF" type veth peer name "$NS_IF"
  fi

  ip link set "$NS_IF" netns "$NS" 2>/dev/null || true
  ip addr replace "$HOST_IP" dev "$HOST_IF"
  ip link set "$HOST_IF" up

  ip -n "$NS" link set lo up
  ip -n "$NS" addr replace "$NS_IP" dev "$NS_IF"
  ip -n "$NS" link set "$NS_IF" up
  ip -n "$NS" route replace default via "$NS_GW"

  sysctl -w net.ipv4.ip_forward=1 >/dev/null

  host_rule_add nat POSTROUTING -s 10.200.1.0/30 -o "$WAN_IF" -j MASQUERADE
  host_rule_add filter FORWARD -i "$HOST_IF" -o "$WAN_IF" -j ACCEPT
  host_rule_add filter FORWARD -i "$WAN_IF" -o "$HOST_IF" -m conntrack --ctstate RELATED,ESTABLISHED -j ACCEPT

  ns_reset_firewall
}

down() {
  WAN_IF="$(get_wan_if || true)"
  if [ -n "$WAN_IF" ]; then
    host_rule_del nat POSTROUTING -s 10.200.1.0/30 -o "$WAN_IF" -j MASQUERADE
    host_rule_del filter FORWARD -i "$HOST_IF" -o "$WAN_IF" -j ACCEPT
    host_rule_del filter FORWARD -i "$WAN_IF" -o "$HOST_IF" -m conntrack --ctstate RELATED,ESTABLISHED -j ACCEPT
  fi

  if ip netns list | grep -qw "$NS"; then
    ip netns pids "$NS" | xargs -r kill >/dev/null 2>&1 || true
    ip netns del "$NS" || true
  fi

  if ip link show "$HOST_IF" >/dev/null 2>&1; then
    ip link del "$HOST_IF" || true
  fi

  if [ -f "$STATE_DIR/ip_forward.before" ]; then
    before="$(cat "$STATE_DIR/ip_forward.before")"
    case "$before" in
      0|1) sysctl -w net.ipv4.ip_forward="$before" >/dev/null || true ;;
    esac
    rm -f "$STATE_DIR/ip_forward.before"
  fi
}

case "${1:-}" in
  up) up ;;
  down) down ;;
  *) echo "Usage: $0 up|down" >&2; exit 2 ;;
esac
