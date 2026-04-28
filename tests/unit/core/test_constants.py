"""
Tests for core/constants.py.

Tests the centralized constants and helper functions.
"""

from core.constants import (
    ATTEMPT_LABELS,
    INTERACTIVE_LIBRARIES,
    LIBRARIES_METADATA,
    LIBRARY_LABELS,
    QUALITY_LABELS,
    QUALITY_THRESHOLD_APPROVAL,
    QUALITY_THRESHOLD_EXCELLENT,
    QUALITY_THRESHOLD_FINAL_APPROVAL,
    QUALITY_THRESHOLD_GOOD,
    QUALITY_THRESHOLD_NEEDS_WORK,
    STATUS_LABELS,
    SUPPORTED_LIBRARIES,
    get_library_label,
    is_interactive_library,
    is_valid_library,
)


class TestSupportedLibraries:
    """Tests for SUPPORTED_LIBRARIES constant."""

    def test_contains_all_nine_libraries(self) -> None:
        """Should contain exactly 9 supported libraries."""
        assert len(SUPPORTED_LIBRARIES) == 9

    def test_contains_expected_libraries(self) -> None:
        """Should contain all expected library IDs."""
        expected = {"altair", "bokeh", "highcharts", "letsplot", "matplotlib", "plotly", "plotnine", "pygal", "seaborn"}
        assert SUPPORTED_LIBRARIES == expected

    def test_is_frozenset(self) -> None:
        """Should be a frozenset (immutable)."""
        assert isinstance(SUPPORTED_LIBRARIES, frozenset)


class TestLibrariesMetadata:
    """Tests for LIBRARIES_METADATA constant."""

    def test_contains_all_nine_libraries(self) -> None:
        """Should contain metadata for all 9 libraries."""
        assert len(LIBRARIES_METADATA) == 9

    def test_ids_match_supported_libraries(self) -> None:
        """All metadata IDs should match SUPPORTED_LIBRARIES."""
        metadata_ids = {lib["id"] for lib in LIBRARIES_METADATA}
        assert metadata_ids == SUPPORTED_LIBRARIES

    def test_each_library_has_required_fields(self) -> None:
        """Each library should have all required fields."""
        required_fields = {"id", "name", "version", "documentation_url", "description"}
        for lib in LIBRARIES_METADATA:
            assert required_fields.issubset(lib.keys()), f"Missing fields in {lib.get('id', 'unknown')}"

    def test_documentation_urls_are_valid(self) -> None:
        """Documentation URLs should be valid HTTP(S) URLs."""
        for lib in LIBRARIES_METADATA:
            url = lib["documentation_url"]
            assert url.startswith("http://") or url.startswith("https://"), f"Invalid URL for {lib['id']}: {url}"


class TestInteractiveLibraries:
    """Tests for INTERACTIVE_LIBRARIES constant."""

    def test_is_subset_of_supported(self) -> None:
        """Interactive libraries should be a subset of supported libraries."""
        assert INTERACTIVE_LIBRARIES.issubset(SUPPORTED_LIBRARIES)

    def test_contains_expected_libraries(self) -> None:
        """Should contain the expected interactive libraries."""
        expected = {"altair", "bokeh", "highcharts", "letsplot", "plotly", "pygal"}
        assert INTERACTIVE_LIBRARIES == expected

    def test_matplotlib_seaborn_plotnine_not_interactive(self) -> None:
        """Static-only libraries should not be in interactive set."""
        assert "matplotlib" not in INTERACTIVE_LIBRARIES
        assert "seaborn" not in INTERACTIVE_LIBRARIES
        assert "plotnine" not in INTERACTIVE_LIBRARIES


class TestGitHubLabels:
    """Tests for GitHub label constants."""

    def test_library_labels_match_supported(self) -> None:
        """Library labels should match supported libraries."""
        expected = {f"library:{lib}" for lib in SUPPORTED_LIBRARIES}
        assert LIBRARY_LABELS == expected

    def test_status_labels_count(self) -> None:
        """Should have expected number of status labels."""
        assert len(STATUS_LABELS) == 10

    def test_quality_labels_count(self) -> None:
        """Should have 4 quality levels."""
        assert len(QUALITY_LABELS) == 4

    def test_attempt_labels_count(self) -> None:
        """Should have 4 attempt labels."""
        assert len(ATTEMPT_LABELS) == 4
        assert ATTEMPT_LABELS == {"ai-attempt-1", "ai-attempt-2", "ai-attempt-3", "ai-attempt-4"}


class TestQualityThresholds:
    """Tests for quality threshold constants."""

    def test_thresholds_are_ordered(self) -> None:
        """Thresholds should be in descending order."""
        assert QUALITY_THRESHOLD_EXCELLENT > QUALITY_THRESHOLD_GOOD
        assert QUALITY_THRESHOLD_GOOD > QUALITY_THRESHOLD_NEEDS_WORK
        assert QUALITY_THRESHOLD_NEEDS_WORK > QUALITY_THRESHOLD_FINAL_APPROVAL

    def test_approval_equals_excellent(self) -> None:
        """Immediate approval threshold should equal excellent."""
        assert QUALITY_THRESHOLD_APPROVAL == QUALITY_THRESHOLD_EXCELLENT

    def test_threshold_values(self) -> None:
        """Thresholds should have expected values."""
        assert QUALITY_THRESHOLD_EXCELLENT == 90
        assert QUALITY_THRESHOLD_GOOD == 85
        assert QUALITY_THRESHOLD_NEEDS_WORK == 75
        assert QUALITY_THRESHOLD_FINAL_APPROVAL == 50


class TestIsValidLibrary:
    """Tests for is_valid_library helper function."""

    def test_valid_library_lowercase(self) -> None:
        """Should return True for valid library in lowercase."""
        assert is_valid_library("matplotlib") is True

    def test_valid_library_uppercase(self) -> None:
        """Should return True for valid library in uppercase."""
        assert is_valid_library("MATPLOTLIB") is True

    def test_valid_library_mixed_case(self) -> None:
        """Should return True for valid library in mixed case."""
        assert is_valid_library("Matplotlib") is True

    def test_invalid_library(self) -> None:
        """Should return False for invalid library."""
        assert is_valid_library("pandas") is False

    def test_all_supported_libraries_valid(self) -> None:
        """All supported libraries should be valid."""
        for lib in SUPPORTED_LIBRARIES:
            assert is_valid_library(lib) is True

    def test_letsplot_is_valid(self) -> None:
        """letsplot should be valid (critical bug fix)."""
        assert is_valid_library("letsplot") is True


class TestGetLibraryLabel:
    """Tests for get_library_label helper function."""

    def test_returns_correct_format(self) -> None:
        """Should return library:name format."""
        assert get_library_label("matplotlib") == "library:matplotlib"

    def test_lowercase_conversion(self) -> None:
        """Should convert to lowercase."""
        assert get_library_label("MATPLOTLIB") == "library:matplotlib"
        assert get_library_label("Matplotlib") == "library:matplotlib"

    def test_all_labels_in_library_labels(self) -> None:
        """Generated labels should be in LIBRARY_LABELS."""
        for lib in SUPPORTED_LIBRARIES:
            label = get_library_label(lib)
            assert label in LIBRARY_LABELS


class TestIsInteractiveLibrary:
    """Tests for is_interactive_library helper function."""

    def test_plotly_is_interactive(self) -> None:
        """Plotly should be interactive."""
        assert is_interactive_library("plotly") is True

    def test_matplotlib_not_interactive(self) -> None:
        """Matplotlib should not be interactive."""
        assert is_interactive_library("matplotlib") is False

    def test_case_insensitive(self) -> None:
        """Should be case insensitive."""
        assert is_interactive_library("PLOTLY") is True
        assert is_interactive_library("Plotly") is True

    def test_all_interactive_libraries(self) -> None:
        """All interactive libraries should return True."""
        for lib in INTERACTIVE_LIBRARIES:
            assert is_interactive_library(lib) is True

    def test_static_libraries(self) -> None:
        """Static libraries should return False."""
        static = SUPPORTED_LIBRARIES - INTERACTIVE_LIBRARIES
        for lib in static:
            assert is_interactive_library(lib) is False
