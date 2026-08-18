# Security policy and operational notes

OpenStream handles VPN profiles and credentials. Treat the project as security-sensitive even though it is a local helper tool.

## Do not commit secrets

Never commit:

```text
real VPN usernames
real VPN passwords
real auth.txt files
real private keys
real client certificates if private
real provider configs if they contain private hostnames or embedded secrets
personal paths such as /home/<real-user>/...
```

Public examples must use placeholders such as:

```text
vpn.example.com
YOUR_USERNAME
YOUR_PASSWORD
REDACTED_CERTIFICATE
REDACTED_PRIVATE_KEY
```

## Credential storage

For username/password and hybrid profiles, OpenStream stores one credential file per profile:

```text
/etc/openvpn/opst/auth/<profile-id>.txt
```

The expected permissions are:

```text
owner: root:root
mode:  0600
```

The patched `.ovpn` points to that profile-specific file and adds:

```text
auth-nocache
```

Do not use one shared `auth.txt` for every server. Providers often give different credentials per region or server group, and shared auth files turn profile switching into a foot-gun.

## LAN mode exposure

`opst on --lan` exposes SOCKS5 on:

```text
0.0.0.0:<configured-port>
```

In `v1.0.0-alpha`, that exposed listener is not a multi-user authenticated proxy. Use LAN mode only on networks you trust.

## Namespace isolation is not a sandbox promise

The network namespace keeps VPN routes away from the host route table. That is useful isolation, but it is not a full security sandbox. Do not treat it as malware containment, process isolation, or a replacement for system hardening.

## Reporting vulnerabilities

Do not open a public issue with real secrets or exploit details. Follow `SECURITY.md` in the repository and provide a minimal reproduction using fake configs.

Good report material:

```text
OS and version
OpenVPN version
OpenStream version / commit
sanitized .ovpn profile
exact command used
relevant logs with secrets removed
```

Bad report material:

```text
real VPN credentials
live provider certificate/private key
unredacted provider hostname if it is private
personal home directory paths that reveal private information
```
