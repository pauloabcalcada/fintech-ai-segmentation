from __future__ import annotations

from fastapi import APIRouter, Depends

from fintech_ai_segmentation.app.settings import Settings, get_settings

router = APIRouter()


@router.get("/health")
async def health(settings: Settings = Depends(get_settings)) -> dict:
    return {"status": "ok", "version": settings.VERSION}
