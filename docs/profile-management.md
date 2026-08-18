# Profile management

OpenStream treats every `.ovpn` file as a profile. It is designed for normal provider configs, not just one hardcoded server name.

Supported profile shapes in `v1.0.0-alpha`:

```text
username/password only
certificate-based / TLS mutual auth
hybrid username/password + certificate
static key / tls-auth / tls-crypt style
```

## Drop folder

The installer creates a drop folder for the real desktop user:

```text
/home/<username>/Desktop/opst/
```

When the installer is run through `sudo`, it should not create `/root/Desktop/opst`. It resolves the real user and creates the drop folder under that user's home directory.

## Import behavior

When you run:

```sh
opst on
opst on --lan
opst add
```

OpenStream scans the drop folder for `*.ovpn` files. New or changed profiles are copied into:

```text
/var/lib/opst/profiles/<profile-id>/original.ovpn
```

The patched copy is written to:

```text
/var/lib/opst/profiles/<profile-id>/patched.ovpn
```

Profile metadata is written to:

```text
/var/lib/opst/profiles/<profile-id>/metadata.json
```

The global registry is:

```text
/etc/opst/profiles.json
```

## Profile IDs

Profile IDs are based on the filename plus a short SHA-256 digest:

```text
<sanitized-filename>-<short-sha256>
```

Example:

```text
NL-Amsterdam-a13f92c1
```

This avoids collisions when two providers use the same filename.

## Selecting a profile

List profiles:

```sh
opst profiles
```

Switch profile interactively:

```sh
opst use
```

Show the current profile:

```sh
opst current
```

The selected patched profile is symlinked here:

```text
/etc/openvpn/opst/current.ovpn
```

## Removing a profile

```sh
opst remove
```

This removes the cached OpenStream copy and its matching auth file. It does not delete the original `.ovpn` from the user's desktop drop folder. That is intentional; original provider configs are user data.
