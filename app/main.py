from fastapi import FastAPI

from app.core.config import get_settings
from app.routes.upload import router as upload_router

settings = get_settings()

app = FastAPI(
    title=settings.app_name,
    debug=settings.debug,
    version=settings.api_version,
)

app.include_router(upload_router, prefix="/api/v1")

@app.get("/health")
def health_check() -> dict[str, str]:
    return {
        "status": "ok",
        "app": settings.app_name,
        "environment": settings.environment,
        "version": settings.api_version,
    }
