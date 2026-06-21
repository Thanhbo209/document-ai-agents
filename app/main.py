from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.admin.routes import router as admin_router
from app.core.config import get_settings
from app.middleware.request_id import RequestIDMiddleware
from app.observability.logging import configure_logging
from app.routes.auth import router as auth_router
from app.routes.billing import router as billing_router
from app.routes.documents import router as documents_router
from app.routes.exports import router as exports_router
from app.routes.health import router as health_router
from app.routes.metrics import router as metrics_router
from app.routes.query import router as query_router
from app.routes.reviews import router as reviews_router
from app.routes.upload import router as upload_router
from app.routes.usage import router as usage_router

settings = get_settings()
configure_logging(settings)

app = FastAPI(
    title=settings.app_name,
    debug=settings.debug,
    version=settings.api_version,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(RequestIDMiddleware)

app.include_router(health_router)
app.include_router(metrics_router)
app.include_router(billing_router, prefix="/api/v1")
app.include_router(usage_router, prefix="/api/v1")
app.include_router(upload_router, prefix="/api/v1")
app.include_router(documents_router, prefix="/api/v1")
app.include_router(query_router, prefix="/api/v1")
app.include_router(reviews_router, prefix="/api/v1")
app.include_router(exports_router, prefix="/api/v1")
app.include_router(admin_router, prefix="/api/v1")
app.include_router(auth_router, prefix="/api/v1")
