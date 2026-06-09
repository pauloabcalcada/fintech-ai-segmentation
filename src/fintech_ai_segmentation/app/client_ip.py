from __future__ import annotations

import hashlib

from starlette.requests import Request


def hash_ip(ip: str, salt: str = "") -> str:
    """Hash a client IP so the raw address is never persisted.

    Rate limiting only needs equality comparison, so a stable salted SHA-256 is
    a drop-in replacement that removes the personal data at rest: the stored
    value can no longer be read back as an IP. The salt should be a secret —
    the IPv4 space is small enough to brute-force an unsalted hash.
    """
    return hashlib.sha256(f"{salt}:{ip}".encode()).hexdigest()


def get_client_ip(request: Request, trusted_proxy_hops: int = 1) -> str:
    """Resolve the real client IP for rate limiting.

    Behind a reverse proxy (Railway, nginx), ``request.client.host`` is the
    proxy's address — not the caller's. Using it directly collapses every user
    onto a single IP, which silently breaks per-IP rate limiting. The caller's
    address lives in the ``X-Forwarded-For`` chain instead.

    The chain reads left-to-right as ``client, proxy1, ..., proxyN``; each proxy
    appends the address that connected to it, so the rightmost entries are the
    ones added by infrastructure we trust. With ``trusted_proxy_hops`` proxies
    in front of the app, the caller's address is that many positions from the
    right. Selecting it from the right is spoof-resistant: a client-supplied
    ``X-Forwarded-For`` value lands to the left of whatever the trusted proxy
    appends, so it is never the one we pick.
    """
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        parts = [part.strip() for part in forwarded.split(",") if part.strip()]
        if parts:
            index = max(0, len(parts) - trusted_proxy_hops)
            return parts[index]
    if request.client:
        return request.client.host
    return "unknown"
