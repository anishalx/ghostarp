"""Command-line interface for GhostARP."""
from __future__ import annotations

import argparse
import logging
import sys
from typing import Callable, List, Optional

from colorama import Fore, Style, init

from . import __version__
from .core import Spoofer
from .network import get_default_gateway, get_route_source, scan_hosts
from .utils import GhostARPError, is_valid_ipv4

log = logging.getLogger("ghostarp")

init()  # enable ANSI colors on Windows terminals

_BANNER_ART = r"""
                   ________.__                    __     _____ ____________________ 
                  /  _____/|  |__   ____  _______/  |_  /  _  \______   \______   \
                 /   \  ___|  |  \ /  _ \/  ___/\   __\/  /_\  \|       _/|     ___/
                 \    \_\  \   Y  (  <_> )___ \  |  | /    |    \    |   \|    |    
                  \______  /___|  /\____/____  > |__| \____|__  /____|_  /|____|    
                         \/     \/           \/               \/       \/                    
                                ---- Stealth ARP Spoofing Tool ----
"""

_BANNER_COLORS = [Fore.RED, Fore.BLUE, Fore.GREEN, Fore.YELLOW, Fore.RED, Fore.RED, Fore.CYAN]


def _colored_banner() -> str:
    lines = _BANNER_ART.strip("\n").splitlines()
    colored = []
    for i, line in enumerate(lines):
        color = _BANNER_COLORS[min(i, len(_BANNER_COLORS) - 1)]
        colored.append(f"{Style.BRIGHT}{color}{line}")
    return "\n".join(colored) + Style.RESET_ALL


BANNER = _colored_banner()

LEGAL_DISCLAIMER = (
    "\n[!] Legal disclaimer: Usage of GhostARP for attacking targets without prior mutual "
    "consent is illegal. It is the end user's responsibility to obey all applicable local, "
    "state, and federal laws. Developer assumes no liability and is not responsible for any "
    "misuse or damage caused by this program."
)


def print_disclaimer() -> None:
    print(f"{Style.BRIGHT}{Fore.WHITE}{LEGAL_DISCLAIMER}{Style.RESET_ALL}")


def setup_logging(verbose: bool) -> None:
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(level=level, format="%(levelname)s: %(message)s")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="ghostarp",
        description=(
            "GhostARP - ARP spoofing / MITM testing tool for authorized network security "
            "assessments. Reroutes traffic between a target and the gateway and restores "
            "ARP tables automatically on exit."
        ),
        epilog=(
            "Examples:\n"
            "  ghostarp -t 192.168.1.50 -g 192.168.1.1          # explicit target + gateway\n"
            "  ghostarp -t 192.168.1.50                           # gateway auto-detected\n"
            "  ghostarp                                          # gateway + target auto-discovered"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("-t", "--target", help="Target IP address (auto-discovered if omitted)")
    parser.add_argument("-g", "--gateway", help="Gateway IP address (auto-detected if omitted)")
    parser.add_argument(
        "-i", "--interface", help="Network interface to use (default: system default)"
    )
    parser.add_argument(
        "--interval", type=float, default=2.0, help="Seconds between spoof cycles (default: 2.0)"
    )
    parser.add_argument(
        "--jitter",
        type=float,
        default=0.0,
        help="Random extra delay of 0..jitter seconds added to each interval (default: 0.0)",
    )
    parser.add_argument(
        "--timeout", type=float, default=1.0, help="Seconds to wait for ARP replies (default: 1.0)"
    )
    parser.add_argument(
        "--retries", type=int, default=3, help="ARP resolution retries per address (default: 3)"
    )
    parser.add_argument(
        "-q", "--quiet", action="store_true", help="Suppress the banner and disclaimer"
    )
    parser.add_argument("-v", "--verbose", action="store_true", help="Verbose (debug) logging")
    parser.add_argument(
        "--version", action="version", version=f"%(prog)s {__version__}"
    )
    return parser


def _make_progress() -> Callable[[int], None]:
    def progress(count: int) -> None:
        sys.stdout.write(f"\r[+] Packets sent: {count}   ")
        sys.stdout.flush()

    return progress


def choose_target(interface: Optional[str], timeout: float) -> str:
    """Auto-discover a target from the local subnet, prompting if ambiguous."""
    hosts: List[str] = []
    try:
        hosts = scan_hosts(interface=interface, timeout=timeout)
    except GhostARPError as exc:
        log.info("Host discovery failed (%s); falling back to manual entry", exc)

    if hosts:
        print(f"[+] Discovered {len(hosts)} live host(s) on the local network:")
        for i, ip in enumerate(hosts, 1):
            print(f"    {i}. {ip}")
        if len(hosts) == 1:
            print(f"[+] Auto-selected {hosts[0]}")
            return hosts[0]
        choice = input("Select target by number, or press Enter to type an IP: ").strip()
        if choice.isdigit() and 1 <= int(choice) <= len(hosts):
            return hosts[int(choice) - 1]

    while True:
        ip = input("Enter Target IP: ").strip()
        if is_valid_ipv4(ip):
            return ip
        print(f"[!] Invalid IP address: {ip!r}. Please enter a valid IPv4 address.")


def main(argv: Optional[List[str]] = None) -> int:
    args = build_parser().parse_args(argv)
    setup_logging(args.verbose)
    if not args.quiet:
        print(BANNER)
        print_disclaimer()
        print()

    try:
        gateway = args.gateway
        if gateway is None:
            gateway = get_default_gateway(args.interface)
            if gateway:
                log.info("Auto-detected gateway: %s", gateway)
            else:
                raise GhostARPError(
                    "Could not auto-detect the gateway. Specify it with -g/--gateway."
                )
        if not is_valid_ipv4(gateway):
            raise GhostARPError(f"Invalid gateway IP address: {gateway!r}")

        target = args.target
        if target is None:
            target = choose_target(args.interface, args.timeout)
        if not is_valid_ipv4(target):
            raise GhostARPError(f"Invalid target IP address: {target!r}")

        own_ip = get_route_source(target, args.interface)
        if own_ip == target:
            raise GhostARPError(
                f"Target {target} appears to be this machine; refusing to spoof ourselves."
            )
        if own_ip == gateway:
            log.warning("Gateway %s is this machine's own IP; is the gateway correct?", gateway)

        spoofer = Spoofer(
            target_ip=target,
            gateway_ip=gateway,
            interface=args.interface,
            interval=args.interval,
            jitter=args.jitter,
            timeout=args.timeout,
            retries=args.retries,
        )
        log.info(
            "Starting ARP spoof: %s <-> %s (interface: %s)",
            target,
            gateway,
            args.interface or "default",
        )
        progress = None if args.quiet else _make_progress()
        total = spoofer.run(progress=progress)
        if progress:
            print()
        log.info("Stopped. Total packets sent: %d", total)
        return 0
    except GhostARPError as exc:
        print(f"{Style.BRIGHT}{Fore.RED}[!] {exc}{Style.RESET_ALL}", file=sys.stderr)
        return 1
    except KeyboardInterrupt:
        print("\n[!] Interrupted.")
        return 130


if __name__ == "__main__":
    raise SystemExit(main())
