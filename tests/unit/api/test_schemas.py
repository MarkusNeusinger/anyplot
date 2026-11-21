"""
Tests for API Pydantic schemas.

Validates schema creation, defaults, and serialization.
"""

from typing import get_args

import pytest

from api.schemas import (
    FilterCountsResponse,
    FilteredPlotsResponse,
    ImageResponse,
    ImplementationResponse,
    LibraryInfo,
    SpecDetailResponse,
    SpecListItem,
    SpecSources,
    StatsResponse,
)
from core.spec_sources import DATA_KINDS


class TestSpecSources:
    """The stored sources block as the API serves it."""

    def test_the_data_kinds_are_the_checks(self) -> None:
        literal, _none = get_args(SpecSources.model_fields["data"].annotation)
        assert get_args(literal) == DATA_KINDS

    def test_a_stored_block_is_served_with_every_field(self) -> None:
        sources = SpecSources.from_stored({"inspired_by": [{"title": "A", "url": "https://example.org/a"}]})
        assert sources is not None
        assert sources.has_entries
        assert sources.model_dump() == {
            "data": None,
            "inspired_by": [{"title": "A", "url": "https://example.org/a", "doi": None, "isbn": None}],
            "references": [],
        }

    def test_data_alone_has_no_entries(self) -> None:
        sources = SpecSources.from_stored({"data": "invented"})
        assert sources is not None
        assert not sources.has_entries

    @pytest.mark.parametrize(
        "value",
        [None, "text", ["a"], {"references": [{"title": "A", "url": "javascript:alert(1)"}]}, {"unknown": []}],
        ids=["null", "string", "list", "javascript-url", "unknown-key"],
    )
    def test_nothing_that_fails_the_check_is_served(self, value: object) -> None:
        assert SpecSources.from_stored(value) is None

    def test_the_spec_detail_defaults_to_no_sources(self) -> None:
        assert SpecDetailResponse(id="scatter-basic", title="Basic Scatter Plot").sources is None


class TestImplementationResponse:
    """Tests for ImplementationResponse schema."""

    def test_minimal_creation(self) -> None:
        impl = ImplementationResponse(library_id="matplotlib", library_name="Matplotlib", language="python")
        assert impl.library_id == "matplotlib"
        assert impl.library_name == "Matplotlib"
        assert impl.language == "python"
        assert impl.preview_url is None
        assert impl.quality_score is None
        assert impl.code is None
        assert impl.review_strengths == []
        assert impl.review_weaknesses == []
        assert impl.impl_tags is None

    def test_full_creation(self) -> None:
        impl = ImplementationResponse(
            library_id="matplotlib",
            library_name="Matplotlib",
            language="python",
            preview_url="https://example.com/img.png",
            preview_html="<div>chart</div>",
            quality_score=92.5,
            code="import matplotlib",
            generated_at="2025-01-01T00:00:00",
            updated="2025-01-02T00:00:00",
            generated_by="claude",
            python_version="3.13",
            library_version="3.10.0",
            review_strengths=["clean code"],
            review_weaknesses=["needs labels"],
            review_image_description="A scatter plot",
            review_criteria_checklist={"visual_quality": {"score": 36}},
            review_verdict="APPROVED",
            impl_tags={"techniques": ["annotations"]},
        )
        assert impl.quality_score == 92.5
        assert impl.review_verdict == "APPROVED"
        assert impl.impl_tags == {"techniques": ["annotations"]}

    def test_serialization(self) -> None:
        impl = ImplementationResponse(library_id="matplotlib", library_name="Matplotlib", language="python")
        data = impl.model_dump()
        assert data["library_id"] == "matplotlib"
        assert data["language"] == "python"
        assert data["review_strengths"] == []


class TestSpecDetailResponse:
    """Tests for SpecDetailResponse schema."""

    def test_minimal_creation(self) -> None:
        spec = SpecDetailResponse(id="scatter-basic", title="Basic Scatter")
        assert spec.id == "scatter-basic"
        assert spec.description is None
        assert spec.applications == []
        assert spec.implementations == []
        assert spec.tags is None
        assert spec.issue is None

    def test_with_implementations(self) -> None:
        impl = ImplementationResponse(library_id="matplotlib", library_name="Matplotlib", language="python")
        spec = SpecDetailResponse(
            id="scatter-basic",
            title="Basic Scatter",
            description="A scatter plot",
            implementations=[impl],
            tags={"plot_type": ["scatter"]},
            issue=42,
        )
        assert len(spec.implementations) == 1
        assert spec.implementations[0].library_id == "matplotlib"


class TestSpecListItem:
    """Tests for SpecListItem schema."""

    def test_minimal_creation(self) -> None:
        item = SpecListItem(id="scatter-basic", title="Basic Scatter")
        assert item.library_count == 0
        assert item.description is None
        assert item.tags is None

    def test_with_library_count(self) -> None:
        item = SpecListItem(id="scatter-basic", title="Basic Scatter", library_count=5)
        assert item.library_count == 5


class TestImageResponse:
    """Tests for ImageResponse schema."""

    def test_minimal(self) -> None:
        img = ImageResponse(spec_id="scatter-basic", library="matplotlib")
        assert img.url is None
        assert img.html is None
        assert img.code is None

    def test_full(self) -> None:
        img = ImageResponse(
            spec_id="scatter-basic",
            library="matplotlib",
            url="https://example.com/img.png",
            html="<div></div>",
            code="import matplotlib",
        )
        assert img.url == "https://example.com/img.png"


class TestFilterCountsResponse:
    """Tests for FilterCountsResponse schema."""

    def test_defaults_empty(self) -> None:
        counts = FilterCountsResponse()
        assert counts.lib == {}
        assert counts.spec == {}
        assert counts.plot == {}
        assert counts.data == {}
        assert counts.dom == {}
        assert counts.feat == {}
        assert counts.dep == {}
        assert counts.tech == {}
        assert counts.pat == {}
        assert counts.prep == {}
        assert counts.style == {}

    def test_with_counts(self) -> None:
        counts = FilterCountsResponse(lib={"matplotlib": 5, "seaborn": 3}, plot={"scatter": 8})
        assert counts.lib["matplotlib"] == 5


class TestFilteredPlotsResponse:
    """Tests for FilteredPlotsResponse schema."""

    def test_minimal(self) -> None:
        resp = FilteredPlotsResponse(total=0, images=[], counts={}, globalCounts={}, orCounts=[])
        assert resp.total == 0
        assert resp.offset == 0
        assert resp.limit is None
        assert resp.specTitles == {}

    def test_with_pagination(self) -> None:
        resp = FilteredPlotsResponse(
            total=100,
            images=[{"spec_id": "s1", "library": "matplotlib"}],
            counts={},
            globalCounts={},
            orCounts=[],
            offset=10,
            limit=20,
        )
        assert resp.offset == 10
        assert resp.limit == 20


class TestLibraryInfo:
    """Tests for LibraryInfo schema."""

    def test_minimal(self) -> None:
        lib = LibraryInfo(id="matplotlib", name="Matplotlib", language="python")
        assert lib.language == "python"
        assert lib.version is None
        assert lib.documentation_url is None

    def test_full(self) -> None:
        lib = LibraryInfo(
            id="matplotlib",
            name="Matplotlib",
            language="python",
            version="3.10.0",
            documentation_url="https://matplotlib.org",
            description="A comprehensive plotting library",
        )
        assert lib.version == "3.10.0"


class TestStatsResponse:
    """Tests for StatsResponse schema."""

    def test_creation(self) -> None:
        stats = StatsResponse(specs=100, plots=500, libraries=9)
        assert stats.specs == 100
        assert stats.plots == 500
        assert stats.libraries == 9

    def test_serialization(self) -> None:
        stats = StatsResponse(specs=10, plots=50, libraries=9)
        data = stats.model_dump()
        assert data == {"specs": 10, "plots": 50, "libraries": 9, "languages": 0, "lines_of_code": 0}

    def test_languages_field(self) -> None:
        stats = StatsResponse(specs=10, plots=50, libraries=10, languages=2)
        assert stats.languages == 2
