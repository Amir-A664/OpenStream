# OpenStream architecture

OpenStream is a local proxy wrapper around OpenVPN. It does not try to replace OpenVPN, and it does not route the whole host through a VPN by default. Its job is narrower: run OpenVPN in an isolated Linux network namespace, start a SOCKS5 server inside that namespace, then expose that SOCKS5 endpoint on the host.

The public identity is deliberately consistent:

```text
project: OpenStream
cli:     opst
netns:   opstns
repo:    https://github.com/Amir-A664/OpenStream/
```

## Why a network namespace?

A normal OpenVPN client usually changes the host route table. That is fine when the entire machine should use the VPN, but annoying when only one app, browser profile, downloader, or LAN device should use it. OpenStream avoids that by moving OpenVPN into `opstns`. The host keeps its normal default route. Only traffic sent through the SOCKS5 proxy goes through the VPN.

## Runtime network model

OpenStream creates a veth pair:

```text
host namespace                  opstns namespace
--------------                  ----------------
veth-opst-host  <------------>  veth-opst-ns
10.200.1.1/30                   10.200.1.2/30
```

Inside `opstns`, OpenVPN creates the tunnel device:

```text
tun-opst
```

`microsocks` binds inside the namespace on:

```text
10.200.1.2:<configured-port>
```

On the host, `socat` listens on either:

```text
127.0.0.1:<configured-port>   # local mode
0.0.0.0:<configured-port>     # LAN mode
```

and forwards TCP connections to:

```text
10.200.1.2:<configured-port>
```

## Service chain

The four systemd units are intentionally small and layered:

```text
opst-setup.service       creates namespace, veth, routes, DNS, NAT cleanup hooks
opst-openvpn.service     runs OpenVPN inside opstns
opst-socks.service       waits for tun-opst and starts microsocks inside opstns
opst-localproxy.service  waits for microsocks and starts host-side socat listener
```

The local proxy service waits for the namespace SOCKS target before starting its long-running listener. That is there to prevent noisy early `socat ... Connection refused` loops.

## Filesystem layout

Runtime files are written here:

```text
/etc/opst/config.toml
/etc/opst/listen_ip
/etc/opst/profiles.json
/etc/openvpn/opst/current.ovpn
/etc/openvpn/opst/auth/<profile-id>.txt
/etc/netns/opstns/resolv.conf
/var/lib/opst/profiles/<profile-id>/
/usr/local/bin/opst
/usr/local/lib/opst/
/etc/systemd/system/opst-*.service
```

User-provided `.ovpn` files are not edited in place. They stay in the drop folder:

```text
/home/<username>/Desktop/opst/
```

OpenStream copies each profile into `/var/lib/opst/profiles/<profile-id>/`, patches the copy, and symlinks the selected patched profile to `/etc/openvpn/opst/current.ovpn`.
