"""Tests for ghostarp.core.Spoofer using a fully mocked scapy layer."""
import logging
import sys
from typing import Dict, List, Optional

import pytest

from ghostarp.core import RESTORE_COUNT, Spoofer
from ghostarp.utils import GhostARPError

TARGET = "192.168.1.50"
GATEWAY = "192.168.1.1"
TARGET_MAC = "aa:bb:cc:dd:ee:01"
GATEWAY_MAC = "aa:bb:cc:dd:ee:02"


class _Recv:
    def __init__(self, mac: str):
        self.hwsrc = mac


class _Sent:
    pass


class _Stack:
    """Result of ``Ether / ARP`` — exposes the ARP layer as ``.payload``."""

    def __init__(self, ether, payload):
        self.ether = ether
        self.payload = payload


class FakeScapy:
    """Minimal stand-in for scapy.all: records sends, answers ARP requests."""

    def __init__(self, answers: Optional[Dict[str, str]] = None):
        self.answers: Dict[str, str] = answers or {}
        self.no_reply_before: Dict[str, int] = {}
        self.sent: List[dict] = []
        self.srp_calls: List[dict] = []

    class ARP:
        def __init__(self, **kwargs):
            self.__dict__.update(kwargs)

    class Ether:
        def __init__(self, **kwargs):
            self.__dict__.update(kwargs)

        def __truediv__(self, other):
            return _Stack(self, other)

    def srp(self, pkt, timeout=None, verbose=None, iface=None):
        self.srp_calls.append(
            {"pkt": pkt, "timeout": timeout, "verbose": verbose, "iface": iface}
        )
        ip = pkt.payload.pdst
        if self.no_reply_before.get(ip, 0) > 0:
            self.no_reply_before[ip] -= 1
            return [], []
        mac = self.answers.get(ip)
        answered = [] if mac is None else [(_Sent(), _Recv(mac))]
        return answered, []

    def send(self, pkt, **kwargs):
        self.sent.append({"pkt": pkt, "kwargs": kwargs})


def make_spoofer(answers=None, **kwargs) -> tuple:
    fake = FakeScapy(answers)
    opts = dict(interval=0, jitter=0, timeout=0.1, retries=3, scapy=fake)
    opts.update(kwargs)
    spoofer = Spoofer(TARGET, GATEWAY, **opts)
    return spoofer, fake


@pytest.fixture(autouse=True)
def _no_sleep(monkeypatch):
    monkeypatch.setattr("ghostarp.core.time.sleep", lambda _s: None)


# --------------------------------------------------------------------------- #
# Construction / validation
# --------------------------------------------------------------------------- #
def test_invalid_target_ip():
    with pytest.raises(GhostARPError, match="target"):
        Spoofer("not-an-ip", GATEWAY)


def test_invalid_gateway_ip():
    with pytest.raises(GhostARPError, match="gateway"):
        Spoofer(TARGET, "999.1.1.1")


def test_target_equals_gateway():
    with pytest.raises(GhostARPError, match="different"):
        Spoofer("192.168.1.1", "192.168.1.1")


def test_jitter_clamped_to_interval():
    spoofer = Spoofer(TARGET, GATEWAY, interval=1.0, jitter=5.0)
    assert spoofer.jitter == 1.0
    assert spoofer.interval == 1.0


def test_negative_cycles_clamped_to_unlimited():
    spoofer = Spoofer(TARGET, GATEWAY, cycles=-5)
    assert spoofer.cycles == 0


# --------------------------------------------------------------------------- #
# MAC resolution
# --------------------------------------------------------------------------- #
def test_resolve_mac_caches_result():
    spoofer, fake = make_spoofer({TARGET: TARGET_MAC})
    assert spoofer.resolve_mac(TARGET) == TARGET_MAC
    assert spoofer.resolve_mac(TARGET) == TARGET_MAC
    assert len(fake.srp_calls) == 1  # second call served from cache


def test_resolve_mac_retries_then_gives_up():
    spoofer, fake = make_spoofer({}, retries=3)
    assert spoofer.resolve_mac(TARGET) is None
    assert len(fake.srp_calls) == 3


def test_resolve_mac_recovers_after_failures():
    spoofer, fake = make_spoofer({TARGET: TARGET_MAC})
    fake.no_reply_before[TARGET] = 2
    assert spoofer.resolve_mac(TARGET) == TARGET_MAC
    assert len(fake.srp_calls) == 3  # two misses, then a hit


# --------------------------------------------------------------------------- #
# Spoofing
# --------------------------------------------------------------------------- #
def test_spoof_sends_packets_in_both_directions():
    spoofer, fake = make_spoofer({TARGET: TARGET_MAC, GATEWAY: GATEWAY_MAC})
    assert spoofer.spoof() == 2
    assert len(fake.sent) == 2

    p1 = fake.sent[0]["pkt"]
    assert (p1.op, p1.pdst, p1.hwdst, p1.psrc) == (2, TARGET, TARGET_MAC, GATEWAY)
    p2 = fake.sent[1]["pkt"]
    assert (p2.op, p2.pdst, p2.hwdst, p2.psrc) == (2, GATEWAY, GATEWAY_MAC, TARGET)
    assert fake.sent[0]["kwargs"]["verbose"] is False


def test_spoof_skips_cycle_when_target_unresolvable():
    spoofer, fake = make_spoofer({GATEWAY: GATEWAY_MAC})
    assert spoofer.spoof() == 0
    assert fake.sent == []


def test_spoof_partial_when_gateway_unresolvable():
    spoofer, fake = make_spoofer({TARGET: TARGET_MAC})
    assert spoofer.spoof() == 1
    assert len(fake.sent) == 1
    assert fake.sent[0]["pkt"].pdst == TARGET


def test_spoof_logs_packet_details(caplog):
    spoofer, fake = make_spoofer({TARGET: TARGET_MAC, GATEWAY: GATEWAY_MAC})
    with caplog.at_level(logging.DEBUG, logger="ghostarp.core"):
        spoofer.spoof()
    messages = [r.message for r in caplog.records if r.name == "ghostarp.core"]
    assert any(
        "psrc=192.168.1.1" in m and "pdst=192.168.1.50" in m and "hwdst=aa:bb:cc:dd:ee:01" in m
        for m in messages
    )
    assert any(
        "psrc=192.168.1.50" in m and "pdst=192.168.1.1" in m and "hwdst=aa:bb:cc:dd:ee:02" in m
        for m in messages
    )


def test_restore_logs_packet_details(caplog):
    spoofer, fake = make_spoofer({TARGET: TARGET_MAC, GATEWAY: GATEWAY_MAC})
    with caplog.at_level(logging.DEBUG, logger="ghostarp.core"):
        spoofer.restore()
    messages = [r.message for r in caplog.records if r.name == "ghostarp.core"]
    assert any(
        "Sent restore ARP reply" in m
        and "count=4" in m
        and "hwsrc=aa:bb:cc:dd:ee:02" in m
        and "hwdst=aa:bb:cc:dd:ee:01" in m
        for m in messages
    )


def test_resolve_mac_logs_success(caplog):
    spoofer, fake = make_spoofer({TARGET: TARGET_MAC})
    with caplog.at_level(logging.DEBUG, logger="ghostarp.core"):
        spoofer.resolve_mac(TARGET)
    messages = [r.message for r in caplog.records if r.name == "ghostarp.core"]
    assert any(f"Resolved MAC {TARGET_MAC} for {TARGET}" in m for m in messages)


# --------------------------------------------------------------------------- #
# Restore
# --------------------------------------------------------------------------- #
def test_restore_sends_correct_packets():
    spoofer, fake = make_spoofer({TARGET: TARGET_MAC, GATEWAY: GATEWAY_MAC})
    assert spoofer.restore() == 2
    assert len(fake.sent) == 2
    for entry in fake.sent:
        assert entry["kwargs"]["count"] == RESTORE_COUNT

    r1 = fake.sent[0]["pkt"]
    assert (r1.pdst, r1.hwdst, r1.psrc, r1.hwsrc) == (
        TARGET, TARGET_MAC, GATEWAY, GATEWAY_MAC,
    )
    r2 = fake.sent[1]["pkt"]
    assert (r2.pdst, r2.hwdst, r2.psrc, r2.hwsrc) == (
        GATEWAY, GATEWAY_MAC, TARGET, TARGET_MAC,
    )


def test_restore_partial_when_macs_unresolvable():
    spoofer, fake = make_spoofer({})
    assert spoofer.restore() == 0
    assert fake.sent == []


def test_restore_falls_back_to_cache():
    spoofer, fake = make_spoofer({TARGET: TARGET_MAC, GATEWAY: GATEWAY_MAC})
    spoofer.resolve_mac(TARGET)
    spoofer.resolve_mac(GATEWAY)
    fake.answers.clear()  # fresh resolution now fails -> cache is used
    assert spoofer.restore() == 2


# --------------------------------------------------------------------------- #
# Run loop
# --------------------------------------------------------------------------- #
def test_run_restores_after_interrupt():
    spoofer, fake = make_spoofer({TARGET: TARGET_MAC, GATEWAY: GATEWAY_MAC})
    calls = {"n": 0}

    def fake_spoof():
        calls["n"] += 1
        if calls["n"] > 1:
            raise KeyboardInterrupt
        return 2

    spoofer.spoof = fake_spoof  # type: ignore[method-assign]
    assert spoofer.run() == 2
    restore_pkts = [e for e in fake.sent if e["kwargs"].get("count") == RESTORE_COUNT]
    assert len(restore_pkts) == 2  # both tables restored after Ctrl+C


def test_run_reports_progress():
    spoofer, fake = make_spoofer({TARGET: TARGET_MAC, GATEWAY: GATEWAY_MAC})
    calls = {"n": 0}
    seen = []

    def fake_spoof():
        calls["n"] += 1
        if calls["n"] > 1:
            raise KeyboardInterrupt
        return 2

    spoofer.spoof = fake_spoof  # type: ignore[method-assign]
    spoofer.run(progress=lambda packets, cycles: seen.append((packets, cycles)))
    assert seen == [(2, 1)]  # (packets, cycles)


def test_run_stops_after_cycle_limit():
    spoofer, fake = make_spoofer({TARGET: TARGET_MAC, GATEWAY: GATEWAY_MAC}, cycles=3)
    spoofer.spoof = lambda: 2  # type: ignore[method-assign]
    assert spoofer.run() == 6
    # ARP tables are still restored after hitting the limit
    restore_pkts = [e for e in fake.sent if e["kwargs"].get("count") == RESTORE_COUNT]
    assert len(restore_pkts) == 2


def test_run_progress_with_cycle_limit():
    spoofer, fake = make_spoofer({TARGET: TARGET_MAC, GATEWAY: GATEWAY_MAC}, cycles=2)
    spoofer.spoof = lambda: 2  # type: ignore[method-assign]
    seen = []
    spoofer.run(progress=lambda packets, cycles: seen.append((packets, cycles)))
    assert seen == [(2, 1), (4, 2)]


def test_missing_scapy_raises_helpful_error(monkeypatch):
    monkeypatch.setitem(sys.modules, "scapy", None)
    spoofer = Spoofer(TARGET, GATEWAY)
    with pytest.raises(GhostARPError, match="scapy is not installed"):
        spoofer.resolve_mac(TARGET)
