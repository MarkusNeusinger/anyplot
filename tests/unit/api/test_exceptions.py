"""
Tests for api/exceptions.py.

Tests custom exception classes, handlers, and helper functions.
"""

from unittest.mock import MagicMock

import pytest
from fastapi import Request
from fastapi.responses import JSONResponse

from api.exceptions import (
    AnyplotException,
    DatabaseNotConfiguredError,
    DatabaseQueryError,
    ExternalServiceError,
    ResourceNotFoundError,
    ValidationError,
    anyplot_exception_handler,
    generic_exception_handler,
    http_exception_handler,
    raise_database_not_configured,
    raise_database_query_error,
    raise_external_service_error,
    raise_not_found,
    raise_validation_error,
)


class TestAnyplotException:
    """Tests for AnyplotException base class."""

    def test_default_status_code(self) -> None:
        """Should have default status code 500."""
        exc = AnyplotException("Test error")
        assert exc.status_code == 500
        assert exc.message == "Test error"

    def test_custom_status_code(self) -> None:
        """Should accept custom status code."""
        exc = AnyplotException("Test error", status_code=418)
        assert exc.status_code == 418
        assert exc.message == "Test error"

    def test_str_representation(self) -> None:
        """Should return message as string representation."""
        exc = AnyplotException("Test error")
        assert str(exc) == "Test error"


class TestResourceNotFoundError:
    """Tests for ResourceNotFoundError."""

    def test_status_code(self) -> None:
        """Should have status code 404."""
        exc = ResourceNotFoundError("Spec", "scatter-basic")
        assert exc.status_code == 404

    def test_message_format(self) -> None:
        """Should format message with resource type and ID."""
        exc = ResourceNotFoundError("Spec", "scatter-basic")
        assert "Spec" in exc.message
        assert "scatter-basic" in exc.message
        assert "not found" in exc.message.lower()


class TestDatabaseNotConfiguredError:
    """Tests for DatabaseNotConfiguredError."""

    def test_status_code(self) -> None:
        """Should have status code 503."""
        exc = DatabaseNotConfiguredError()
        assert exc.status_code == 503

    def test_message_mentions_env_vars(self) -> None:
        """Should mention required environment variables."""
        exc = DatabaseNotConfiguredError()
        assert "DATABASE_URL" in exc.message
        assert "INSTANCE_CONNECTION_NAME" in exc.message


class TestExternalServiceError:
    """Tests for ExternalServiceError."""

    def test_status_code(self) -> None:
        """Should have status code 502."""
        exc = ExternalServiceError("GCS", "Connection timeout")
        assert exc.status_code == 502

    def test_message_format(self) -> None:
        """Should format message with service name and detail."""
        exc = ExternalServiceError("GCS", "Connection timeout")
        assert "GCS" in exc.message
        assert "Connection timeout" in exc.message


class TestValidationError:
    """Tests for ValidationError."""

    def test_status_code(self) -> None:
        """Should have status code 400."""
        exc = ValidationError("Invalid library ID")
        assert exc.status_code == 400

    def test_message(self) -> None:
        """Should format validation error message."""
        exc = ValidationError("Invalid library ID")
        assert "Validation failed" in exc.message
        assert "Invalid library ID" in exc.message


class TestDatabaseQueryError:
    """Tests for DatabaseQueryError."""

    def test_status_code(self) -> None:
        """Should have status code 500."""
        exc = DatabaseQueryError("fetch_specs", "Connection pool exhausted")
        assert exc.status_code == 500

    def test_message_format(self) -> None:
        """Should format message with operation and detail."""
        exc = DatabaseQueryError("fetch_specs", "Connection pool exhausted")
        assert "fetch_specs" in exc.message
        assert "Connection pool exhausted" in exc.message

    def test_operation_attribute(self) -> None:
        """Should store operation attribute."""
        exc = DatabaseQueryError("filter_plots", "Timeout")
        assert exc.operation == "filter_plots"


class TestExceptionHandlers:
    """Tests for exception handler functions."""

    @pytest.mark.asyncio
    async def test_anyplot_exception_handler(self) -> None:
        """Should handle AnyplotException and return proper JSON response."""
        request = MagicMock(spec=Request)
        request.url.path = "/test/path"
        exc = AnyplotException("Test error", status_code=418)

        response = await anyplot_exception_handler(request, exc)

        assert isinstance(response, JSONResponse)
        assert response.status_code == 418
        content = response.body.decode()
        assert "Test error" in content
        assert "/test/path" in content

    @pytest.mark.asyncio
    async def test_http_exception_handler(self) -> None:
        """Should handle HTTPException and return proper JSON response."""
        request = MagicMock(spec=Request)
        request.url.path = "/test/path"

        # Create mock HTTPException
        exc = MagicMock()
        exc.status_code = 404
        exc.detail = "Not found"

        response = await http_exception_handler(request, exc)

        assert isinstance(response, JSONResponse)
        assert response.status_code == 404
        content = response.body.decode()
        assert "Not found" in content
        assert "/test/path" in content

    @pytest.mark.asyncio
    async def test_generic_exception_handler(self) -> None:
        """Should handle generic Exception and return 500 response without leaking exc text."""
        request = MagicMock(spec=Request)
        request.url.path = "/test/path"
        exc = Exception("Unexpected error")

        response = await generic_exception_handler(request, exc)

        assert isinstance(response, JSONResponse)
        assert response.status_code == 500
        content = response.body.decode()
        # Static message only — raw exception text MUST NOT reach the client
        # (would otherwise leak DSN fragments, table names, traceback paths).
        assert "Internal server error" in content
        assert "/test/path" in content
        assert "Unexpected error" not in content


class TestHelperFunctions:
    """Tests for exception helper functions."""

    def test_raise_not_found(self) -> None:
        """Should raise ResourceNotFoundError with proper message."""
        with pytest.raises(ResourceNotFoundError) as exc_info:
            raise_not_found("Spec", "scatter-basic")

        assert exc_info.value.status_code == 404
        assert "Spec" in str(exc_info.value)
        assert "scatter-basic" in str(exc_info.value)

    def test_raise_database_not_configured(self) -> None:
        """Should raise DatabaseNotConfiguredError."""
        with pytest.raises(DatabaseNotConfiguredError) as exc_info:
            raise_database_not_configured()

        assert exc_info.value.status_code == 503

    def test_raise_external_service_error(self) -> None:
        """Should raise ExternalServiceError with proper message."""
        with pytest.raises(ExternalServiceError) as exc_info:
            raise_external_service_error("GCS", "Connection failed")

        assert exc_info.value.status_code == 502
        assert "GCS" in str(exc_info.value)
        assert "Connection failed" in str(exc_info.value)

    def test_raise_validation_error(self) -> None:
        """Should raise ValidationError with proper message."""
        with pytest.raises(ValidationError) as exc_info:
            raise_validation_error("Invalid input")

        assert exc_info.value.status_code == 400
        assert "Invalid input" in str(exc_info.value)

    def test_raise_database_query_error(self) -> None:
        """Should raise DatabaseQueryError with proper message."""
        with pytest.raises(DatabaseQueryError) as exc_info:
            raise_database_query_error("fetch_specs", "Connection failed")

        assert exc_info.value.status_code == 500
        assert "fetch_specs" in str(exc_info.value)
        assert "Connection failed" in str(exc_info.value)
