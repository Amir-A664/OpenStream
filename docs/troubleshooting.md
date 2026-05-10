# Troubleshooting

Start with OpenStream's own status commands:

```sh
opst status
opst current
opst test
opst logs
```

## Check systemd units

```sh
systemctl status opst-setup.service --no-pager -l
systemctl status opst-openvpn.service --no-pager -l
systemctl status opst-socks.service --no-pager -l
systemctl status opst-localproxy.service --no-pager -l
```

Follow logs:

```sh
journalctl -u opst-openvpn.service -u opst-socks.service -u opst-localproxy.service -f
```

Scoped logs:

```sh
opst logs setup
opst logs openvpn
opst logs socks
opst logs localproxy
opst logs all
```

## Check the namespace

```sh
ip netns list
ip netns exec opstns ip addr
ip netns exec opstns ip route
ip netns exec opstns iptables -S
ip netns exec opstns iptables -t nat -S
```

## Manually test OpenVPN inside the namespace

```sh
ip netns exec opstns /usr/sbin/openvpn --config /etc/openvpn/opst/current.ovpn --verb 4
```

If OpenVPN fails here, the problem is likely the provider config, credentials, certificate material, DNS inside the namespace, or server reachability.

## Test the SOCKS endpoint

Local mode:

```sh
curl --proxy socks5h://127.0.0.1:<configured-port> https://ifconfig.me
```

Namespace target readiness:

```sh
socat -T1 - TCP4:10.200.1.2:<configured-port>,connect-timeout=1
```

## Common failures

### `No .ovpn files were found`

Put your OpenVPN provider config files here:

```text
/home/<username>/Desktop/opst/
```

Then run:

```sh
opst on
```

### OpenVPN asks for username/password repeatedly

Run:

```sh
opst profiles
```

Remove and re-add the profile if credentials were entered wrong:

```sh
opst remove
opst add
```

The credential file should be profile-specific:

```text
/etc/openvpn/opst/auth/<profile-id>.txt
```

### `compat-mode 2.4` error

OpenStream's patcher removes this directive from patched profiles because it can break with OpenVPN 2.6.x. If you still see it, check that OpenVPN is using:

```text
/etc/openvpn/opst/current.ovpn
```

and not your original unpatched file.

### `socat ... Connection refused`

This usually means the host-side forwarder started before `microsocks` was ready inside `opstns`. The localproxy script includes readiness gating, but logs may still show old attempts if services were restarted manually.

Restart cleanly:

```sh
opst restart
```

Then watch:

```sh
opst logs localproxy
```

### Port is already in use

Check listeners:

```sh
ss -ltnp | grep ':<configured-port>'
```

Choose a different port by editing `/etc/opst/config.toml` carefully, then reinstall generated helpers or rerun the installer. The cleaner path is to rerun `sudo ./install.sh` and choose a different port.
