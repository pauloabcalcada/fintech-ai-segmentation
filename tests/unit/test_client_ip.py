from __future__ import annotations

from starlette.requests import Request

from fintech_ai_segmentation.app.client_ip import get_client_ip


def _request(
    headers: dict[str, str] | None = None, peer: str | None = "10.0.0.1"
) -> Request:
    raw_headers = [
        (k.lower().encode("latin1"), v.encode("latin1"))
        for k, v in (headers or {}).items()
    ]
    scope = {
        "type": "http",
        "headers": raw_headers,
        "client": (peer, 12345) if peer else None,
    }
    return Request(scope)


def test_falls_back_to_peer_when_no_forwarded_header() -> None:
    assert get_client_ip(_request(peer="203.0.113.9")) == "203.0.113.9"


def test_returns_unknown_when_no_peer_and_no_header() -> None:
    assert get_client_ip(_request(peer=None)) == "unknown"


def test_single_proxy_uses_forwarded_client() -> None:
    req = _request({"X-Forwarded-For": "198.51.100.7"}, peer="10.0.0.1")
    assert get_client_ip(req, trusted_proxy_hops=1) == "198.51.100.7"


def test_spoofed_leading_entry_is_ignored() -> None:
    # Attacker sends a fake X-Forwarded-For; the trusted proxy appends the real
    # client on the right. With one trusted hop we must pick the rightmost.
    req = _request({"X-Forwarded-For": "1.2.3.4, 198.51.100.7"}, peer="10.0.0.1")
    assert get_client_ip(req, trusted_proxy_hops=1) == "198.51.100.7"


def test_two_trusted_hops_picks_correct_entry() -> None:
    req = _request(
        {"X-Forwarded-For": "198.51.100.7, 70.0.0.1, 70.0.0.2"}, peer="10.0.0.1"
    )
    assert get_client_ip(req, trusted_proxy_hops=2) == "70.0.0.1"


def test_more_hops_than_entries_falls_back_to_leftmost() -> None:
    req = _request({"X-Forwarded-For": "198.51.100.7"}, peer="10.0.0.1")
    assert get_client_ip(req, trusted_proxy_hops=3) == "198.51.100.7"
