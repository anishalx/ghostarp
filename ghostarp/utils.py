"""Shared helpers for GhostARP: errors and input validation."""
from __future__ import annotations

import ipaddress
from typing import Any


class GhostARPError(Exception):
    """Raised for expected, user-facing failures (invalid input, missing scapy, network issues)."""


def is_valid_ipv4(ip: Any) -> bool:
    """Return True if ``ip`` is a well-formed IPv4 address such as ``192.168.1.1``.

    Uses the stdlib ``ipaddress`` module, so invalid octets (``999.1.1.1``),
    IPv6 addresses and arbitrary strings are all rejected. Non-string input
    (e.g. ints, which ipaddress would happily accept) is rejected as well.
    """
    if not isinstance(ip, str):
        return False
    try:
        ipaddress.IPv4Address(ip)
    except ValueError:
        return False
    return True
