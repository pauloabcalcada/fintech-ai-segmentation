from __future__ import annotations

from contextlib import asynccontextmanager
from typing import AsyncIterator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from fintech_ai_segmentation.app.database import close_db, init_db
from fintech_ai_segmentation.app.middleware import RequestLogMiddleware
from fintech_ai_segmentation.app.routers import health
from fintech_ai_segmentation.app.settings import get_settings


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    await init_db()
    yield
    await close_db()


def create_app() -> FastAPI:
    settings = get_settings()
    application = FastAPI(version=settings.VERSION, lifespan=lifespan)
    application.add_middleware(
        CORSMiddleware,
        allow_origins=[settings.FRONTEND_ORIGIN],
        allow_methods=["*"],
        allow_headers=["*"],
    )
    application.add_middleware(RequestLogMiddleware)
    application.include_router(health.router)
    return application


app = create_app()
