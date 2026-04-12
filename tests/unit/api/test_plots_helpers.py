"""
Tests for plots filter helper functions.

Directly tests the pure helper functions in api/routers/plots.py.
"""

from unittest.mock import MagicMock

from api.routers.plots import (
    _build_cache_key,
    _build_impl_lookup,
    _build_spec_lookup,
    _calculate_contextual_counts,
    _calculate_global_counts,
    _calculate_or_counts,
    _category_matches_filter,
    _collect_all_images,
    _create_empty_counts,
    _filter_images,
    _get_category_values,
    _image_matches_groups,
    _increment_category_counts,
    _sort_counts,
)


class TestGetCategoryValues:
    """Tests for _get_category_values."""

    def test_lib_category(self) -> None:
        result = _get_category_values("lib", "scatter-basic", "matplotlib", {}, {})
        assert result == ["matplotlib"]

    def test_spec_category(self) -> None:
        result = _get_category_values("spec", "scatter-basic", "matplotlib", {}, {})
        assert result == ["scatter-basic"]

    def test_spec_level_category(self) -> None:
        spec_tags = {"plot_type": ["scatter", "line"]}
        result = _get_category_values("plot", "s", "m", spec_tags, {})
        assert result == ["scatter", "line"]

    def test_impl_level_category(self) -> None:
        impl_tags = {"techniques": ["annotations", "colorbar"]}
        result = _get_category_values("tech", "s", "m", {}, impl_tags)
        assert result == ["annotations", "colorbar"]

    def test_unknown_category(self) -> None:
        result = _get_category_values("unknown", "s", "m", {}, {})
        assert result == []

    def test_data_category(self) -> None:
        spec_tags = {"data_type": ["numeric"]}
        result = _get_category_values("data", "s", "m", spec_tags, {})
        assert result == ["numeric"]

    def test_dom_category(self) -> None:
        spec_tags = {"domain": ["statistics", "finance"]}
        result = _get_category_values("dom", "s", "m", spec_tags, {})
        assert result == ["statistics", "finance"]

    def test_feat_category(self) -> None:
        spec_tags = {"features": ["basic", "3d"]}
        result = _get_category_values("feat", "s", "m", spec_tags, {})
        assert result == ["basic", "3d"]

    def test_dep_category(self) -> None:
        impl_tags = {"dependencies": ["scipy"]}
        result = _get_category_values("dep", "s", "m", {}, impl_tags)
        assert result == ["scipy"]

    def test_pat_category(self) -> None:
        impl_tags = {"patterns": ["data-generation"]}
        result = _get_category_values("pat", "s", "m", {}, impl_tags)
        assert result == ["data-generation"]

    def test_prep_category(self) -> None:
        impl_tags = {"dataprep": ["binning"]}
        result = _get_category_values("prep", "s", "m", {}, impl_tags)
        assert result == ["binning"]

    def test_style_category(self) -> None:
        impl_tags = {"styling": ["minimal-chrome"]}
        result = _get_category_values("style", "s", "m", {}, impl_tags)
        assert result == ["minimal-chrome"]

    def test_missing_key_in_tags(self) -> None:
        spec_tags = {"other_key": ["value"]}
        result = _get_category_values("plot", "s", "m", spec_tags, {})
        assert result == []


class TestCategoryMatchesFilter:
    """Tests for _category_matches_filter."""

    def test_matching_lib(self) -> None:
        assert _category_matches_filter("lib", ["matplotlib"], "s", "matplotlib", {}, {}) is True

    def test_non_matching_lib(self) -> None:
        assert _category_matches_filter("lib", ["seaborn"], "s", "matplotlib", {}, {}) is False

    def test_one_of_multiple_values_matches(self) -> None:
        assert _category_matches_filter("lib", ["seaborn", "matplotlib"], "s", "matplotlib", {}, {}) is True

    def test_matching_spec_tag(self) -> None:
        spec_tags = {"plot_type": ["scatter"]}
        assert _category_matches_filter("plot", ["scatter"], "s", "m", spec_tags, {}) is True

    def test_matching_impl_tag(self) -> None:
        impl_tags = {"techniques": ["annotations"]}
        assert _category_matches_filter("tech", ["annotations"], "s", "m", {}, impl_tags) is True


class TestImageMatchesGroups:
    """Tests for _image_matches_groups."""

    def test_empty_groups_matches_all(self) -> None:
        spec_lookup = {"s1": {"tags": {}}}
        impl_lookup = {}
        assert _image_matches_groups("s1", "matplotlib", [], spec_lookup, impl_lookup) is True

    def test_single_group_match(self) -> None:
        spec_lookup = {"s1": {"tags": {"plot_type": ["scatter"]}}}
        impl_lookup = {}
        groups = [{"category": "plot", "values": ["scatter"]}]
        assert _image_matches_groups("s1", "matplotlib", groups, spec_lookup, impl_lookup) is True

    def test_single_group_no_match(self) -> None:
        spec_lookup = {"s1": {"tags": {"plot_type": ["bar"]}}}
        impl_lookup = {}
        groups = [{"category": "plot", "values": ["scatter"]}]
        assert _image_matches_groups("s1", "matplotlib", groups, spec_lookup, impl_lookup) is False

    def test_multiple_groups_and_logic(self) -> None:
        spec_lookup = {"s1": {"tags": {"plot_type": ["scatter"], "domain": ["statistics"]}}}
        impl_lookup = {}
        groups = [{"category": "plot", "values": ["scatter"]}, {"category": "dom", "values": ["statistics"]}]
        assert _image_matches_groups("s1", "matplotlib", groups, spec_lookup, impl_lookup) is True

    def test_multiple_groups_one_fails(self) -> None:
        spec_lookup = {"s1": {"tags": {"plot_type": ["scatter"], "domain": ["finance"]}}}
        impl_lookup = {}
        groups = [{"category": "plot", "values": ["scatter"]}, {"category": "dom", "values": ["statistics"]}]
        assert _image_matches_groups("s1", "matplotlib", groups, spec_lookup, impl_lookup) is False

    def test_spec_not_in_lookup(self) -> None:
        assert _image_matches_groups("unknown", "matplotlib", [], {}, {}) is False

    def test_impl_tags_matching(self) -> None:
        spec_lookup = {"s1": {"tags": {}}}
        impl_lookup = {("s1", "matplotlib"): {"techniques": ["annotations"]}}
        groups = [{"category": "tech", "values": ["annotations"]}]
        assert _image_matches_groups("s1", "matplotlib", groups, spec_lookup, impl_lookup) is True


class TestCreateEmptyCounts:
    """Tests for _create_empty_counts."""

    def test_has_all_categories(self) -> None:
        counts = _create_empty_counts()
        expected = {"lib", "spec", "plot", "data", "dom", "feat", "dep", "tech", "pat", "prep", "style"}
        assert set(counts.keys()) == expected

    def test_all_categories_empty(self) -> None:
        counts = _create_empty_counts()
        for category in counts.values():
            assert category == {}


class TestIncrementCategoryCounts:
    """Tests for _increment_category_counts."""

    def test_increments_all_categories(self) -> None:
        counts = _create_empty_counts()
        spec_tags = {"plot_type": ["scatter"], "domain": ["statistics"]}
        impl_tags = {"techniques": ["annotations"]}
        _increment_category_counts(counts, "scatter-basic", "matplotlib", spec_tags, impl_tags)

        assert counts["lib"]["matplotlib"] == 1
        assert counts["spec"]["scatter-basic"] == 1
        assert counts["plot"]["scatter"] == 1
        assert counts["dom"]["statistics"] == 1
        assert counts["tech"]["annotations"] == 1

    def test_increments_existing_counts(self) -> None:
        counts = _create_empty_counts()
        counts["lib"]["matplotlib"] = 5
        _increment_category_counts(counts, "s", "matplotlib", {}, {})
        assert counts["lib"]["matplotlib"] == 6


class TestSortCounts:
    """Tests for _sort_counts."""

    def test_sorts_by_count_descending(self) -> None:
        counts = {"lib": {"a": 1, "b": 3, "c": 2}}
        result = _sort_counts(counts)
        keys = list(result["lib"].keys())
        assert keys == ["b", "c", "a"]

    def test_alphabetical_on_tie(self) -> None:
        counts = {"lib": {"b": 2, "a": 2, "c": 2}}
        result = _sort_counts(counts)
        keys = list(result["lib"].keys())
        assert keys == ["a", "b", "c"]


class TestBuildCacheKey:
    """Tests for _build_cache_key."""

    def test_empty_groups(self) -> None:
        assert _build_cache_key([]) == "filter:all"

    def test_single_group(self) -> None:
        groups = [{"category": "lib", "values": ["matplotlib"]}]
        result = _build_cache_key(groups)
        assert result == "filter:lib=matplotlib"

    def test_multiple_groups_sorted(self) -> None:
        groups = [{"category": "plot", "values": ["scatter"]}, {"category": "lib", "values": ["matplotlib"]}]
        result = _build_cache_key(groups)
        assert result == "filter:lib=matplotlib:plot=scatter"

    def test_values_sorted(self) -> None:
        groups = [{"category": "lib", "values": ["seaborn", "matplotlib"]}]
        result = _build_cache_key(groups)
        assert result == "filter:lib=matplotlib,seaborn"

    def test_stable_key_different_order(self) -> None:
        groups1 = [{"category": "lib", "values": ["matplotlib"]}, {"category": "plot", "values": ["scatter"]}]
        groups2 = [{"category": "plot", "values": ["scatter"]}, {"category": "lib", "values": ["matplotlib"]}]
        assert _build_cache_key(groups1) == _build_cache_key(groups2)


class TestBuildSpecLookup:
    """Tests for _build_spec_lookup."""

    def test_with_impls(self) -> None:
        spec = MagicMock()
        spec.id = "scatter-basic"
        spec.tags = {"plot_type": ["scatter"]}
        spec.impls = [MagicMock()]

        result = _build_spec_lookup([spec])
        assert "scatter-basic" in result
        assert result["scatter-basic"]["tags"] == {"plot_type": ["scatter"]}

    def test_without_impls_excluded(self) -> None:
        spec = MagicMock()
        spec.id = "no-impls"
        spec.impls = []

        result = _build_spec_lookup([spec])
        assert "no-impls" not in result

    def test_none_tags_default_empty(self) -> None:
        spec = MagicMock()
        spec.id = "s1"
        spec.tags = None
        spec.impls = [MagicMock()]

        result = _build_spec_lookup([spec])
        assert result["s1"]["tags"] == {}


class TestBuildImplLookup:
    """Tests for _build_impl_lookup."""

    def test_with_preview_url(self) -> None:
        impl = MagicMock()
        impl.library_id = "matplotlib"
        impl.preview_url = "https://example.com/img.png"
        impl.impl_tags = {"techniques": ["annotations"]}

        spec = MagicMock()
        spec.id = "s1"
        spec.impls = [impl]

        result = _build_impl_lookup([spec])
        assert ("s1", "matplotlib") in result
        assert result[("s1", "matplotlib")] == {"techniques": ["annotations"]}

    def test_without_preview_url_excluded(self) -> None:
        impl = MagicMock()
        impl.library_id = "matplotlib"
        impl.preview_url = None

        spec = MagicMock()
        spec.id = "s1"
        spec.impls = [impl]

        result = _build_impl_lookup([spec])
        assert ("s1", "matplotlib") not in result

    def test_none_impl_tags_default_empty(self) -> None:
        impl = MagicMock()
        impl.library_id = "matplotlib"
        impl.preview_url = "https://example.com/img.png"
        impl.impl_tags = None

        spec = MagicMock()
        spec.id = "s1"
        spec.impls = [impl]

        result = _build_impl_lookup([spec])
        assert result[("s1", "matplotlib")] == {}


class TestCollectAllImages:
    """Tests for _collect_all_images."""

    def test_collects_images_with_preview(self) -> None:
        impl = MagicMock()
        impl.library_id = "matplotlib"
        impl.preview_url = "https://example.com/img.png"
        impl.preview_html = None
        impl.quality_score = 92.5

        spec = MagicMock()
        spec.id = "scatter-basic"
        spec.title = "Basic Scatter"
        spec.impls = [impl]

        result = _collect_all_images([spec])
        assert len(result) == 1
        assert result[0]["spec_id"] == "scatter-basic"
        assert result[0]["library"] == "matplotlib"
        assert result[0]["title"] == "Basic Scatter"

    def test_skips_without_preview(self) -> None:
        impl = MagicMock()
        impl.library_id = "matplotlib"
        impl.preview_url = None

        spec = MagicMock()
        spec.id = "s1"
        spec.impls = [impl]

        result = _collect_all_images([spec])
        assert len(result) == 0

    def test_skips_without_impls(self) -> None:
        spec = MagicMock()
        spec.id = "s1"
        spec.impls = []

        result = _collect_all_images([spec])
        assert len(result) == 0


class TestFilterImages:
    """Tests for _filter_images."""

    def test_no_filters_returns_all(self) -> None:
        images = [{"spec_id": "s1", "library": "matplotlib"}]
        spec_lookup = {"s1": {"tags": {}}}
        impl_lookup = {}
        result = _filter_images(images, [], spec_lookup, impl_lookup)
        assert len(result) == 1

    def test_filter_by_lib(self) -> None:
        images = [{"spec_id": "s1", "library": "matplotlib"}, {"spec_id": "s1", "library": "seaborn"}]
        spec_lookup = {"s1": {"tags": {}}}
        impl_lookup = {}
        groups = [{"category": "lib", "values": ["matplotlib"]}]
        result = _filter_images(images, groups, spec_lookup, impl_lookup)
        assert len(result) == 1
        assert result[0]["library"] == "matplotlib"


class TestCalculateGlobalCounts:
    """Tests for _calculate_global_counts."""

    def test_counts_all_images(self) -> None:
        impl1 = MagicMock()
        impl1.library_id = "matplotlib"
        impl1.preview_url = "https://example.com/img.png"
        impl1.impl_tags = {}

        impl2 = MagicMock()
        impl2.library_id = "seaborn"
        impl2.preview_url = "https://example.com/img2.png"
        impl2.impl_tags = {}

        spec = MagicMock()
        spec.id = "scatter-basic"
        spec.tags = {"plot_type": ["scatter"]}
        spec.impls = [impl1, impl2]

        result = _calculate_global_counts([spec])
        assert result["lib"]["matplotlib"] == 1
        assert result["lib"]["seaborn"] == 1
        assert result["plot"]["scatter"] == 2

    def test_empty_specs(self) -> None:
        result = _calculate_global_counts([])
        assert all(len(v) == 0 for v in result.values())


class TestCalculateContextualCounts:
    """Tests for _calculate_contextual_counts."""

    def test_counts_filtered_images(self) -> None:
        filtered = [{"spec_id": "s1", "library": "matplotlib"}]
        spec_tags = {"s1": {"plot_type": ["scatter"]}}
        impl_lookup = {}
        result = _calculate_contextual_counts(filtered, spec_tags, impl_lookup)
        assert result["lib"]["matplotlib"] == 1
        assert result["plot"]["scatter"] == 1


class TestCalculateOrCounts:
    """Tests for _calculate_or_counts."""

    def test_or_counts_for_single_group(self) -> None:
        filter_groups = [{"category": "lib", "values": ["matplotlib"]}]
        all_images = [{"spec_id": "s1", "library": "matplotlib"}, {"spec_id": "s1", "library": "seaborn"}]
        spec_id_to_tags = {"s1": {}}
        spec_lookup = {"s1": {"tags": {}}}
        impl_lookup = {}

        result = _calculate_or_counts(filter_groups, all_images, spec_id_to_tags, spec_lookup, impl_lookup)
        assert len(result) == 1
        # With no other groups, all images are included
        assert result[0]["matplotlib"] == 1
        assert result[0]["seaborn"] == 1
