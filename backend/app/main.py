from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.exceptions import HTTPException, RequestValidationError

from app.api.routes.router import api_router
from app.config import settings
from app.core.auth_config import ensure_auth_secrets
from app.core.credential_config import ensure_credentials_encryption_key
from app.core.errors import (
    AppError,
    app_error_handler,
    http_exception_handler,
    validation_exception_handler,
)
from app.models.base import SessionLocal
from app.services.auth_service import seed_admin_user


@asynccontextmanager
async def lifespan(_app: FastAPI):
    ensure_auth_secrets()
    ensure_credentials_encryption_key()
    db = SessionLocal()
    try:
        seed_admin_user(db)
    finally:
        db.close()
    yield


def create_app() -> FastAPI:
    app = FastAPI(
        title=settings.app_name,
        version="1.0.0",
        docs_url="/docs",
        redoc_url="/redoc",
        lifespan=lifespan,
    )

    app.add_exception_handler(AppError, app_error_handler)
    app.add_exception_handler(HTTPException, http_exception_handler)
    app.add_exception_handler(RequestValidationError, validation_exception_handler)

    app.include_router(api_router, prefix=settings.api_v1_prefix)

    @app.get("/health")
    async def health_check() -> dict[str, str]:
        return {"status": "ok"}

    return app


app = create_app()
