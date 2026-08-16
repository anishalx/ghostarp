"""Tests for ghostarp.network helpers using a mocked scapy."""
import ipaddress
from types import SimpleNamespace

import pytest

from ghostarp import network
from ghostarp.network import get_default_gateway, get_local_network, scan_hosts
from ghostarp.utils import GhostARPError

NET = int(ipaddress.IPv4Address("192.168.1.0"))
MASK = int(ipaddress.IPv4Address("255.255.255.0"))
SELF_IP = "192.168.1.100"


class _Route:
    routes = []

    def route(self, dst, verbose=False):
        return ("eth0", SELF_IP, "192.168.1.1")


class _Recv:
    def __init__(self, psrc: str):
        self.psrc = psrc


def make_fake_scapy(routes=None, arping_answers=None):
    route = _Route()
    route.routes = routes if routes is not None else []
    fake = SimpleNamespace(
        conf=SimpleNamespace(route=route),
        arping_calls=[],
        arping_answers=arping_answers or [],
    )

    def arping(net, timeout=None, verbose=None, iface=None):
        fake.arping_calls.append(net)
        return fake.arping_answers, []

    fake.arping = arping
    return fake


def _connected_routes():
    return [(NET, MASK, 0, "eth0", int(ipaddress.IPv4Address(SELF_IP)), 1)]


def test_get_default_gateway(monkeypatch):
    fake = make_fake_scapy()
    monkeypatch.setattr(network, "get_scapy", lambda: fake)
    assert get_default_gateway() == "192.168.1.1"


def test_get_route_source(monkeypatch):
    fake = make_fake_scapy()
    monkeypatch.setattr(network, "get_scapy", lambda: fake)
    assert network.get_route_source("192.168.1.50") == SELF_IP


def test_get_local_network(monkeypatch):
    fake = make_fake_scapy(routes=_connected_routes())
    monkeypatch.setattr(network, "get_scapy", lambda: fake)
    assert str(get_local_network()) == "192.168.1.0/24"


def test_get_local_network_ignores_default_route(monkeypatch):
    routes = _connected_routes() + [(0, 0, 0, "eth0", 0, 1)]
    fake = make_fake_scapy(routes=routes)
    monkeypatch.setattr(network, "get_scapy", lambda: fake)
    assert str(get_local_network()) == "192.168.1.0/24"


def test_get_local_network_scapy_27_string_gateway(monkeypatch):
    """scapy 2.7+ stores the gateway as '0.0.0.0' and out-IP as a string."""
    routes = [
        (0, 0, "192.168.1.1", "eth0", SELF_IP, 45),  # default route (string gw)
        (NET, MASK, "0.0.0.0", "eth0", SELF_IP, 301),  # connected route (string gw)
    ]
    fake = make_fake_scapy(routes=routes)
    monkeypatch.setattr(network, "get_scapy", lambda: fake)
    assert str(get_local_network()) == "192.168.1.0/24"


def test_scan_hosts_excludes_self(monkeypatch):
    answers = [
        (None, _Recv(SELF_IP)),
        (None, _Recv("192.168.1.51")),
        (None, _Recv("192.168.1.50")),
    ]
    fake = make_fake_scapy(routes=_connected_routes(), arping_answers=answers)
    monkeypatch.setattr(network, "get_scapy", lambda: fake)
    assert scan_hosts(timeout=1.0) == ["192.168.1.50", "192.168.1.51"]
    assert fake.arping_calls == ["192.168.1.0/24"]


def test_scan_hosts_without_subnet_raises(monkeypatch):
    fake = make_fake_scapy(routes=[])  # no connected route
    monkeypatch.setattr(network, "get_scapy", lambda: fake)
    with pytest.raises(GhostARPError, match="subnet"):
        scan_hosts(timeout=1.0)


@pytest.mark.parametrize(
    "gw", [0, "0.0.0.0", None, ""],
)
def test_is_connected_route(gw):
    assert network._is_connected_route(gw)


def test_is_connected_route_rejects_real_gateway():
    assert not network._is_connected_route("192.168.1.1")


def test_missing_scapy_raises(monkeypatch):
    import sys

    monkeypatch.setitem(sys.modules, "scapy", None)
    with pytest.raises(GhostARPError, match="scapy is not installed"):
        get_default_gateway()
