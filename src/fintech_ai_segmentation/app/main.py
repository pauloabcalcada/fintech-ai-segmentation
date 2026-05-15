from __future__ import annotations

from contextlib import asynccontextmanager
from typing import AsyncIterator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from fintech_ai_segmentation.app.database import close_db, get_engine, init_db
from fintech_ai_segmentation.app.middleware import RequestLogMiddleware
from fintech_ai_segmentation.app.repositories.customer import AggregateCache
from fintech_ai_segmentation.app.routers import customers, dashboard, health
from fintech_ai_segmentation.app.settings import get_settings

_aggregate_cache: AggregateCache | None = None


def _configure_langsmith(settings) -> None:
    import os
    if settings.LANGCHAIN_API_KEY:
        os.environ.setdefault("LANGCHAIN_TRACING_V2", "true")
        os.environ.setdefault("LANGCHAIN_API_KEY", settings.LANGCHAIN_API_KEY)
        os.environ.setdefault("LANGCHAIN_PROJECT", settings.LANGCHAIN_PROJECT or "synaptiqpay-recommendations")


def get_aggregate_cache() -> AggregateCache | None:
    return _aggregate_cache


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    global _aggregate_cache
    await init_db()
    _aggregate_cache = await AggregateCache.load(get_engine())
    yield
    await close_db()


def create_app() -> FastAPI:
    settings = get_settings()
    _configure_langsmith(settings)
    application = FastAPI(version=settings.VERSION, lifespan=lifespan)
    application.add_middleware(
        CORSMiddleware,
        allow_origins=[settings.FRONTEND_ORIGIN],
        allow_methods=["*"],
        allow_headers=["*"],
    )
    application.add_middleware(RequestLogMiddleware)
    application.include_router(health.router)
    application.include_router(customers.router)
    application.include_router(dashboard.router)
    return application


app = create_app()
