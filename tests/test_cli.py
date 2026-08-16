"""Tests for ghostarp.cli."""
import sys

import pytest

from ghostarp import cli
from ghostarp.utils import GhostARPError


def test_parser_defaults():
    args = cli.build_parser().parse_args([])
    assert args.target is None
    assert args.gateway is None
    assert args.interface is None
    assert args.interval == 2.0
    assert args.jitter == 0.0
    assert args.timeout == 1.0
    assert args.retries == 3
    assert args.verbose is False
    assert args.quiet is False


def test_parser_flags():
    args = cli.build_parser().parse_args(
        [
            "-t", "192.168.1.50",
            "-g", "192.168.1.1",
            "-i", "eth0",
            "--interval", "0.5",
            "--jitter", "0.2",
            "-v",
            "-q",
        ]
    )
    assert args.target == "192.168.1.50"
    assert args.gateway == "192.168.1.1"
    assert args.interface == "eth0"
    assert args.interval == 0.5
    assert args.jitter == 0.2
    assert args.verbose is True
    assert args.quiet is True


def test_version_flag():
    with pytest.raises(SystemExit) as exc:
        cli.build_parser().parse_args(["--version"])
    assert exc.value.code == 0


def test_main_missing_scapy(monkeypatch, capsys):
    monkeypatch.setitem(sys.modules, "scapy", None)
    rc = cli.main(["-t", "192.168.1.50", "-g", "192.168.1.1", "-q"])
    assert rc == 1
    assert "scapy" in capsys.readouterr().err


def test_main_invalid_gateway(capsys):
    rc = cli.main(["-t", "192.168.1.50", "-g", "nope", "-q"])
    assert rc == 1
    assert "gateway" in capsys.readouterr().err.lower()


def test_main_invalid_target(capsys):
    rc = cli.main(["-t", "999.999.999.999", "-g", "192.168.1.1", "-q"])
    assert rc == 1
    assert "target" in capsys.readouterr().err.lower()


def test_main_refuses_self_as_target(monkeypatch, capsys):
    monkeypatch.setattr(cli, "get_route_source", lambda *a, **k: "192.168.1.50")
    rc = cli.main(["-t", "192.168.1.50", "-g", "192.168.1.1", "-q"])
    assert rc == 1
    assert "ourselves" in capsys.readouterr().err


def test_main_happy_path(monkeypatch, capsys):
    class FakeSpoofer:
        def __init__(self, **kwargs):
            self.kwargs = kwargs

        def run(self, progress=None):
            return 42

    monkeypatch.setattr(cli, "Spoofer", FakeSpoofer)
    monkeypatch.setattr(cli, "get_route_source", lambda *a, **k: "192.168.1.100")
    rc = cli.main(["-t", "192.168.1.50", "-g", "192.168.1.1", "-q"])
    assert rc == 0


def test_main_auto_detects_gateway(monkeypatch, capsys):
    class FakeSpoofer:
        def __init__(self, **kwargs):
            self.kwargs = kwargs

        def run(self, progress=None):
            return 42

    monkeypatch.setattr(cli, "get_default_gateway", lambda *a, **k: "192.168.1.1")
    monkeypatch.setattr(cli, "get_route_source", lambda *a, **k: "192.168.1.100")
    monkeypatch.setattr(cli, "Spoofer", FakeSpoofer)
    rc = cli.main(["-t", "192.168.1.50", "-q"])
    assert rc == 0


# --------------------------------------------------------------------------- #
# choose_target
# --------------------------------------------------------------------------- #
def _raise(exc):
    def _fn(*a, **k):
        raise exc

    return _fn


def test_choose_target_single_host(monkeypatch, capsys):
    monkeypatch.setattr(cli, "scan_hosts", lambda *a, **k: ["192.168.1.50"])
    assert cli.choose_target(None, 1.0) == "192.168.1.50"


def test_choose_target_selection(monkeypatch, capsys):
    monkeypatch.setattr(cli, "scan_hosts", lambda *a, **k: ["192.168.1.50", "192.168.1.51"])
    monkeypatch.setattr("builtins.input", lambda _prompt: "2")
    assert cli.choose_target(None, 1.0) == "192.168.1.51"


def test_choose_target_bad_selection_falls_back(monkeypatch, capsys):
    monkeypatch.setattr(cli, "scan_hosts", lambda *a, **k: ["192.168.1.50", "192.168.1.51"])
    inputs = iter(["9", "10.0.0.5"])
    monkeypatch.setattr("builtins.input", lambda _prompt: next(inputs))
    assert cli.choose_target(None, 1.0) == "10.0.0.5"


def test_choose_target_manual_entry(monkeypatch, capsys):
    monkeypatch.setattr(cli, "scan_hosts", lambda *a, **k: [])
    monkeypatch.setattr("builtins.input", lambda _prompt: "192.168.1.50")
    assert cli.choose_target(None, 1.0) == "192.168.1.50"


def test_choose_target_invalid_then_valid(monkeypatch, capsys):
    monkeypatch.setattr(cli, "scan_hosts", lambda *a, **k: [])
    inputs = iter(["999.999.999.999", "192.168.1.50"])
    monkeypatch.setattr("builtins.input", lambda _prompt: next(inputs))
    assert cli.choose_target(None, 1.0) == "192.168.1.50"


def test_choose_target_scan_failure_falls_back(monkeypatch, capsys):
    monkeypatch.setattr(cli, "scan_hosts", _raise(GhostARPError("nope")))
    monkeypatch.setattr("builtins.input", lambda _prompt: "192.168.1.50")
    assert cli.choose_target(None, 1.0) == "192.168.1.50"
