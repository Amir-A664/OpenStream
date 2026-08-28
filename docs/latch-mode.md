# Latch mode

Latch mode is designed for server deployments where OpenStream must stay connected to the VPN indefinitely — even if the connection drops suddenly. When latch is active, the OpenVPN process is configured to **exit** on any connection failure instead of internally soft-restarting, so the systemd unit can immediately relaunch it from scratch.

## Why latch?

By default, OpenVPN tries to reconnect internally on a drop (via `SIGUSR1`). This keeps the process alive but can leave the `tun-opst` device in a hung or partitioned state. On a server — where the SOCKS5 proxy must be reliably available — a full process restart is safer: it tears everything down and brings it back up clean.

Systemd's existing `Restart=always` + `RestartSec=5` + `StartLimitIntervalSec=0` on `opst-openvpn.service` means the restart loop runs indefinitely with no cap.

## Start with latch

```sh
opst on --latch
```

Latch can be combined with LAN mode:

```sh
opst on --lan --latch
```

## Restart with latch

```sh
opst restart --latch
```

If latch was already active when services were started, a bare `opst restart` (without `--latch`) preserves the active latch state automatically.

## What latch changes in the OpenVPN config

When latch is enabled, `opst` produces a separate patched `.ovpn` for the active profile with two adjustments applied on top of the normal patch:

| Directive | Normal mode | Latch mode |
|---|---|---|
| `persist-tun` | Added if missing | Removed/omitted |
| `remap-usr1` | Not present | `remap-usr1 SIGTERM` added |

- **`persist-tun` removed** — without this, when the VPN tunnel drops, OpenVPN tears down `tun-opst` and exits rather than trying to reuse the stale device.
- **`remap-usr1 SIGTERM`** — `ping-restart` and other internal reconnect triggers send `SIGUSR1` to the OpenVPN process. Remapping that signal to `SIGTERM` causes the process to terminate, passing control to systemd for a clean restart.

The normal `patched.ovpn` (used for non-latch mode) is unchanged. The latch-specific config is written alongside it as `patched-latch.ovpn`.

## Stop and clear latch

```sh
opst off
```

`opst off` stops all services **and** clears the latch flag. The next `opst on` (without `--latch`) will run in normal mode.

## Latch state file

The latch flag is persisted as a file:

```text
/etc/opst/latch
```

Its presence means latch is active; its absence means it is not. You can inspect it directly:

```sh
ls /etc/opst/latch    # present = latch active
```

## Profile switches in latch mode

If latch is active and you run `opst use` to switch to a different profile, the new profile is automatically patched with latch directives too.

## Recommended server setup

```sh
# On first start
opst on --lan --latch

# After a reboot (systemd auto-starts services if enabled; if manually managed)
opst on --latch
```

Enable the services to auto-start on boot:

```sh
sudo systemctl enable opst-setup.service opst-openvpn.service opst-socks.service opst-localproxy.service
```

With latch active and systemd auto-start enabled, the proxy restarts automatically after both process crashes and host reboots.
