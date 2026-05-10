# Changelog

All notable changes to OpenStream will be documented here.

This project follows semantic versioning starting with the first public stable release.

## [1.0.0] - 2026-05-10

Initial public stable release.

Added:

- OpenStream / `opst` / `opstns` identity cleanup.
- Root `install.sh` bootstrapper.
- Root `uninstall.sh` wrapper.
- Python package under `src/openstream`.
- `opst` CLI command model.
- `opst --version` and version output in `opst status`.
- Installer success output with the current OpenStream version.
- User-selected SOCKS5 port, defaulting to `2086`.
- Runtime config at `/etc/opst/config.toml`, including the installed version.
- Profile drop folder at `/home/<username>/Desktop/opst/`.
- Profile registry at `/etc/opst/profiles.json`.
- Profile cache under `/var/lib/opst/profiles/`.
- Profile-specific credential files under `/etc/openvpn/opst/auth/`.
- Auth-method detection for username/password, certificate, hybrid, and static-key profiles.
- Conservative `.ovpn` patcher for OpenVPN 2.6.x compatibility.
- Removal of `compat-mode 2.4` during patching.
- `data-ciphers` and `data-ciphers-fallback` normalization.
- `tun-opst` tunnel device normalization.
- Auto-reconnect directives for patched OpenVPN profiles.
- External certificate/key file copy and rewrite support.
- systemd templates for setup, OpenVPN, SOCKS, and local proxy services.
- Namespace helper script template.
- SOCKS startup helper template.
- Local proxy helper template with readiness gating to reduce `socat Connection refused` noise.
- OpenVPN remote directive parsing for namespace firewall port/protocol allowance.
- LAN mode via `opst on --lan`.
- LAN exposure warning using the configured port.
- Developer helper scripts for local install, linting, and smoke testing.
- Persian README at `README-fa.md` with a link from the main README.
- Crypto donation placeholder sections in English and Persian READMEs.
- Examples, documentation, and pytest coverage for OpenVPN patching, profile registry, auth detection, dependency checks, CLI sudo re-entry, version output, and runtime template checks.

Changed:

- Replaced old prototype assumptions such as fixed server names and personal paths with a general profile registry.
- Changed CLI privilege escalation to re-enter through the installed `/usr/local/bin/opst` wrapper instead of trying to execute the Python module file directly.
- Tightened `.gitignore` so real `.ovpn` files are ignored by default while public examples and test fixtures remain trackable.
- Updated repository metadata from early development wording to `v1.0.0` release wording.

Security:

- No real VPN credentials, provider configs, private hostnames, or private paths are included.
- Donation addresses in the README files are explicit placeholders and must be replaced before accepting real donations.
