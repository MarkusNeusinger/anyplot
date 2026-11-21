"""
Custom SQLAlchemy types that work with both PostgreSQL and SQLite.

Provides ARRAY, JSONB, and UUID types that use PostgreSQL native types in production
but fall back to compatible types for SQLite (useful for testing).
"""

import json

from sqlalchemy import JSON, String, TypeDecorator
from sqlalchemy.dialects import postgresql


class StringArray(TypeDecorator):
    """
    Array of strings that works with both PostgreSQL and SQLite.

    - PostgreSQL: Uses native ARRAY(String)
    - SQLite: Stores as JSON text
    """

    impl = String
    cache_ok = True

    def load_dialect_impl(self, dialect):
        """Load the appropriate type based on the dialect."""
        if dialect.name == "postgresql":
            return dialect.type_descriptor(postgresql.ARRAY(String))
        else:
            # SQLite and others: use JSON text
            return dialect.type_descriptor(String)

    def process_bind_param(self, value: list[str] | None, dialect) -> str | list[str] | None:
        """Convert Python list to database format."""
        if value is None:
            return None

        if dialect.name == "postgresql":
            return value  # PostgreSQL handles lists natively
        else:
            # SQLite: serialize to JSON
            return json.dumps(value)

    def process_result_value(self, value: str | list[str] | None, dialect) -> list[str] | None:
        """Convert database value to Python list."""
        if value is None:
            return None

        if dialect.name == "postgresql":
            return value  # PostgreSQL returns lists natively
        else:
            # SQLite: deserialize from JSON
            if isinstance(value, str):
                return json.loads(value)
            return value  # Already a list (shouldn't happen)


class UniversalJSON(TypeDecorator):
    """
    JSON type that works with both PostgreSQL and SQLite.

    - PostgreSQL: Uses JSONB (binary JSON, faster)
    - SQLite: Uses JSON

    `UniversalJSON(none_as_null=True)` stores a Python None as SQL NULL; without it, as the JSON value
    `null`, which `IS NULL` does not match.
    """

    impl = JSON
    cache_ok = True

    def __init__(self, none_as_null: bool = False):
        # Stored on the type itself, not only on its impl: SQLAlchemy builds the statement cache key from the
        # `__init__` parameters held as attributes, so the two variants must not share one.
        self.none_as_null = none_as_null
        super().__init__(none_as_null=none_as_null)

    def load_dialect_impl(self, dialect):
        """Load the appropriate type based on the dialect, keeping `none_as_null`."""
        none_as_null = self.none_as_null
        if dialect.name == "postgresql":
            return dialect.type_descriptor(postgresql.JSONB(none_as_null=none_as_null))
        else:
            # SQLite and others: use JSON
            return dialect.type_descriptor(JSON(none_as_null=none_as_null))


class UniversalUUID(TypeDecorator):
    """
    UUID type that works with both PostgreSQL and SQLite.

    - PostgreSQL: Uses native UUID
    - SQLite: Stores as String
    """

    impl = String
    cache_ok = True

    def load_dialect_impl(self, dialect):
        """Load the appropriate type based on the dialect."""
        if dialect.name == "postgresql":
            return dialect.type_descriptor(postgresql.UUID(as_uuid=False))
        else:
            # SQLite: use String
            return dialect.type_descriptor(String(36))

    def process_bind_param(self, value: str | None, dialect) -> str | None:
        """Convert Python value to database format."""
        if value is None:
            return None
        return str(value)

    def process_result_value(self, value: str | None, dialect) -> str | None:
        """Convert database value to Python value."""
        if value is None:
            return None
        return str(value)
