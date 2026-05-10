# Install OpenStream

OpenStream currently targets Debian and Ubuntu-style Linux systems with systemd, OpenVPN, iproute2, iptables, socat, microsocks, and curl.

## Install from a cloned repository

```sh
git clone https://github.com/Amir-A664/OpenStream.git
cd OpenStream
sudo ./install.sh
```

The installer must run as root because it writes systemd units, `/etc` config, `/usr/local` helpers, and network namespace support files.

## SOCKS5 port selection

During installation, OpenStream asks which SOCKS5 port to expose:

```text
Choose the SOCKS5 port OpenStream should expose on this machine.
Default: 2086
Port:
```

Press Enter to use `2086`. The selected port is stored in:

```text
/etc/opst/config.toml
```

The same port is then used by `microsocks`, `socat`, `opst test`, LAN warnings, and generated service scripts.

## Dependencies

Required runtime commands:

```text
openvpn     package: openvpn
ip          package: iproute2
iptables    package: iptables
socat       package: socat
microsocks  package: microsocks
curl        package: curl
systemctl   package: systemd
```

The installer checks them and shows a summary. It may offer to install only the missing packages using apt, but it does not silently run apt without asking.

Manual install example:

```sh
sudo apt update
sudo apt install openvpn iproute2 iptables socat microsocks curl
```

## Where to put `.ovpn` files

After installation, put provider `.ovpn` files here:

```text
/home/<username>/Desktop/opst/
```

Do not commit real `.ovpn` files to GitHub. They may contain private hostnames, embedded certificates, private keys, or auth paths.

## First run

```sh
opst on
```

OpenStream scans the drop folder, imports new profiles, detects the authentication method, asks for credentials if needed, patches the config, and starts the service chain.

Test the proxy:

```sh
opst test
```

The local endpoint is:

```text
socks5h://127.0.0.1:<configured-port>
```


## Change the SOCKS5 port after install

You do not need to uninstall and reinstall OpenStream just to change the SOCKS5 port. Run:

```sh
sudo opst changeport
```

or set the port directly:

```sh
sudo opst changeport 2099
```

OpenStream updates `/etc/opst/config.toml`, re-renders the helper scripts and systemd units, reloads systemd, and restarts the service chain if it was already running.

## LAN mode

```sh
opst on --lan
```

This exposes the SOCKS5 listener on all host interfaces. Use it only on trusted networks.

## Uninstall

```sh
sudo opst uninstall
```

or from the cloned repo:

```sh
sudo ./uninstall.sh
```
