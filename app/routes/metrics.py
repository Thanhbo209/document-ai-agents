from fastapi import APIRouter, HTTPException, status
from fastapi.responses import PlainTextResponse

from app.core.config import get_settings
from app.observability.metrics import render_prometheus_metrics

router = APIRouter(tags=["metrics"])


@router.get("/metrics", response_class=PlainTextResponse)
def metrics() -> PlainTextResponse:
    if not get_settings().metrics_enabled:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Metrics are disabled.",
        )

    return PlainTextResponse(
        render_prometheus_metrics(),
        media_type="text/plain",
    )
