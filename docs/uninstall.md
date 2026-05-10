# Uninstall OpenStream

OpenStream can be removed through the CLI or the repository script.

Preferred command:

```sh
sudo opst uninstall
```

From a cloned repository:

```sh
sudo ./uninstall.sh
```

## What uninstall removes

The uninstall routine stops and disables OpenStream services:

```text
opst-localproxy.service
opst-socks.service
opst-openvpn.service
opst-setup.service
```

It removes systemd units:

```text
/etc/systemd/system/opst-setup.service
/etc/systemd/system/opst-openvpn.service
/etc/systemd/system/opst-socks.service
/etc/systemd/system/opst-localproxy.service
```

It removes OpenStream-installed files:

```text
/usr/local/bin/opst
/usr/local/lib/opst/
/etc/opst/
/etc/openvpn/opst/
/etc/netns/opstns/
/var/lib/opst/
/var/cache/opst/
/run/opst/
```

It also tries to clean up leftover runtime networking:

```sh
ip netns pids opstns | xargs -r kill || true
ip netns del opstns || true
ip link del veth-opst-host || true
```

## What uninstall does not remove

The user's original drop folder is not deleted by default:

```text
/home/<username>/Desktop/opst/
```

That folder may contain original provider configs. Deleting it automatically would be the wrong kind of clever.

Remove it manually only when you are sure you no longer need those files:

```sh
rm -rf ~/Desktop/opst
```

## After uninstall

Confirm services are gone:

```sh
systemctl status opst-setup.service --no-pager
systemctl status opst-openvpn.service --no-pager
systemctl status opst-socks.service --no-pager
systemctl status opst-localproxy.service --no-pager
```

Confirm the namespace is gone:

```sh
ip netns list | grep opstns || true
```
