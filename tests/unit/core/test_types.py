"""Tests for core.database.types module.

Tests custom SQLAlchemy types that work with both PostgreSQL and SQLite.
"""

from core.database.types import StringArray, UniversalJSON, UniversalUUID


class MockDialect:
    """Mock SQLAlchemy dialect for testing."""

    def __init__(self, name: str):
        self.name = name

    def type_descriptor(self, type_obj):
        """Return the type descriptor."""
        return type_obj


class TestStringArray:
    """Tests for StringArray type."""

    def test_load_dialect_impl_sqlite(self):
        """Should use String for SQLite."""
        string_array = StringArray()
        dialect = MockDialect("sqlite")
        result = string_array.load_dialect_impl(dialect)
        # Result should be a String type descriptor
        assert result is not None

    def test_load_dialect_impl_postgresql(self):
        """Should use ARRAY(String) for PostgreSQL."""
        string_array = StringArray()
        dialect = MockDialect("postgresql")
        result = string_array.load_dialect_impl(dialect)
        # Result should be an ARRAY type descriptor
        assert result is not None

    def test_process_bind_param_sqlite_none(self):
        """Should return None for None value."""
        string_array = StringArray()
        dialect = MockDialect("sqlite")
        result = string_array.process_bind_param(None, dialect)
        assert result is None

    def test_process_bind_param_sqlite_list(self):
        """Should serialize list to JSON for SQLite."""
        string_array = StringArray()
        dialect = MockDialect("sqlite")
        result = string_array.process_bind_param(["a", "b", "c"], dialect)
        assert result == '["a", "b", "c"]'

    def test_process_bind_param_postgresql_none(self):
        """Should return None for None value in PostgreSQL."""
        string_array = StringArray()
        dialect = MockDialect("postgresql")
        result = string_array.process_bind_param(None, dialect)
        assert result is None

    def test_process_bind_param_postgresql_list(self):
        """Should return list as-is for PostgreSQL."""
        string_array = StringArray()
        dialect = MockDialect("postgresql")
        result = string_array.process_bind_param(["a", "b", "c"], dialect)
        assert result == ["a", "b", "c"]

    def test_process_result_value_sqlite_none(self):
        """Should return None for None value."""
        string_array = StringArray()
        dialect = MockDialect("sqlite")
        result = string_array.process_result_value(None, dialect)
        assert result is None

    def test_process_result_value_sqlite_json(self):
        """Should deserialize JSON string for SQLite."""
        string_array = StringArray()
        dialect = MockDialect("sqlite")
        result = string_array.process_result_value('["x", "y", "z"]', dialect)
        assert result == ["x", "y", "z"]

    def test_process_result_value_sqlite_already_list(self):
        """Should handle already-a-list case (edge case)."""
        string_array = StringArray()
        dialect = MockDialect("sqlite")
        result = string_array.process_result_value(["x", "y", "z"], dialect)
        assert result == ["x", "y", "z"]

    def test_process_result_value_postgresql_none(self):
        """Should return None for None value in PostgreSQL."""
        string_array = StringArray()
        dialect = MockDialect("postgresql")
        result = string_array.process_result_value(None, dialect)
        assert result is None

    def test_process_result_value_postgresql_list(self):
        """Should return list as-is for PostgreSQL."""
        string_array = StringArray()
        dialect = MockDialect("postgresql")
        result = string_array.process_result_value(["a", "b"], dialect)
        assert result == ["a", "b"]

    def test_cache_ok(self):
        """Should have cache_ok = True."""
        assert StringArray.cache_ok is True


class TestUniversalJSON:
    """Tests for UniversalJSON type."""

    def test_load_dialect_impl_sqlite(self):
        """Should use JSON for SQLite."""
        universal_json = UniversalJSON()
        dialect = MockDialect("sqlite")
        result = universal_json.load_dialect_impl(dialect)
        assert result is not None

    def test_load_dialect_impl_postgresql(self):
        """Should use JSONB for PostgreSQL."""
        universal_json = UniversalJSON()
        dialect = MockDialect("postgresql")
        result = universal_json.load_dialect_impl(dialect)
        assert result is not None

    def test_cache_ok(self):
        """Should have cache_ok = True."""
        assert UniversalJSON.cache_ok is True

    def test_none_as_null_reaches_both_dialects(self):
        """Without the flag the dialect type writes a Python None as the JSON value null, which IS NULL misses."""
        from sqlalchemy.dialects.postgresql import JSONB

        for name in ("postgresql", "sqlite"):
            assert UniversalJSON(none_as_null=True).load_dialect_impl(MockDialect(name)).none_as_null is True
            assert UniversalJSON().load_dialect_impl(MockDialect(name)).none_as_null is False
        assert isinstance(UniversalJSON().load_dialect_impl(MockDialect("postgresql")), JSONB)


class TestUniversalUUID:
    """Tests for UniversalUUID type."""

    def test_load_dialect_impl_sqlite(self):
        """Should use String(36) for SQLite."""
        universal_uuid = UniversalUUID()
        dialect = MockDialect("sqlite")
        result = universal_uuid.load_dialect_impl(dialect)
        assert result is not None

    def test_load_dialect_impl_postgresql(self):
        """Should use UUID for PostgreSQL."""
        universal_uuid = UniversalUUID()
        dialect = MockDialect("postgresql")
        result = universal_uuid.load_dialect_impl(dialect)
        assert result is not None

    def test_process_bind_param_none(self):
        """Should return None for None value."""
        universal_uuid = UniversalUUID()
        dialect = MockDialect("sqlite")
        result = universal_uuid.process_bind_param(None, dialect)
        assert result is None

    def test_process_bind_param_string(self):
        """Should return string representation."""
        universal_uuid = UniversalUUID()
        dialect = MockDialect("sqlite")
        result = universal_uuid.process_bind_param("123e4567-e89b-12d3-a456-426614174000", dialect)
        assert result == "123e4567-e89b-12d3-a456-426614174000"

    def test_process_result_value_none(self):
        """Should return None for None value."""
        universal_uuid = UniversalUUID()
        dialect = MockDialect("sqlite")
        result = universal_uuid.process_result_value(None, dialect)
        assert result is None

    def test_process_result_value_string(self):
        """Should return string representation."""
        universal_uuid = UniversalUUID()
        dialect = MockDialect("sqlite")
        result = universal_uuid.process_result_value("123e4567-e89b-12d3-a456-426614174000", dialect)
        assert result == "123e4567-e89b-12d3-a456-426614174000"

    def test_cache_ok(self):
        """Should have cache_ok = True."""
        assert UniversalUUID.cache_ok is True


class TestDialectCompatibility:
    """Integration-style tests for dialect compatibility."""

    def test_string_array_roundtrip_sqlite(self):
        """StringArray should serialize and deserialize correctly for SQLite."""
        string_array = StringArray()
        dialect = MockDialect("sqlite")

        original = ["apple", "banana", "cherry"]
        bound = string_array.process_bind_param(original, dialect)
        result = string_array.process_result_value(bound, dialect)

        assert result == original

    def test_string_array_roundtrip_postgresql(self):
        """StringArray should pass through correctly for PostgreSQL."""
        string_array = StringArray()
        dialect = MockDialect("postgresql")

        original = ["apple", "banana", "cherry"]
        bound = string_array.process_bind_param(original, dialect)
        result = string_array.process_result_value(bound, dialect)

        assert result == original

    def test_universal_uuid_roundtrip(self):
        """UniversalUUID should serialize and deserialize correctly."""
        universal_uuid = UniversalUUID()
        dialect = MockDialect("sqlite")

        original = "550e8400-e29b-41d4-a716-446655440000"
        bound = universal_uuid.process_bind_param(original, dialect)
        result = universal_uuid.process_result_value(bound, dialect)

        assert result == original

    def test_empty_string_array(self):
        """Should handle empty arrays."""
        string_array = StringArray()
        dialect = MockDialect("sqlite")

        original = []
        bound = string_array.process_bind_param(original, dialect)
        result = string_array.process_result_value(bound, dialect)

        assert result == original

    def test_string_array_with_special_chars(self):
        """Should handle special characters in array."""
        string_array = StringArray()
        dialect = MockDialect("sqlite")

        original = ["hello\nworld", 'foo"bar', "baz\\qux"]
        bound = string_array.process_bind_param(original, dialect)
        result = string_array.process_result_value(bound, dialect)

        assert result == original
