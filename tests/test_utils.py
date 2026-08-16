"""Tests for ghostarp.utils."""
import pytest

from ghostarp.utils import is_valid_ipv4


@pytest.mark.parametrize(
    "ip",
    [
        "192.168.1.1",
        "0.0.0.0",
        "255.255.255.255",
        "10.0.0.1",
        "8.8.8.8",
        "172.16.0.254",
    ],
)
def test_valid_ipv4(ip):
    assert is_valid_ipv4(ip)


@pytest.mark.parametrize(
    "ip",
    [
        "999.999.999.999",  # octets out of range
        "256.1.1.1",
        "1.2.3",  # too few octets
        "1.2.3.4.5",  # too many octets
        "1.2.3.-1",
        "1.2.3.4 ",
        " 1.2.3.4",
        "abc",
        "",
        "2001:db8::1",  # IPv6
        "localhost",
        None,
        12345,
    ],
)
def test_invalid_ipv4(ip):
    assert not is_valid_ipv4(ip)
