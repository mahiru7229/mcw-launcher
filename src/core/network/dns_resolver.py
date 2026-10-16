"""DNS resolution utilities with IPv4 preference for dual-stack networks."""
from __future__ import annotations

import socket
from typing import Any

_ORIGINAL_GETADDRINFO = socket.getaddrinfo


def prefer_ipv4_dns() -> None:
    """Configure socket.getaddrinfo to sort IPv4 (AF_INET) addresses before IPv6 (AF_INET6).

    In dual-stack networks (especially in regions like Vietnam where ISP IPv6 routing
    to Microsoft/Azure Anycast prefixes often drops packets), OS-level RFC 6724 address
    selection places unroutable IPv6 addresses first. Because Python's socket.create_connection
    is sequential, each unroutable IPv6 address hangs for 21+ seconds before falling back,
    causing connect timeouts in HTTP clients.

    Sorting AF_INET first allows connections to succeed in under 1 second while preserving
    IPv6 addresses as secondary fallbacks if IPv4 is unavailable.
    """
    if getattr(socket.getaddrinfo, "_ipv4_preferred", False):
        return

    def ipv4_first_getaddrinfo(
        host: bytes | str | None,
        port: bytes | str | int | None,
        family: int = 0,
        type: int = 0,
        proto: int = 0,
        flags: int = 0,
    ) -> list[tuple[Any, ...]]:
        results = _ORIGINAL_GETADDRINFO(host, port, family, type, proto, flags)
        if family != 0 or len(results) <= 1:
            return results
        return sorted(results, key=lambda res: 0 if res[0] == socket.AF_INET else 1)

    ipv4_first_getaddrinfo._ipv4_preferred = True  # type: ignore[attr-defined]
    ipv4_first_getaddrinfo._orig_getaddrinfo = _ORIGINAL_GETADDRINFO  # type: ignore[attr-defined]
    socket.getaddrinfo = ipv4_first_getaddrinfo
