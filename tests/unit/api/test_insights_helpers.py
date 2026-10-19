"""
Tests for insights helper functions.

Directly tests the pure helper functions in api/routers/insights.py
that don't require database or HTTP setup.
"""

from datetime import timezone
from unittest.mock import MagicMock

from api.routers.insights import _flatten_tags, _parse_iso, _related_entry, _score_bucket


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


def _impl(library_id: str, impl_tags: object, score: float | None = None, preview: str | None = None) -> MagicMock:
    impl = MagicMock()
    impl.library_id = library_id
    impl.impl_tags = impl_tags
    impl.quality_score = score
    impl.preview_url = preview
    impl.preview_url_light = preview
    impl.preview_url_dark = None
    impl.library.language = "python"
    return impl


def _spec(tags: dict | None, impls: list[MagicMock]) -> MagicMock:
    spec = MagicMock()
    spec.id = "scatter-basic"
    spec.title = "Basic Scatter"
    spec.tags = tags
    spec.impls = impls
    return spec


class TestRelatedEntryTags:
    """Tests for the tag sets of _related_entry."""

    def test_spec_with_no_tags(self) -> None:
        entry = _related_entry(_spec(None, []))
        assert entry.tags("spec", None) == set()
        assert entry.tags("full", None) == set()

    def test_spec_mode_ignores_impl_tags(self) -> None:
        entry = _related_entry(
            _spec({"plot_type": ["scatter"]}, [_impl("matplotlib", {"techniques": ["annotations"]})])
        )
        assert entry.tags("spec", "matplotlib") == {"plot_type:scatter"}

    def test_full_mode_without_library_collects_every_impl(self) -> None:
        impls = [_impl("matplotlib", {"techniques": ["annotations"]}), _impl("seaborn", {"techniques": ["regression"]})]
        entry = _related_entry(_spec({"plot_type": ["scatter"]}, impls))
        assert entry.tags("full", None) == {"plot_type:scatter", "techniques:annotations", "techniques:regression"}

    def test_full_mode_filters_by_library(self) -> None:
        impls = [_impl("matplotlib", {"techniques": ["annotations"]}), _impl("seaborn", {"techniques": ["regression"]})]
        entry = _related_entry(_spec({"plot_type": ["scatter"]}, impls))
        assert entry.tags("full", "matplotlib") == {"plot_type:scatter", "techniques:annotations"}
        assert entry.tags("full", "plotly") == {"plot_type:scatter"}

    def test_one_library_in_two_languages_unions_its_tags(self) -> None:
        impls = [_impl("plotly", {"techniques": ["hover"]}), _impl("plotly", {"techniques": ["animation"]})]
        entry = _related_entry(_spec({}, impls))
        assert entry.tags("full", "plotly") == {"techniques:hover", "techniques:animation"}

    def test_impl_tags_none(self) -> None:
        entry = _related_entry(_spec({"plot_type": ["scatter"]}, [_impl("matplotlib", None)]))
        assert entry.tags("full", None) == {"plot_type:scatter"}

    def test_impl_tags_not_dict(self) -> None:
        entry = _related_entry(_spec({}, [_impl("matplotlib", "not-a-dict")]))
        assert entry.tags("full", None) == set()


class TestRelatedEntryPreview:
    """Tests for the preview _related_entry picks."""

    def test_best_scored_impl_with_a_preview(self) -> None:
        impls = [
            _impl("matplotlib", None, score=88.0, preview="m.png"),
            _impl("seaborn", None, score=95.0, preview="s.png"),
            _impl("plotly", None, score=99.0, preview=None),
        ]
        assert _related_entry(_spec(None, impls)).preview == ("s.png", "s.png", None, "seaborn", "python")

    def test_no_preview(self) -> None:
        assert _related_entry(_spec(None, [_impl("matplotlib", None, score=90.0)])).preview is None
