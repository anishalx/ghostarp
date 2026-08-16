# GhostARP

```text
                   ________.__                    __     _____ ____________________ 
                  /  _____/|  |__   ____  _______/  |_  /  _  \______   \______   \
                 /   \  ___|  |  \ /  _ \/  ___/\   __\/  /_\  \|       _/|     ___/
                 \    \_\  \   Y  (  <_> )___ \  |  | /    |    \    |   \|    |    
                  \______  /___|  /\____/____  > |__| \____|__  /____|_  /|____|    
                         \/     \/           \/               \/       \/                    
                                ---- Stealth ARP Spoofing Tool ----
```

## Overview

**GhostARP** is an ARP spoofing / Man-in-the-Middle (MitM) testing tool for authorized network
security assessments. By sending spoofed ARP replies, it reroutes traffic between a target and the
gateway through your machine so you can analyze it — and it always restores the real ARP tables
when the run stops.

GhostARP v2.0 is a full rewrite: a structured Python package with a real command-line interface,
strict input validation, automatic gateway detection and host discovery, robust error handling,
and a unit-tested engine that never leaves the network poisoned.

## Features

- **Real CLI** — `-t/--target`, `-g/--gateway`, `-i/--interface`, `--interval`, `--jitter`,
  `--timeout`, `--retries`, `-q/--quiet`, `-v/--verbose`, `--version` (`ghostarp -h`).
- **Auto-discovery** — gateway is detected from the routing table; if no target is given, the
  local subnet is ARP-scanned and live hosts are listed for selection (or auto-picked when there
  is exactly one).
- **Strict validation** — IPv4 addresses are checked with the stdlib `ipaddress` module; the tool
  refuses to spoof itself or to run with a target equal to the gateway.
- **Reliable ARP handling** — MAC resolution is cached per run and retried with backoff; a host
  that disappears mid-run is skipped gracefully instead of crashing.
- **Guaranteed restore** — ARP tables are restored on Ctrl+C *and* on any unexpected error via
  `try/finally`, so the network is left clean.
- **Lazy scapy import** — the package imports and tests cleanly without scapy; running without it
  gives a clear install hint.
- **Test suite** — pytest coverage of the engine, network helpers and CLI with the network layer
  fully mocked (no root, no packets, no scapy needed to run the tests).

## Requirements

- Python 3.9+
- [scapy](https://scapy.readthedocs.io/) >= 2.5 and `colorama` (see `requirements.txt`)
- Packet injection privileges: root/sudo on Linux and macOS; on Windows, install
  [Npcap](https://npcap.com/) and run from an elevated prompt.

## Installation

```bash
git clone https://github.com/anishalx/ghostarp.git
cd ghostarp
pip install -r requirements.txt
```

## Usage

```bash
python -m ghostarp -t 192.168.1.50 -g 192.168.1.1   # explicit target + gateway
# or
python main.py -t 192.168.1.50 -g 192.168.1.1
```

| Option | Description |
| --- | --- |
| `-t, --target IP` | Target IP address. If omitted, live hosts are auto-discovered and you select one. |
| `-g, --gateway IP` | Gateway IP address. If omitted, it is detected from the routing table. |
| `-i, --interface NAME` | Network interface (defaults to the system default route). |
| `--interval SECONDS` | Delay between spoof cycles (default `2.0`). |
| `--jitter SECONDS` | Add a random delay of `0..jitter` to each interval (default `0.0`). |
| `--timeout SECONDS` | Seconds to wait for ARP replies (default `1.0`). |
| `--retries N` | ARP resolution retries per address (default `3`). |
| `-c, --count N` | Stop automatically after N spoof cycles and restore ARP tables (default `0` = run until Ctrl+C). |
| `-q, --quiet` | Suppress the banner and disclaimer. |
| `-v, --verbose` | Debug-level logging, including details of every packet sent and MAC resolved. |
| `--version` | Print the version and exit. |

### Examples

```bash
# Gateway auto-detected, target given explicitly
python -m ghostarp -t 192.168.1.50

# Fully automatic: gateway detected, subnet scanned, target selected interactively
python -m ghostarp

# Specific interface, slower and less disruptive cadence
python -m ghostarp -t 192.168.1.50 -g 192.168.1.1 -i eth0 --interval 5 --jitter 2

# Run exactly 100 cycles, then restore ARP tables and exit
python -m ghostarp -t 192.168.1.50 -g 192.168.1.1 -c 100

# Debug mode: log every packet sent (spoofed and restore) to stderr
python -m ghostarp -t 192.168.1.50 -g 192.168.1.1 -v
```

The tool prints a running packet count and stops on Ctrl+C. Before exiting it re-resolves and
restores the real ARP entries for both the target and the gateway.

## Making the MITM actually work: IP forwarding

ARP spoofing only changes the data-link (MAC) mapping. For traffic to actually flow through
your machine — and be captured and analyzed — the OS must forward IP packets:

### Linux

```bash
sudo sysctl -w net.ipv4.ip_forward=1
# persist across reboots:
echo 'net.ipv4.ip_forward=1' | sudo tee /etc/sysctl.d/99-ghostarp.conf
```

Verify with `sysctl net.ipv4.ip_forward` (should print `1`).

### macOS

```bash
sudo sysctl -w net.inet.ip.forwarding=1
# persist across reboots: add `net.inet.ip.forwarding=1` to /etc/sysctl.conf
```

### Windows (PowerShell, elevated)

```powershell
Set-NetIPInterface -InterfaceAlias "Ethernet" -Forwarding Enabled
# alternative via registry (requires reboot):
#   reg add HKLM\SYSTEM\CurrentControlSet\Services\Tcpip\Parameters /v IPEnableRouter /t REG_DWORD /d 1 /f
```

> **Firewall note:** some host firewalls drop *forwarded* traffic even when forwarding is
> enabled (e.g. the Windows Defender Firewall or strict `iptables` FORWARD policies). If the
> target loses connectivity mid-test, allow forwarded traffic through the firewall for the
> test interface.

**Quick verification:** while a spoof run is active, run `arp -a` on the target machine — the
gateway's IP should resolve to *your* MAC address. `ping`/`traceroute` to the gateway should
still work, confirming traffic is being relayed through your machine.

## IPv6 support

ARP is an **IPv4-only** protocol. IPv6 neighbor discovery uses NDP (ICMPv6), which GhostARP
does **not** spoof — any IPv6 traffic between the target and gateway will bypass the test and
won't be captured. If the target or gateway has working IPv6 (global or link-local), traffic
may simply prefer the IPv6 path.

Options for an IPv4-only test:

- Run the assessment in an IPv4-only environment.
- Disable IPv6 on the test interfaces: on Windows uncheck *Internet Protocol Version 6 (TCP/IPv6)*
  in the adapter properties; on Linux run `sudo sysctl -w net.ipv6.conf.all.disable_ipv6=1`.

IPv6 NDP spoofing is out of scope for this tool; GhostARP itself works fine on machines that
have IPv6 enabled, it just cannot redirect that traffic.

## Development

```bash
pip install -r requirements-dev.txt
python -m pytest -v
```

The tests mock the entire network layer, so they run anywhere — no root privileges, no live
packets, and no scapy required. CI (`.github/workflows/ci.yml`) runs them on Python 3.9–3.13.

## Safety & Ethics

ARP spoofing is a network attack technique. **Only use GhostARP on networks you own or have
explicit written permission to test.** Unauthorized interception of traffic is illegal in most
jurisdictions. The tool prints a legal disclaimer at startup and is intended solely for
penetration testing, security research, and education.

## License

MIT — see [LICENSE](LICENSE).
