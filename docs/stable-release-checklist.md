# Stable release checklist

This checklist gates the first stable OpenStream release, `v1.0.0`. The current published release is `v1.0.0-alpha`; do not create the stable tag or GitHub release until every required check below is complete and the evidence has been recorded in the release notes or linked test results.

## Release identity and documentation

- [ ] Change the package version in `pyproject.toml` from `1.0.0a0` to `1.0.0`.
- [ ] Change `VERSION` in `src/openstream/config.py` from `1.0.0-alpha` to `1.0.0`.
- [ ] Change the package classifier from Alpha to Production/Stable only after the operational checks pass.
- [ ] Update `CHANGELOG.md`, both README files, `SECURITY.md`, and version-specific documentation for the stable release.
- [ ] Point the remote-bootstrap URL in `install.sh` at `v1.0.0` and confirm the URL works after the tag is created.

## Automated checks

- [ ] Run `./scripts/lint.sh`.
- [ ] Run `./scripts/smoke-test.sh` with pytest installed so the full test suite runs.
- [ ] Confirm the GitHub Actions workflow passes on the exact release commit.
- [ ] Build the package and confirm its metadata reports version `1.0.0` and the expected Python requirement.

## Clean installation matrix

Run these checks in disposable, fully updated virtual machines. Record the distribution release, Python version, OpenVPN version, and systemd version used.

- [ ] Install successfully on a clean supported Debian system.
- [ ] Install successfully on a clean supported Ubuntu LTS system.
- [ ] Verify dependency detection and the interactive apt-install path.
- [ ] Verify installation with both the default SOCKS5 port and a custom port.
- [ ] Confirm `/etc/opst/config.toml`, installed helpers, and systemd units contain the selected port and stable version.

## Runtime and profile validation

- [ ] Start local mode and confirm only `127.0.0.1:<configured-port>` is listening.
- [ ] Confirm `opst test` and a manual `curl --proxy socks5h://...` request use the VPN route while the host default route remains unchanged.
- [ ] Start LAN mode on a trusted isolated network, confirm `0.0.0.0:<configured-port>` is listening, and confirm the warning shows the configured port.
- [ ] Verify username/password, certificate, hybrid, and static-key profile fixtures or sanitized test profiles.
- [ ] Verify profile switching, reconnect behavior, `opst changeport`, status output, and relevant logs.

## Secrets and security

- [ ] Inspect the release diff and packaged artifacts for real `.ovpn` files, credentials, auth files, private keys, private certificates, provider hostnames, and personal paths.
- [ ] Confirm credential files are stored under `/etc/openvpn/opst/auth/` with `root:root` ownership and `0600` permissions.
- [ ] Confirm LAN mode remains unauthenticated and is documented as trusted-network-only behavior.
- [ ] Review open security reports and release-blocking defects.

## Uninstall and release

- [ ] Uninstall from each clean-test system and confirm services, units, namespaces, installed files, and runtime state are removed.
- [ ] Confirm the original user profile drop folder is preserved.
- [ ] Reinstall after uninstall to catch leftover-state problems.
- [ ] Create the `v1.0.0` tag from the exact validated commit.
- [ ] Verify the tag archive and remote-bootstrap installer before publishing the GitHub release.
- [ ] Publish release notes that list tested environments, known limitations, security considerations, and any deferred work.
