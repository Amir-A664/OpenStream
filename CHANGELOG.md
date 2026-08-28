# Changelog

All notable changes to OpenStream will be documented here.

This project follows semantic versioning. The current public version is a prerelease; the first stable release has not been published yet.

## [Unreleased]

Added:

- Latch mode (`opst on --latch` / `opst restart --latch`) for server deployments.
  - When latch is active, OpenVPN is configured to exit on connection drop instead of internally soft-restarting. Systemd's `Restart=always` + `StartLimitIntervalSec=0` immediately relaunches it from scratch, indefinitely.
  - Implemented by omitting `persist-tun` and appending `remap-usr1 SIGTERM` in the patched `.ovpn` (written as a separate `patched-latch.ovpn` alongside the normal `patched.ovpn`).
  - Latch state is persisted as a flag file at `/etc/opst/latch`. `opst off` always clears it.
  - `opst restart` without `--latch` preserves the latch state that was active when services were started.
  - `opst use` (profile switch) picks up the active latch state automatically.
- `docs/latch-mode.md` explaining the latch feature and recommended server setup.

## [1.0.0-alpha] - 2026-05-10

Initial public alpha release.

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

- Improved the installer, uninstaller, status, profile, test, logs, and configuration command output with clearer terminal UX.
- Added `opst changeport` for changing the SOCKS5 port without uninstalling and reinstalling.
- Replaced old prototype assumptions such as fixed server names and personal paths with a general profile registry.
- Changed CLI privilege escalation to re-enter through the installed `/usr/local/bin/opst` wrapper instead of trying to execute the Python module file directly.
- Tightened `.gitignore` so real `.ovpn` files are ignored by default while public examples and test fixtures remain trackable.
- Updated repository metadata from early development wording to `v1.0.0-alpha` release wording.

Fixed during alpha development:

- Fixed installer completion-summary crash caused by using `CONFIG_PATH` without importing it in `installer.py`.
- Added regression coverage for the full installer success summary so the completion screen is tested.
- Quieted harmless uninstall cleanup noise when `opstns` or `veth-opst-host` does not exist.

Security:

- No real VPN credentials, provider configs, private hostnames, or private paths are included.
- Donation addresses in the README files are explicit placeholders and must be replaced before accepting real donations.
