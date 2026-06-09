from __future__ import annotations

import time

import structlog
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

logger = structlog.get_logger()


class RequestLogMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: object) -> Response:
        start = time.perf_counter()
        response: Response = await call_next(request)  # type: ignore[arg-type]
        duration_ms = round((time.perf_counter() - start) * 1000, 2)
        logger.info(
            "request",
            method=request.method,
            path=request.url.path,
            status_code=response.status_code,
            duration_ms=duration_ms,
        )
        return response


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Attach baseline security headers to every API response.

    The API returns JSON, so it does not need a full CSP, but ``nosniff``
    (blocks MIME sniffing), HSTS (enforces HTTPS), and a restrictive
    ``Referrer-Policy`` are cheap defense-in-depth. ``Cache-Control: no-store``
    keeps PII-bearing responses out of shared caches.
    """

    async def dispatch(self, request: Request, call_next: object) -> Response:
        response: Response = await call_next(request)  # type: ignore[arg-type]
        response.headers.setdefault("X-Content-Type-Options", "nosniff")
        response.headers.setdefault("Referrer-Policy", "no-referrer")
        response.headers.setdefault(
            "Strict-Transport-Security", "max-age=31536000; includeSubDomains"
        )
        response.headers.setdefault("Cache-Control", "no-store")
        return response
