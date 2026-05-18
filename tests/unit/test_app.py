from __future__ import annotations

import asyncio
import os

import pytest
from fastapi.testclient import TestClient

from fintech_ai_segmentation.app.main import app

client = TestClient(app)


def test_health_returns_ok() -> None:
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_request_log_emits_method_path_status_duration() -> None:
    from unittest.mock import patch

    import fintech_ai_segmentation.app.middleware as mw

    with patch.object(mw, "logger") as mock_logger:
        client.get("/health")

    mock_logger.info.assert_called_once()
    event, kwargs = mock_logger.info.call_args.args[0], mock_logger.info.call_args.kwargs
    assert event == "request"
    assert kwargs["method"] == "GET"
    assert kwargs["path"] == "/health"
    assert "status_code" in kwargs
    assert "duration_ms" in kwargs


def test_cors_allows_local_dev_origin() -> None:
    response = client.get("/health", headers={"Origin": "http://localhost:5173"})
    assert response.headers.get("access-control-allow-origin") == "http://localhost:5173"


# ---------------------------------------------------------------------------
# Docs visibility
# ---------------------------------------------------------------------------


def test_docs_disabled_in_production(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("ENVIRONMENT", "production")
    from fintech_ai_segmentation.app import main as main_module
    from fintech_ai_segmentation.app import settings as settings_module
    settings_module.get_settings.cache_clear()
    prod_app = main_module.create_app()
    from fastapi.testclient import TestClient as _TC
    with _TC(prod_app) as prod_client:
        assert prod_client.get("/docs").status_code == 404
        assert prod_client.get("/redoc").status_code == 404
    settings_module.get_settings.cache_clear()


def test_docs_enabled_in_development(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("ENVIRONMENT", "development")
    from fintech_ai_segmentation.app import main as main_module
    from fintech_ai_segmentation.app import settings as settings_module
    settings_module.get_settings.cache_clear()
    dev_app = main_module.create_app()
    from fastapi.testclient import TestClient as _TC
    with _TC(dev_app) as dev_client:
        assert dev_client.get("/docs").status_code == 200
    settings_module.get_settings.cache_clear()


def test_settings_reads_max_per_ip_daily_from_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("MAX_PER_IP_DAILY", "25")
    from fintech_ai_segmentation.app.settings import Settings
    settings = Settings()
    assert settings.MAX_PER_IP_DAILY == 25


@pytest.mark.skipif(
    not os.getenv("SUPABASE_DATABASE_URL"),
    reason="requires live Supabase connection",
)
def test_db_engine_connects_to_supabase() -> None:
    from sqlalchemy import text

    from fintech_ai_segmentation.app.database import close_db, get_engine, init_db

    async def _run() -> int:
        await init_db()
        async with get_engine().connect() as conn:
            result = await conn.execute(text("SELECT 1"))
            value = result.scalar()
        await close_db()
        return value  # type: ignore[return-value]

    assert asyncio.run(_run()) == 1
