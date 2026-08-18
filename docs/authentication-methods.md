# Authentication methods

OpenStream detects common OpenVPN authentication styles by reading directives outside inline blocks. If detection fails, it asks the user to choose a method.

## Username/password

A basic auth profile usually contains:

```text
auth-user-pass
```

or an old provider-specific path such as:

```text
auth-user-pass /some/private/path/auth.txt
```

OpenStream replaces that with a profile-specific file:

```text
auth-user-pass /etc/openvpn/opst/auth/<profile-id>.txt
auth-nocache
```

The auth file format is:

```text
username
password
```

Permissions are locked down:

```sh
chown root:root /etc/openvpn/opst/auth/<profile-id>.txt
chmod 600 /etc/openvpn/opst/auth/<profile-id>.txt
```

## Certificate-based auth

Certificate profiles usually contain one or more of:

```text
ca
cert
key
pkcs12
<ca>...</ca>
<cert>...</cert>
<key>...</key>
```

OpenStream must not blindly add `auth-user-pass` to certificate-only profiles. Some providers reject that, and some configs break if an auth file is forced in.

Inline blocks are preserved. Relative external references are copied into the profile cache where possible and rewritten to absolute paths.

## Hybrid auth

Hybrid profiles contain username/password plus certificate material. OpenStream preserves the cert/key directives and adds the profile-specific credential file:

```text
auth-user-pass /etc/openvpn/opst/auth/<profile-id>.txt
auth-nocache
```

## Static key / tls-auth / tls-crypt

Static-key style profiles may contain:

```text
tls-auth
tls-crypt
tls-crypt-v2
secret
key-direction
<tls-auth>...</tls-auth>
<tls-crypt>...</tls-crypt>
```

OpenStream preserves those directives. It does not ask for username/password unless the profile also explicitly needs `auth-user-pass` and is detected or selected as hybrid.

## Not supported in this build

These are future work and should not be promised for `v1.0.0-alpha`:

```text
PAM backend
LDAP backend
RADIUS backend
token / OTP / Google Authenticator style flows
```
