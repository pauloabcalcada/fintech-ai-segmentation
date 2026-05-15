from __future__ import annotations

import time
from typing import Annotated

import structlog
from fastapi import Header, HTTPException
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

from fintech_ai_segmentation.app.settings import get_settings

logger = structlog.get_logger()


def require_demo_password(x_demo_password: Annotated[str | None, Header()] = None) -> None:
    settings = get_settings()
    if x_demo_password is None or x_demo_password != settings.DEMO_PASSWORD:
        raise HTTPException(status_code=401, detail="Invalid or missing demo password")


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
