# LAN mode

By default, OpenStream exposes SOCKS5 only on localhost:

```text
socks5h://127.0.0.1:<configured-port>
```

That is the safer mode. Only apps on the same machine can use the proxy.

## Start LAN mode

```sh
opst on --lan
```

or restart into LAN mode:

```sh
opst restart --lan
```

In LAN mode, the host-side `socat` listener binds to:

```text
0.0.0.0:<configured-port>
```

That means other devices on the same network may be able to use the proxy if they can reach the machine.

OpenStream prints a warning using the real configured port:

```text
WARNING: LAN mode exposes SOCKS5 on 0.0.0.0:<configured-port>
Only use this on trusted networks.
```

## Client configuration

On another device in the same LAN, configure SOCKS5 like this:

```text
host: <OpenStream-machine-LAN-IP>
port: <configured-port>
DNS:  use SOCKS remote DNS if the app supports it
```

For curl from another Linux machine:

```sh
curl --proxy socks5h://<OpenStream-machine-LAN-IP>:<configured-port> https://ifconfig.me
```

Use `socks5h`, not plain `socks5`, when you want DNS resolution to happen through the proxy.

## Security warning

LAN mode is not an authenticated proxy layer. Treat it like opening a local network service. Use it on your home/trusted LAN, not a dorm, cafe, airport, public Wi-Fi, or hostile network.

For the current build there is no custom bind-address argument and no SOCKS username/password on the exposed LAN listener. That is intentional for `v1.0.0`: simpler surface, fewer fake promises.
