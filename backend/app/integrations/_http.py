"""Shared HTTP helpers for external integrations."""

from typing import Any

import httpx

from app.core.errors import AppError
from app.schemas.common import ConnectionTestFailure, ConnectionTestResponse, ConnectionTestSuccess, ErrorDetail


def normalize_base_url(base_url: str, *, default_scheme: str = "https") -> str:
    cleaned = base_url.strip().rstrip("/")
    if not cleaned.startswith(("http://", "https://")):
        cleaned = f"{default_scheme}://{cleaned}"
    return cleaned


def map_http_error(
    exc: httpx.HTTPError,
    *,
    code: str,
    message: str,
) -> AppError:
    return AppError(status_code=502, code=code, message=message, details={"reason": str(exc)})


async def request_json(
    method: str,
    url: str,
    *,
    headers: dict[str, str] | None = None,
    auth: httpx.Auth | tuple[str, str] | None = None,
    params: dict[str, Any] | None = None,
    json: dict[str, Any] | None = None,
    data: Any | None = None,
    files: Any | None = None,
    timeout: float = 30.0,
) -> Any:
    async with httpx.AsyncClient(timeout=timeout) as client:
        response = await client.request(
            method,
            url,
            headers=headers,
            auth=auth,
            params=params,
            json=json,
            data=data,
            files=files,
        )

    if response.status_code in (401, 403):
        raise AppError(
            status_code=401,
            code="AUTH_FAILED",
            message="Authentication failed for the external API.",
            details={"status_code": response.status_code},
        )
    if response.status_code == 404:
        raise AppError(
            status_code=404,
            code="NOT_FOUND",
            message="The requested external resource was not found.",
            details={"status_code": response.status_code},
        )
    if response.status_code >= 400:
        raise AppError(
            status_code=502,
            code="EXTERNAL_API_ERROR",
            message=f"External API returned HTTP {response.status_code}.",
            details={"body": response.text[:500]},
        )

    if response.status_code == 204 or not response.content:
        return None
    return response.json()


def connection_ok() -> ConnectionTestResponse:
    return ConnectionTestSuccess(ok=True)


def connection_failed(code: str, message: str) -> ConnectionTestResponse:
    return ConnectionTestFailure(ok=False, error=ErrorDetail(code=code, message=message))
