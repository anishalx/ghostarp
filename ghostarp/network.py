"""Low-level network helpers: scapy loading, gateway detection and host discovery."""
from __future__ import annotations

import ipaddress
import logging
from typing import List, Optional

from .utils import GhostARPError

log = logging.getLogger("ghostarp.network")


def get_scapy():
    """Return the scapy module, raising a clear GhostARPError if it is unavailable.

    scapy is imported lazily (rather than at module import time) so the package
    can be imported and tested without scapy installed.
    """
    try:
        import scapy.all as scapy
        return scapy
    except ImportError as exc:
        raise GhostARPError(
            "scapy is not installed. Install it with: pip install scapy"
        ) from exc


def get_default_gateway(interface: Optional[str] = None) -> Optional[str]:
    """Return the default gateway IP from the system routing table, or None."""
    scapy = get_scapy()
    try:
        return scapy.conf.route.route("0.0.0.0")[2]
    except Exception as exc:  # pragma: no cover - depends on platform/scapy
        log.debug("Gateway auto-detection failed: %s", exc)
        return None


def get_route_source(dst_ip: str, interface: Optional[str] = None) -> Optional[str]:
    """Return the local source IP that would be used to reach ``dst_ip``, or None."""
    scapy = get_scapy()
    try:
        return scapy.conf.route.route(dst_ip)[1]
    except Exception as exc:  # pragma: no cover - depends on platform/scapy
        log.debug("Route lookup for %s failed: %s", dst_ip, exc)
        return None


def _is_connected_route(gw) -> bool:
    """Return True if a route entry is directly connected (has no gateway).

    Older scapy versions store the gateway as the int ``0``; newer ones
    (e.g. 2.7) use the string ``"0.0.0.0"`` for connected routes.
    """
    if gw is None or gw == 0 or gw == "":
        return True
    try:
        return int(ipaddress.IPv4Address(str(gw))) == 0
    except ValueError:
        return False


def get_local_network(interface: Optional[str] = None) -> Optional[ipaddress.IPv4Network]:
    """Return the directly connected IPv4 subnet for the (default) interface, or None."""
    scapy = get_scapy()
    try:
        default_iface = scapy.conf.route.route("0.0.0.0")[0] if interface is None else interface
        for net, mask, gw, iface, out_ip, metric in scapy.conf.route.routes:
            if iface != default_iface or not _is_connected_route(gw):
                continue
            mask = int(mask)
            if mask == 0:
                continue
            # scapy stores the mask as an int bitmask; convert it to a prefix length
            prefix = bin(mask).count("1")
            network = ipaddress.IPv4Network((net, prefix), strict=False)
            if ipaddress.IPv4Address(out_ip) in network:
                return network
    except Exception as exc:  # pragma: no cover - depends on platform/scapy
        log.debug("Local subnet detection failed: %s", exc)
    return None


def scan_hosts(interface: Optional[str] = None, timeout: float = 1.0) -> List[str]:
    """ARP-scan the local subnet and return the IPs of live hosts (excluding our own)."""
    scapy = get_scapy()
    network = get_local_network(interface)
    if network is None:
        raise GhostARPError(
            "Could not determine the local subnet; pass -t/--target and -g/--gateway explicitly."
        )
    try:
        answered, _ = scapy.arping(str(network), timeout=timeout, verbose=False, iface=interface)
    except Exception as exc:
        raise GhostARPError(f"Host discovery failed: {exc}") from exc
    own_ip = get_route_source("0.0.0.0", interface)
    hosts = sorted({recv.psrc for _, recv in answered if recv.psrc != own_ip})
    return hosts
