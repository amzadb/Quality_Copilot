from typing import Any

from fastapi import HTTPException, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel


class ErrorDetail(BaseModel):
    code: str
    message: str
    details: dict[str, Any] | None = None


class ErrorResponse(BaseModel):
    error: ErrorDetail


class AppError(HTTPException):
    def __init__(
        self,
        status_code: int,
        code: str,
        message: str,
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(status_code=status_code, detail=message)
        self.code = code
        self.details = details


def not_implemented_yet(feature: str, message: str | None = None) -> None:
    """Raise a 501 response for skeleton endpoints not yet implemented."""
    raise AppError(
        status_code=501,
        code="NOT_IMPLEMENTED",
        message=message or f"{feature} is not implemented yet.",
    )


def app_error_handler(_request: Request, exc: AppError) -> JSONResponse:
    return JSONResponse(
        status_code=exc.status_code,
        content=ErrorResponse(
            error=ErrorDetail(code=exc.code, message=str(exc.detail), details=exc.details)
        ).model_dump(),
    )


def http_exception_handler(_request: Request, exc: HTTPException) -> JSONResponse:
    code = "HTTP_ERROR"
    if isinstance(exc.detail, dict) and "code" in exc.detail:
        return JSONResponse(status_code=exc.status_code, content={"error": exc.detail})

    return JSONResponse(
        status_code=exc.status_code,
        content=ErrorResponse(
            error=ErrorDetail(code=code, message=str(exc.detail), details=None)
        ).model_dump(),
    )
