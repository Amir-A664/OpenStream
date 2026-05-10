# 🔒 OpenStream (`opst`)

> OpenStream is a small Linux tool that runs OpenVPN inside an isolated network namespace and exposes the VPN connection as a SOCKS5 proxy.

The point is simple: your host keeps its normal internet route. Only applications configured to use the SOCKS5 endpoint go through the VPN.

🌍 **Language:** English | [برای خوندن راهنمای فارسی اینجارو کلیک کنید](README-fa.md)

---

## ✨ What it does

OpenStream creates a dedicated Linux network namespace named `opstns`, starts OpenVPN inside it, starts `microsocks` inside the same namespace, then forwards a local or LAN-facing TCP listener to that namespace SOCKS server using `socat`.

Default endpoint after install:

```text
socks5h://127.0.0.1:2086
```

The port is not fixed. The installer asks you which SOCKS5 port to use and saves it in `/etc/opst/config.toml`.

---

## 🚫 What it does not do

OpenStream is not a VPN provider, does not ship VPN credentials, does not hide all traffic automatically, and does not modify the default route of your host. Apps must explicitly use the SOCKS5 proxy.

It is currently aimed at Debian/Ubuntu-style Linux systems using `systemd`, `iproute2`, `iptables`, OpenVPN, `microsocks`, and `socat`.

---

## 📦 Install

Run the following commands in order: (Naturally, for the initial installation from GitHub and for installing the required packages, unrestricted internet access is needed the first time.)

```sh
git clone https://github.com/Amir-A664/OpenStream.git
cd OpenStream
sudo ./install.sh
```

The installer will:

1. ask for the SOCKS5 port;
2. check runtime dependencies;
3. if something is missing, offer to install the required packages using `apt` (naturally, if this project is going to be used on Linux distributions that do not use the `apt` package manager, the dependencies should be installed manually);
4. create the following directory for storing `.ovpn` files:

Required runtime commands:

```text
openvpn, ip, iptables, socat, microsocks, curl, systemctl
```

Typical packages:

```sh
sudo apt install openvpn iproute2 iptables socat microsocks curl systemd
```

---

## 📁 Add OpenVPN profiles

Put one or more `.ovpn` files here:

```text
/home/<username>/Desktop/opst/
```

Then run:

```sh
opst on
```

OpenStream scans that folder, copies profiles into `/var/lib/opst/profiles/`, detects the authentication method, asks for credentials only when needed, patches the `.ovpn` safely for OpenVPN 2.6.x compatibility, and lets you choose the active profile.

Supported profile types in v1.0.0:

```text
username/password
certificate-based
hybrid username/password + certificate
static key / tls-auth / tls-crypt
```

---

## 🖥️ Start local mode

```sh
opst on
```

This binds the host listener to:

```text
127.0.0.1:<configured-port>
```

Example:

```sh
curl --proxy socks5h://127.0.0.1:2086 https://ifconfig.me
```

Use the port you selected during install.

---

## 🌐 Start LAN mode

```sh
opst on --lan
```

LAN mode binds the host listener to:

```text
0.0.0.0:<configured-port>
```

OpenStream prints a warning like this:

```text
WARNING: LAN mode exposes SOCKS5 on 0.0.0.0:2086
Only use this on trusted networks.
```

> [!WARNING]
> Do not enable LAN mode on public networks, dormitories, cafés, airports, or any network you do not trust.

Now, by simply keeping OpenStream running on your laptop or desktop, you can create a SOCKS5 proxy inside Telegram on your phone using your computer’s IP address and your chosen port, then connect Telegram through it. (The same thing can also be done with apps like V2rayNG on Android (or other apps on IOS) if you want your entire phone to access the internet through the proxy.)

Do not enable LAN mode on public networks, dormitories, cafés, airports, or any network you do not trust. In practice, this mode exposes a gateway into your VPN profile and should not be left open carelessly.

---

## 🛠 Commands

```sh
opst on
opst on --lan
opst off
opst restart
opst restart --lan
opst status
opst current
opst use
opst profiles
opst add
opst remove
opst test
opst logs
opst logs openvpn
sudo opst uninstall
```

---

## ✅ Test

```sh
opst test
```

This runs:

```sh
curl --proxy socks5h://127.0.0.1:<configured-port> https://ifconfig.me
```

---

## 📜 Logs

```sh
opst logs
opst logs setup
opst logs openvpn
opst logs socks
opst logs localproxy
```

---

## 🧹 Uninstall

```sh
sudo opst uninstall
```

or from the repository:

```sh
sudo ./uninstall.sh
```

The uninstaller removes system files, systemd units, runtime state, cached profiles, and namespaces. It does not delete your original `.ovpn` drop folder by default.

---

## ❤️ Support / Donate

If OpenStream saves you time, crypto donations are welcome!

```text
Bitcoin (BTC): bc1ql05zalkxftmrxwp2d6y9u97e3ypg6n8yfzpp2g

Ethereum / ERC-20 / (Ethereum mainnet, Binance Smart Chain, Arbitrum, Optimism, Base, Polygon, and other ERC-20/L2 networks):
0x920986fee228a8d62b58a9a25fece7aafb469e70

Solana (SOL / SPL): D6sFh8xjgnfLe2p3w55m68ERwt8gaMYDcNZaqfhUrvQ8

Litecoin (LTC): ltc1qzl3lyaz83xnnurr2rwge5smgg8e3nma5fwk632

Zcash (ZEC): t1QX9A83h4GxnZsXbqWbx8SCbprkwductoA

Ton (TON): UQBoXYOLS8sn4YBO0ojc042uhGnHyyFuuwJPI7ArBZjOhoq9
```

---

## 🔐 Security notes

Never commit real `.ovpn` files if they include private keys, certificates, provider hostnames, usernames, or passwords. Do not commit `/etc/openvpn/opst/auth/*.txt` under any circumstances.

OpenStream writes profile-specific auth files to:

```text
/etc/openvpn/opst/auth/<profile-id>.txt
```

with `root:root` ownership and `0600` permissions.
