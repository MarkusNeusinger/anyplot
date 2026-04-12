"""
Tests for insights helper functions.

Directly tests the pure helper functions in api/routers/insights.py
that don't require database or HTTP setup.
"""

from datetime import datetime, timezone

import pytest

from api.routers.insights import (
    _collect_impl_tags,
    _flatten_tags,
    _parse_iso,
    _score_bucket,
)


class TestScoreBucket:
    """Tests for _score_bucket mapping."""

    def test_minimum_score(self) -> None:
        assert _score_bucket(50) == "50-55"

    def test_maximum_score(self) -> None:
        assert _score_bucket(100) == "95-100"

    def test_middle_scores(self) -> None:
        assert _score_bucket(72) == "70-75"
        assert _score_bucket(85) == "85-90"
        assert _score_bucket(90) == "90-95"

    def test_boundary_at_55(self) -> None:
        assert _score_bucket(55) == "55-60"

    def test_below_50_clamped(self) -> None:
        assert _score_bucket(30) == "50-55"

    def test_above_100_clamped(self) -> None:
        assert _score_bucket(110) == "95-100"

    def test_exact_boundary(self) -> None:
        assert _score_bucket(75) == "75-80"
        assert _score_bucket(80) == "80-85"

    def test_fractional_score(self) -> None:
        assert _score_bucket(92.5) == "90-95"
        assert _score_bucket(87.9) == "85-90"


class TestFlattenTags:
    """Tests for _flatten_tags."""

    def test_none_tags(self) -> None:
        assert _flatten_tags(None) == set()

    def test_empty_dict(self) -> None:
        assert _flatten_tags({}) == set()

    def test_single_category(self) -> None:
        tags = {"plot_type": ["scatter"]}
        assert _flatten_tags(tags) == {"plot_type:scatter"}

    def test_multiple_categories(self) -> None:
        tags = {"plot_type": ["scatter", "line"], "domain": ["statistics"]}
        result = _flatten_tags(tags)
        assert result == {"plot_type:scatter", "plot_type:line", "domain:statistics"}

    def test_non_list_values_skipped(self) -> None:
        tags = {"plot_type": ["scatter"], "invalid": "not-a-list"}
        result = _flatten_tags(tags)
        assert result == {"plot_type:scatter"}

    def test_empty_list(self) -> None:
        tags = {"plot_type": []}
        assert _flatten_tags(tags) == set()


class TestParseIso:
    """Tests for _parse_iso."""

    def test_none_input(self) -> None:
        assert _parse_iso(None) is None

    def test_empty_string(self) -> None:
        assert _parse_iso("") is None

    def test_valid_iso_with_z(self) -> None:
        result = _parse_iso("2025-01-15T10:30:00Z")
        assert result is not None
        assert result.year == 2025
        assert result.month == 1
        assert result.tzinfo is not None

    def test_valid_iso_with_offset(self) -> None:
        result = _parse_iso("2025-01-15T10:30:00+02:00")
        assert result is not None
        assert result.tzinfo is not None

    def test_naive_datetime_gets_utc(self) -> None:
        result = _parse_iso("2025-01-15T10:30:00")
        assert result is not None
        assert result.tzinfo == timezone.utc

    def test_invalid_string(self) -> None:
        assert _parse_iso("not-a-date") is None

    def test_date_only(self) -> None:
        result = _parse_iso("2025-01-15")
        assert result is not None
        assert result.year == 2025


class TestCollectImplTags:
    """Tests for _collect_impl_tags."""

    def test_spec_with_no_tags(self) -> None:
        from unittest.mock import MagicMock

        spec = MagicMock()
        spec.tags = None
        spec.impls = []
        result = _collect_impl_tags(spec)
        assert result == set()

    def test_spec_with_tags_and_impl_tags(self) -> None:
        from unittest.mock import MagicMock

        impl = MagicMock()
        impl.library_id = "matplotlib"
        impl.impl_tags = {"techniques": ["annotations"]}

        spec = MagicMock()
        spec.tags = {"plot_type": ["scatter"]}
        spec.impls = [impl]

        result = _collect_impl_tags(spec)
        assert "plot_type:scatter" in result
        assert "techniques:annotations" in result

    def test_filter_by_library(self) -> None:
        from unittest.mock import MagicMock

        impl1 = MagicMock()
        impl1.library_id = "matplotlib"
        impl1.impl_tags = {"techniques": ["annotations"]}

        impl2 = MagicMock()
        impl2.library_id = "seaborn"
        impl2.impl_tags = {"techniques": ["regression"]}

        spec = MagicMock()
        spec.tags = {"plot_type": ["scatter"]}
        spec.impls = [impl1, impl2]

        result = _collect_impl_tags(spec, library="matplotlib")
        assert "techniques:annotations" in result
        assert "techniques:regression" not in result

    def test_impl_tags_none(self) -> None:
        from unittest.mock import MagicMock

        impl = MagicMock()
        impl.library_id = "matplotlib"
        impl.impl_tags = None

        spec = MagicMock()
        spec.tags = {"plot_type": ["scatter"]}
        spec.impls = [impl]

        result = _collect_impl_tags(spec)
        assert result == {"plot_type:scatter"}

    def test_impl_tags_not_dict(self) -> None:
        from unittest.mock import MagicMock

        impl = MagicMock()
        impl.library_id = "matplotlib"
        impl.impl_tags = "not-a-dict"

        spec = MagicMock()
        spec.tags = {}
        spec.impls = [impl]

        result = _collect_impl_tags(spec)
        assert result == set()
