from __future__ import annotations

from fastapi import APIRouter, Depends

from fintech_ai_segmentation.app.repositories.dashboard import (
    DashboardRepository,
    get_dashboard_repository,
)
from fintech_ai_segmentation.app.schemas.dashboard import (
    DashboardAggregatesResponse,
    DashboardSummaryResponse,
)

router = APIRouter()


@router.get("/dashboard/summary", response_model=DashboardSummaryResponse)
async def get_dashboard_summary(
    dashboard: DashboardRepository = Depends(get_dashboard_repository),
) -> DashboardSummaryResponse:
    return await dashboard.get_summary()


@router.get("/dashboard/aggregates", response_model=DashboardAggregatesResponse)
async def get_dashboard_aggregates(
    dashboard: DashboardRepository = Depends(get_dashboard_repository),
) -> DashboardAggregatesResponse:
    return await dashboard.get_aggregates()
