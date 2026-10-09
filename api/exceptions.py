"""
Standardized exception handling for anyplot API.

Provides consistent error responses and HTTP status codes.
"""

import json
import logging
from typing import Any

from fastapi import HTTPException, Request
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from api.security_headers import stamp as stamp_security_headers


logger = logging.getLogger(__name__)


# ===== Error Response Schemas =====


class ErrorDetail(BaseModel):
    """Standard error detail format."""

    error: str
    detail: str
    path: str | None = None


class ErrorResponse(BaseModel):
    """Standard error response format."""

    status: int
    message: str
    errors: list[ErrorDetail] | None = None


# ===== Custom Exceptions =====


class AnyplotException(Exception):
    """Base exception for anyplot API."""

    def __init__(self, message: str, status_code: int = 500):
        self.message = message
        self.status_code = status_code
        super().__init__(message)


class ResourceNotFoundError(AnyplotException):
    """Resource not found (404)."""

    def __init__(self, resource: str, identifier: str):
        message = f"{resource} '{identifier}' not found"
        super().__init__(message, status_code=404)
        self.resource = resource
        self.identifier = identifier


class DatabaseNotConfiguredError(AnyplotException):
    """Database not configured (503)."""

    def __init__(self):
        message = "Database not configured. Please set DATABASE_URL or INSTANCE_CONNECTION_NAME environment variable."
        super().__init__(message, status_code=503)


class ExternalServiceError(AnyplotException):
    """External service failure (502)."""

    def __init__(self, service: str, detail: str):
        message = f"External service '{service}' error: {detail}"
        super().__init__(message, status_code=502)
        self.service = service


class ValidationError(AnyplotException):
    """Validation error (400)."""

    def __init__(self, detail: str):
        super().__init__(f"Validation failed: {detail}", status_code=400)


class DatabaseQueryError(AnyplotException):
    """Database query failed (500).

    The raw error text (which may contain SQL fragments, table names, or DSN
    bits) is kept in ``detail`` for server-side logging only — the client-facing
    ``message`` never includes it (see anyplot_exception_handler).
    """

    def __init__(self, operation: str, detail: str):
        message = f"Database query failed during '{operation}'"
        super().__init__(message, status_code=500)
        self.operation = operation
        self.detail = detail


# ===== Exception Handlers =====


def _public_path(request: Request) -> str:
    """The path as the client knows it — never this API's internal routing.

    nginx serves crawlers by prepending /seo-proxy to the request URI, so an
    error on a proxied page echoed the internal prefix back to the crawler
    (`{"path": "/seo-proxy/{slug}"}` on any dead spec URL — live verification
    2026-08-19). Logs keep the full internal path; only the reflected JSON is
    translated.
    """
    path = request.url.path
    if path.startswith("/seo-proxy"):
        return path.removeprefix("/seo-proxy") or "/"
    return path


async def anyplot_exception_handler(request: Request, exc: AnyplotException) -> JSONResponse:
    """Handle AnyplotException and return a standardized JSON response.

    For DatabaseQueryError the raw driver/SQLAlchemy text is logged here and
    never reflected — ``exc.message`` is the generic client-safe string.
    """
    if isinstance(exc, DatabaseQueryError):
        logger.error("Database query failed during '%s' on %s: %s", exc.operation, request.url.path, exc.detail)
    return JSONResponse(
        status_code=exc.status_code,
        content={"status": exc.status_code, "message": exc.message, "path": _public_path(request)},
    )


async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
    """Handle FastAPI HTTPException with standardized format."""
    return JSONResponse(
        status_code=exc.status_code,
        content={"status": exc.status_code, "message": exc.detail, "path": _public_path(request)},
    )


class AsciiJSONResponse(JSONResponse):
    """JSONResponse that escapes every non-ASCII character as ``\\uXXXX``.

    Starlette renders with ``ensure_ascii=False`` and then ``.encode("utf-8")``,
    which raises on a lone surrogate (a JSON body of ``"\\ud800"`` parses to one).
    Escaping keeps the response encodable whatever the client sent, and the body
    stays valid JSON that decodes back to the same string.
    """

    def render(self, content: Any) -> bytes:
        return json.dumps(content, ensure_ascii=True, allow_nan=False, indent=None, separators=(",", ":")).encode(
            "utf-8"
        )


async def request_validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    """Answer a request that fails validation with FastAPI's usual 422 body.

    Same ``{"detail": [{loc, msg, type, input, ...}]}`` shape as FastAPI's default
    handler, but rendered ASCII-safe: that default echoes the offending ``input``,
    and a lone surrogate in it made the encode fail, turning a 422 into a 500.
    """
    return AsciiJSONResponse(status_code=422, content={"detail": jsonable_encoder(exc.errors())})


async def generic_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Handle unexpected exceptions with 500 status.

    Never reflects the raw exception text back to clients — `str(exc)` can leak
    DSN fragments, table names, file-path traceback fragments, and other internal
    state. The full traceback goes to the server log instead.

    Stamps the security headers itself. `ServerErrorMiddleware` wraps every user
    middleware, so this response is built OUTSIDE the http middleware stack and
    is the one exit `api/main.py`'s header middleware cannot reach (Copilot
    review). Same helper on both paths, so the two cannot drift.
    """
    logger.exception("Unhandled exception on %s", request.url.path)
    return stamp_security_headers(
        JSONResponse(
            status_code=500, content={"status": 500, "message": "Internal server error", "path": _public_path(request)}
        )
    )


# ===== Helper Functions =====


def raise_not_found(resource: str, identifier: str) -> None:
    """
    Raise a standardized 404 error.

    Args:
        resource: Resource type (e.g., "Spec", "Library")
        identifier: Resource identifier

    Raises:
        ResourceNotFoundError: Always raises
    """
    raise ResourceNotFoundError(resource, identifier)


def raise_database_not_configured() -> None:
    """
    Raise a standardized 503 error for unconfigured database.

    Raises:
        DatabaseNotConfiguredError: Always raises
    """
    raise DatabaseNotConfiguredError()


def raise_external_service_error(service: str, detail: str) -> None:
    """
    Raise a standardized 502 error for external service failures.

    Args:
        service: Service name (e.g., "GCS", "GitHub API")
        detail: Error details

    Raises:
        ExternalServiceError: Always raises
    """
    raise ExternalServiceError(service, detail)


def raise_validation_error(detail: str) -> None:
    """
    Raise a standardized 400 error for validation failures.

    Args:
        detail: Validation error details

    Raises:
        ValidationError: Always raises
    """
    raise ValidationError(detail)


def raise_database_query_error(operation: str, detail: str) -> None:
    """
    Raise a standardized 500 error for database query failures.

    Args:
        operation: The operation that failed (e.g., "fetch_specs", "filter_plots")
        detail: Error details (logged server-side only, never returned to clients)

    Raises:
        DatabaseQueryError: Always raises
    """
    raise DatabaseQueryError(operation, detail)
