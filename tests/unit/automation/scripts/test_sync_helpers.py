"""
Tests for sync_to_postgres helper functions that aren't covered by existing tests.

Focuses on _validate_quality_score, _parse_markdown_section, and _validate_spec_id.
"""

import pytest

from automation.scripts.sync_to_postgres import (
    _parse_markdown_section,
    _validate_quality_score,
    _validate_spec_id,
)


class TestValidateQualityScore:
    """Tests for _validate_quality_score."""

    def test_none(self) -> None:
        assert _validate_quality_score(None) is None

    def test_valid_float(self) -> None:
        assert _validate_quality_score(92.5) == 92.5

    def test_valid_int(self) -> None:
        assert _validate_quality_score(90) == 90.0

    def test_zero(self) -> None:
        assert _validate_quality_score(0) == 0.0

    def test_hundred(self) -> None:
        assert _validate_quality_score(100) == 100.0

    def test_string_number(self) -> None:
        assert _validate_quality_score("85.5") == 85.5

    def test_out_of_range_high(self) -> None:
        assert _validate_quality_score(101) is None

    def test_out_of_range_negative(self) -> None:
        assert _validate_quality_score(-1) is None

    def test_invalid_string(self) -> None:
        assert _validate_quality_score("not-a-number") is None

    def test_invalid_type(self) -> None:
        assert _validate_quality_score([1, 2, 3]) is None


class TestValidateSpecId:
    """Tests for _validate_spec_id."""

    def test_valid_simple(self) -> None:
        assert _validate_spec_id("scatter") is True

    def test_valid_with_hyphens(self) -> None:
        assert _validate_spec_id("scatter-basic") is True

    def test_valid_multi_hyphen(self) -> None:
        assert _validate_spec_id("scatter-regression-linear") is True

    def test_valid_with_numbers(self) -> None:
        assert _validate_spec_id("bar-3d-categorical") is True

    def test_invalid_uppercase(self) -> None:
        assert _validate_spec_id("Scatter-Basic") is False

    def test_invalid_underscore(self) -> None:
        assert _validate_spec_id("scatter_basic") is False

    def test_invalid_spaces(self) -> None:
        assert _validate_spec_id("scatter basic") is False

    def test_invalid_starts_with_hyphen(self) -> None:
        assert _validate_spec_id("-scatter") is False

    def test_invalid_ends_with_hyphen(self) -> None:
        assert _validate_spec_id("scatter-") is False

    def test_empty_string(self) -> None:
        assert _validate_spec_id("") is False

    def test_invalid_double_hyphen(self) -> None:
        assert _validate_spec_id("scatter--basic") is False


class TestParseMarkdownSection:
    """Tests for _parse_markdown_section."""

    def test_parse_text_section(self) -> None:
        content = "## Description\nThis is a scatter plot.\n## Applications\n- Data viz\n"
        result = _parse_markdown_section(content, "Description")
        assert result == "This is a scatter plot."

    def test_parse_bullet_section(self) -> None:
        content = "## Applications\n- Data visualization\n- Correlation analysis\n## Notes\n"
        result = _parse_markdown_section(content, "Applications", as_bullets=True)
        assert result == ["Data visualization", "Correlation analysis"]

    def test_missing_section_text(self) -> None:
        content = "## Other\nSome content\n"
        result = _parse_markdown_section(content, "Description")
        assert result == ""

    def test_missing_section_bullets(self) -> None:
        content = "## Other\nSome content\n"
        result = _parse_markdown_section(content, "Applications", as_bullets=True)
        assert result == []

    def test_section_at_end_of_file(self) -> None:
        content = "## Description\nLast section content."
        result = _parse_markdown_section(content, "Description")
        assert result == "Last section content."

    def test_multiline_text_section(self) -> None:
        content = "## Description\nLine 1\nLine 2\nLine 3\n## Next\n"
        result = _parse_markdown_section(content, "Description")
        assert "Line 1" in result
        assert "Line 3" in result
