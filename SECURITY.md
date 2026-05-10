# Security Policy

OpenStream handles VPN configuration files and, for some profile types, VPN usernames and passwords. Treat the runtime files as sensitive.

## Supported versions

| Version | Status |
| --- | --- |
| `1.0.0` | Security fixes accepted |

## What not to publish

Never publish:

- real VPN usernames,
- real VPN passwords,
- real auth files,
- real client private keys,
- private client certificates,
- provider-specific private `.ovpn` files,
- private server hostnames,
- personal local paths.

The following runtime path is especially sensitive:

```text
/etc/openvpn/opst/auth/
```

Auth files are intended to be owned by `root:root` and chmodded to `0600`.

## LAN mode warning

`opst on --lan` exposes the SOCKS5 listener on `0.0.0.0:<configured-port>`. Use it only on trusted networks.

OpenStream does not add authentication to the SOCKS5 listener in this release. If a device on your LAN can reach the listener, it may be able to use your VPN route.

## Reporting a vulnerability

Open a private security advisory on GitHub if available, or contact the maintainer through the repository:

<https://github.com/Amir-A664/OpenStream/>

Do not paste real secrets into public issues. Redact aggressively.

## Scope

Useful reports include:

- credential leaks,
- unsafe file permissions,
- command injection paths,
- profile parsing bugs that corrupt private key blocks,
- firewall rules that expose more than intended,
- LAN mode behavior that contradicts the warning.

Reports about unsupported platforms such as Windows or macOS are out of scope for this release.
