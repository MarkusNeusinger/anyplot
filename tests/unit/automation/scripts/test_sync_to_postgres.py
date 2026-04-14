"""Tests for automation.scripts.sync_to_postgres module."""

from datetime import datetime
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from automation.scripts.sync_to_postgres import (
    _chunked,
    convert_datetimes_to_strings,
    main,
    parse_bullet_points,
    parse_library_metadata_yaml,
    parse_metadata_yaml,
    parse_spec_markdown,
    parse_timestamp,
    scan_plot_directory,
    sync_to_database,
)


class TestParseTimestamp:
    """Tests for parse_timestamp function."""

    def test_parse_datetime_object(self):
        dt = datetime(2025, 1, 10, 8, 0, 0)
        result = parse_timestamp(dt)
        assert result == dt
        assert result.tzinfo is None

    def test_parse_datetime_with_timezone(self):
        from datetime import timezone

        dt = datetime(2025, 1, 10, 8, 0, 0, tzinfo=timezone.utc)
        result = parse_timestamp(dt)
        assert result == datetime(2025, 1, 10, 8, 0, 0)
        assert result.tzinfo is None

    def test_parse_iso_string_with_z(self):
        result = parse_timestamp("2025-01-10T08:00:00Z")
        assert result == datetime(2025, 1, 10, 8, 0, 0)

    def test_parse_iso_string_with_offset(self):
        result = parse_timestamp("2025-01-10T08:00:00+00:00")
        assert result == datetime(2025, 1, 10, 8, 0, 0)

    def test_parse_invalid_string(self):
        result = parse_timestamp("not-a-date")
        assert result is None

    def test_parse_none(self):
        result = parse_timestamp(None)
        assert result is None

    def test_parse_integer_returns_none(self):
        result = parse_timestamp(12345)
        assert result is None


class TestParseBulletPoints:
    """Tests for parse_bullet_points function."""

    def test_parse_dash_bullets(self):
        text = "- Item 1\n- Item 2\n- Item 3"
        result = parse_bullet_points(text)
        assert result == ["Item 1", "Item 2", "Item 3"]

    def test_parse_asterisk_bullets(self):
        text = "* Item 1\n* Item 2"
        result = parse_bullet_points(text)
        assert result == ["Item 1", "Item 2"]

    def test_parse_mixed_bullets(self):
        text = "- Item 1\n* Item 2\n- Item 3"
        result = parse_bullet_points(text)
        assert result == ["Item 1", "Item 2", "Item 3"]

    def test_parse_with_leading_whitespace(self):
        text = "  - Item 1\n  - Item 2"
        result = parse_bullet_points(text)
        assert result == ["Item 1", "Item 2"]

    def test_parse_empty_string(self):
        result = parse_bullet_points("")
        assert result == []

    def test_parse_no_bullets(self):
        text = "Just some text\nwithout bullets"
        result = parse_bullet_points(text)
        assert result == []

    def test_parse_bullets_with_extra_spaces(self):
        text = "-   Item with spaces  \n-  Another item"
        result = parse_bullet_points(text)
        assert result == ["Item with spaces", "Another item"]


class TestConvertDatetimesToStrings:
    """Tests for convert_datetimes_to_strings function."""

    def test_convert_datetime(self):
        dt = datetime(2025, 1, 10, 8, 0, 0)
        result = convert_datetimes_to_strings(dt)
        assert result == "2025-01-10T08:00:00"

    def test_convert_string_unchanged(self):
        result = convert_datetimes_to_strings("test string")
        assert result == "test string"

    def test_convert_integer_unchanged(self):
        result = convert_datetimes_to_strings(42)
        assert result == 42

    def test_convert_nested_dict(self):
        dt = datetime(2025, 1, 10, 8, 0, 0)
        data = {"created": dt, "nested": {"updated": dt}, "name": "test"}
        result = convert_datetimes_to_strings(data)
        assert result["created"] == "2025-01-10T08:00:00"
        assert result["nested"]["updated"] == "2025-01-10T08:00:00"
        assert result["name"] == "test"

    def test_convert_list(self):
        dt = datetime(2025, 1, 10, 8, 0, 0)
        result = convert_datetimes_to_strings([dt, "string", 123])
        assert result == ["2025-01-10T08:00:00", "string", 123]

    def test_convert_empty_dict(self):
        result = convert_datetimes_to_strings({})
        assert result == {}

    def test_convert_empty_list(self):
        result = convert_datetimes_to_strings([])
        assert result == []


class TestParseSpecMarkdown:
    """Tests for parse_spec_markdown function."""

    def test_parse_complete_spec(self, tmp_path):
        spec_content = """# scatter-basic: Basic Scatter Plot

## Description
A simple scatter plot showing the relationship between two variables.

## Applications
- Correlation analysis
- Data exploration
- Trend identification

## Data
- X values (numeric)
- Y values (numeric)

## Notes
- Use alpha for overlapping points
- Consider adding a trend line
"""
        spec_dir = tmp_path / "scatter-basic"
        spec_dir.mkdir()
        spec_file = spec_dir / "specification.md"
        spec_file.write_text(spec_content)

        result = parse_spec_markdown(spec_file)

        assert result["id"] == "scatter-basic"
        assert result["title"] == "Basic Scatter Plot"
        assert "relationship between two variables" in result["description"]
        assert result["applications"] == ["Correlation analysis", "Data exploration", "Trend identification"]
        assert len(result["data"]) == 2
        assert result["notes"] == ["Use alpha for overlapping points", "Consider adding a trend line"]

    def test_parse_spec_without_notes(self, tmp_path):
        spec_content = """# bar-basic: Basic Bar Chart

## Description
A simple bar chart for comparing categories.

## Applications
- Category comparison

## Data
- Categories
- Values
"""
        spec_dir = tmp_path / "bar-basic"
        spec_dir.mkdir()
        spec_file = spec_dir / "specification.md"
        spec_file.write_text(spec_content)

        result = parse_spec_markdown(spec_file)

        assert result["id"] == "bar-basic"
        assert result["title"] == "Basic Bar Chart"
        assert result["notes"] == []

    def test_parse_spec_without_title_match(self, tmp_path):
        spec_content = """# Just a Title Without Colon

## Description
Some description.

## Applications
- One application

## Data
- Some data
"""
        spec_dir = tmp_path / "no-colon-title"
        spec_dir.mkdir()
        spec_file = spec_dir / "specification.md"
        spec_file.write_text(spec_content)

        result = parse_spec_markdown(spec_file)

        # Falls back to directory name
        assert result["id"] == "no-colon-title"
        assert result["title"] == "no-colon-title"

    def test_parse_spec_minimal_sections(self, tmp_path):
        """Test parsing spec with minimal content in sections."""
        spec_content = """# minimal-spec: Minimal Spec

## Description
Minimal description.

## Applications
- One app

## Data
- One data point
"""
        spec_dir = tmp_path / "minimal-spec"
        spec_dir.mkdir()
        spec_file = spec_dir / "specification.md"
        spec_file.write_text(spec_content)

        result = parse_spec_markdown(spec_file)

        assert result["id"] == "minimal-spec"
        assert result["description"] == "Minimal description."
        assert result["applications"] == ["One app"]
        assert result["data"] == ["One data point"]


class TestParseMetadataYaml:
    """Tests for parse_metadata_yaml function."""

    def test_parse_valid_spec_yaml(self, tmp_path):
        yaml_content = """spec_id: scatter-basic
title: Basic Scatter Plot
created: 2025-01-10T08:00:00Z
tags:
  plot_type: [scatter]
  domain: [statistics]
"""
        yaml_file = tmp_path / "specification.yaml"
        yaml_file.write_text(yaml_content)

        result = parse_metadata_yaml(yaml_file)

        assert result is not None
        assert result["spec_id"] == "scatter-basic"
        assert result["title"] == "Basic Scatter Plot"
        assert result["tags"]["plot_type"] == ["scatter"]

    def test_parse_with_specification_id(self, tmp_path):
        """Test backwards compatibility with specification_id key."""
        yaml_content = """specification_id: scatter-basic
title: Basic Scatter Plot
"""
        yaml_file = tmp_path / "spec.yaml"
        yaml_file.write_text(yaml_content)

        result = parse_metadata_yaml(yaml_file)

        assert result is not None
        assert result["specification_id"] == "scatter-basic"

    def test_parse_missing_spec_id_returns_none(self, tmp_path):
        yaml_content = """title: No Spec ID
tags:
  plot_type: [scatter]
"""
        yaml_file = tmp_path / "invalid.yaml"
        yaml_file.write_text(yaml_content)

        result = parse_metadata_yaml(yaml_file)

        assert result is None

    def test_parse_empty_file_returns_none(self, tmp_path):
        yaml_file = tmp_path / "empty.yaml"
        yaml_file.write_text("")

        result = parse_metadata_yaml(yaml_file)

        assert result is None

    def test_parse_invalid_yaml_returns_none(self, tmp_path):
        yaml_file = tmp_path / "invalid.yaml"
        yaml_file.write_text("not: valid: yaml: : here")

        result = parse_metadata_yaml(yaml_file)

        assert result is None


class TestParseLibraryMetadataYaml:
    """Tests for parse_library_metadata_yaml function."""

    def test_parse_valid_library_metadata(self, tmp_path):
        yaml_content = """library: matplotlib
specification_id: scatter-basic
quality_score: 92
preview_url: https://storage.example.com/plot.png
python_version: "3.13"
library_version: "3.10.0"
"""
        yaml_file = tmp_path / "matplotlib.yaml"
        yaml_file.write_text(yaml_content)

        result = parse_library_metadata_yaml(yaml_file)

        assert result is not None
        assert result["library"] == "matplotlib"
        assert result["quality_score"] == 92
        assert result["python_version"] == "3.13"

    def test_parse_missing_library_returns_none(self, tmp_path):
        yaml_content = """specification_id: scatter-basic
quality_score: 92
"""
        yaml_file = tmp_path / "no_library.yaml"
        yaml_file.write_text(yaml_content)

        result = parse_library_metadata_yaml(yaml_file)

        assert result is None

    def test_parse_with_review_section(self, tmp_path):
        yaml_content = """library: seaborn
specification_id: scatter-basic
quality_score: 88
review:
  strengths:
    - Clean code
    - Good colors
  weaknesses:
    - Missing grid
"""
        yaml_file = tmp_path / "seaborn.yaml"
        yaml_file.write_text(yaml_content)

        result = parse_library_metadata_yaml(yaml_file)

        assert result is not None
        assert result["review"]["strengths"] == ["Clean code", "Good colors"]
        assert result["review"]["weaknesses"] == ["Missing grid"]


class TestScanPlotDirectory:
    """Tests for scan_plot_directory function."""

    def test_scan_complete_directory(self, tmp_path):
        # Create complete plot directory structure
        plot_dir = tmp_path / "scatter-basic"
        plot_dir.mkdir()

        # specification.md
        (plot_dir / "specification.md").write_text("""# scatter-basic: Basic Scatter Plot

## Description
A simple scatter plot.

## Applications
- Correlation analysis

## Data
- X values
- Y values
""")

        # specification.yaml
        (plot_dir / "specification.yaml").write_text("""spec_id: scatter-basic
title: Basic Scatter Plot
created: 2025-01-10T08:00:00Z
issue: 42
suggested: testuser
tags:
  plot_type: [scatter]
  domain: [statistics]
""")

        # implementations/
        impl_dir = plot_dir / "implementations"
        impl_dir.mkdir()
        (impl_dir / "matplotlib.py").write_text('''"""anyplot.ai"""
import matplotlib.pyplot as plt
plt.plot([1, 2, 3])
plt.savefig("plot.png")
''')

        # metadata/
        meta_dir = plot_dir / "metadata"
        meta_dir.mkdir()
        (meta_dir / "matplotlib.yaml").write_text("""library: matplotlib
specification_id: scatter-basic
quality_score: 92
preview_url: https://storage.example.com/plot.png
python_version: "3.13"
library_version: "3.10.0"
review:
  strengths:
    - Clean code
  weaknesses: []
""")

        result = scan_plot_directory(plot_dir)

        assert result is not None
        assert result["spec"]["id"] == "scatter-basic"
        assert result["spec"]["title"] == "Basic Scatter Plot"
        assert result["spec"]["issue"] == 42
        assert result["spec"]["suggested"] == "testuser"
        assert len(result["implementations"]) == 1

        impl = result["implementations"][0]
        assert impl["spec_id"] == "scatter-basic"
        assert impl["library_id"] == "matplotlib"
        assert impl["quality_score"] == 92
        assert impl["python_version"] == "3.13"
        assert impl["review_strengths"] == ["Clean code"]

    def test_scan_missing_spec_returns_none(self, tmp_path):
        plot_dir = tmp_path / "empty-plot"
        plot_dir.mkdir()

        result = scan_plot_directory(plot_dir)

        assert result is None

    def test_scan_legacy_spec_md(self, tmp_path):
        """Test scanning with legacy spec.md filename."""
        plot_dir = tmp_path / "legacy-plot"
        plot_dir.mkdir()

        # Use legacy filename
        (plot_dir / "spec.md").write_text("""# legacy-plot: Legacy Plot

## Description
A legacy format plot.

## Applications
- Testing

## Data
- Values
""")

        result = scan_plot_directory(plot_dir)

        assert result is not None
        assert result["spec"]["id"] == "legacy-plot"
        assert result["spec"]["title"] == "Legacy Plot"

    def test_scan_skips_underscore_files(self, tmp_path):
        """Test that files starting with underscore are skipped."""
        plot_dir = tmp_path / "test-plot"
        plot_dir.mkdir()

        (plot_dir / "specification.md").write_text("""# test-plot: Test

## Description
Test plot.

## Applications
- Testing

## Data
- Values
""")

        impl_dir = plot_dir / "implementations"
        impl_dir.mkdir()
        (impl_dir / "matplotlib.py").write_text("# matplotlib")
        (impl_dir / "_template.py").write_text("# template - should be skipped")

        result = scan_plot_directory(plot_dir)

        assert result is not None
        assert len(result["implementations"]) == 1
        assert result["implementations"][0]["library_id"] == "matplotlib"

    def test_scan_without_implementations(self, tmp_path):
        """Test scanning a plot with only specification, no implementations."""
        plot_dir = tmp_path / "spec-only"
        plot_dir.mkdir()

        (plot_dir / "specification.md").write_text("""# spec-only: Spec Only

## Description
A specification without implementations.

## Applications
- Future work

## Data
- TBD
""")

        (plot_dir / "specification.yaml").write_text("""spec_id: spec-only
title: Spec Only
created: 2025-01-10T08:00:00Z
tags:
  plot_type: [scatter]
""")

        result = scan_plot_directory(plot_dir)

        assert result is not None
        assert result["spec"]["id"] == "spec-only"
        assert result["implementations"] == []

    def test_scan_with_legacy_nested_current(self, tmp_path):
        """Test scanning with legacy current: nested structure in metadata."""
        plot_dir = tmp_path / "legacy-nested"
        plot_dir.mkdir()

        (plot_dir / "specification.md").write_text("""# legacy-nested: Legacy Nested

## Description
Test.

## Applications
- Test

## Data
- Test
""")

        impl_dir = plot_dir / "implementations"
        impl_dir.mkdir()
        (impl_dir / "matplotlib.py").write_text("# code")

        meta_dir = plot_dir / "metadata"
        meta_dir.mkdir()
        (meta_dir / "matplotlib.yaml").write_text("""library: matplotlib
specification_id: legacy-nested
current:
  generated_at: 2025-01-10T08:00:00Z
  quality_score: 85
  python_version: "3.12"
""")

        result = scan_plot_directory(plot_dir)

        assert result is not None
        impl = result["implementations"][0]
        assert impl["quality_score"] == 85
        assert impl["python_version"] == "3.12"

    def test_scan_with_legacy_metadata_yaml(self, tmp_path):
        """Test scanning with legacy metadata.yaml in spec directory."""
        plot_dir = tmp_path / "legacy-format"
        plot_dir.mkdir()

        (plot_dir / "specification.md").write_text("""# legacy-format: Legacy Format

## Description
Test legacy format.

## Applications
- Testing

## Data
- Values
""")

        # Legacy metadata.yaml (not specification.yaml)
        (plot_dir / "metadata.yaml").write_text("""spec_id: legacy-format
title: Legacy Format Title
created: 2025-01-10T08:00:00Z
tags:
  plot_type: [scatter]
implementations:
  matplotlib:
    quality_score: 80
    python_version: "3.11"
""")

        impl_dir = plot_dir / "implementations"
        impl_dir.mkdir()
        (impl_dir / "matplotlib.py").write_text("# matplotlib code")

        result = scan_plot_directory(plot_dir)

        assert result is not None
        assert result["spec"]["title"] == "Legacy Format Title"
        impl = result["implementations"][0]
        assert impl["quality_score"] == 80
        assert impl["python_version"] == "3.11"

    def test_scan_with_extended_review_data(self, tmp_path):
        """Test scanning with extended review data (issue #2845)."""
        plot_dir = tmp_path / "extended-review"
        plot_dir.mkdir()

        (plot_dir / "specification.md").write_text("""# extended-review: Extended Review

## Description
Test extended review data.

## Applications
- Testing

## Data
- Values
""")

        (plot_dir / "specification.yaml").write_text("""spec_id: extended-review
title: Extended Review Test
""")

        impl_dir = plot_dir / "implementations"
        impl_dir.mkdir()
        (impl_dir / "matplotlib.py").write_text("# matplotlib code")

        meta_dir = plot_dir / "metadata"
        meta_dir.mkdir()
        (meta_dir / "matplotlib.yaml").write_text("""library: matplotlib
specification_id: extended-review
quality_score: 88
review:
  image_description: |
    The plot shows a scatter chart with blue points.
  criteria_checklist:
    visual_quality:
      score: 36
      max: 40
  verdict: APPROVED
  strengths:
    - Clean layout
  weaknesses:
    - Missing grid
""")

        result = scan_plot_directory(plot_dir)

        assert result is not None
        impl = result["implementations"][0]
        assert "scatter chart" in impl["review_image_description"]
        assert impl["review_criteria_checklist"]["visual_quality"]["score"] == 36
        assert impl["review_verdict"] == "APPROVED"


class TestChunked:
    """Tests for _chunked helper function."""

    def test_chunked_exact_division(self):
        result = list(_chunked([1, 2, 3, 4], 2))
        assert result == [[1, 2], [3, 4]]

    def test_chunked_with_remainder(self):
        result = list(_chunked([1, 2, 3, 4, 5], 2))
        assert result == [[1, 2], [3, 4], [5]]

    def test_chunked_empty(self):
        result = list(_chunked([], 5))
        assert result == []

    def test_chunked_single_element(self):
        result = list(_chunked([1], 5))
        assert result == [[1]]

    def test_chunked_size_larger_than_input(self):
        result = list(_chunked([1, 2], 10))
        assert result == [[1, 2]]


class TestSyncToDatabase:
    """Tests for sync_to_database function."""

    def test_sync_specs_and_impls(self):
        """Should sync specs and implementations to database."""
        mock_session = MagicMock()
        mock_session.execute = MagicMock()
        mock_session.commit = MagicMock()

        # Mock select results for removal check
        mock_result = MagicMock()
        mock_result.fetchall.return_value = []
        mock_session.execute.return_value = mock_result

        plots = [
            {
                "spec": {
                    "id": "scatter-basic",
                    "title": "Basic Scatter",
                    "description": "A scatter plot",
                    "applications": ["testing"],
                    "data": ["x", "y"],
                    "notes": [],
                    "tags": {"plot_type": ["scatter"]},
                    "created": datetime(2025, 1, 10),
                    "updated": None,
                    "issue": 42,
                    "suggested": "testuser",
                },
                "implementations": [
                    {
                        "spec_id": "scatter-basic",
                        "library_id": "matplotlib",
                        "code": "import matplotlib",
                        "preview_url": "https://example.com/plot.png",
                        "preview_html": None,
                        "python_version": "3.13",
                        "library_version": "3.10.0",
                        "generated_at": datetime(2025, 1, 10),
                        "updated": None,
                        "generated_by": "claude",
                        "workflow_run": 123,
                        "issue": 42,
                        "quality_score": 92,
                        "review_strengths": ["Clean code"],
                        "review_weaknesses": [],
                        "review_image_description": None,
                        "review_criteria_checklist": None,
                        "review_verdict": None,
                        "impl_tags": None,
                    }
                ],
            }
        ]

        stats = sync_to_database(mock_session, plots)

        assert stats["specs_synced"] == 1
        assert stats["impls_synced"] == 1
        assert stats["specs_removed"] == 0
        assert stats["impls_removed"] == 0
        mock_session.commit.assert_called_once()

    def test_sync_calls_commit(self):
        """Should commit session after sync."""
        mock_session = MagicMock()
        mock_result = MagicMock()
        mock_result.fetchall.return_value = []
        mock_session.execute.return_value = mock_result

        plots = [
            {
                "spec": {
                    "id": "test-spec",
                    "title": "Test",
                    "description": "",
                    "applications": [],
                    "data": [],
                    "notes": [],
                    "tags": None,
                    "created": None,
                    "updated": None,
                    "issue": None,
                    "suggested": None,
                },
                "implementations": [],
            }
        ]

        sync_to_database(mock_session, plots)

        mock_session.commit.assert_called_once()

    def test_sync_empty_plots(self):
        """Should handle empty plots list."""
        mock_session = MagicMock()
        mock_result = MagicMock()
        mock_result.fetchall.return_value = []
        mock_session.execute.return_value = mock_result

        stats = sync_to_database(mock_session, [])

        assert stats["specs_synced"] == 0
        assert stats["impls_synced"] == 0
        mock_session.commit.assert_called_once()

    def test_sync_with_extended_review_data(self):
        """Should sync extended review data fields."""
        mock_session = MagicMock()
        mock_result = MagicMock()
        mock_result.fetchall.return_value = []
        mock_session.execute.return_value = mock_result

        plots = [
            {
                "spec": {
                    "id": "test-spec",
                    "title": "Test",
                    "description": "",
                    "applications": [],
                    "data": [],
                    "notes": [],
                    "tags": None,
                    "created": None,
                    "updated": None,
                    "issue": None,
                    "suggested": None,
                },
                "implementations": [
                    {
                        "spec_id": "test-spec",
                        "library_id": "matplotlib",
                        "code": "code",
                        "preview_url": None,
                        "preview_html": None,
                        "python_version": None,
                        "library_version": None,
                        "generated_at": None,
                        "updated": None,
                        "generated_by": None,
                        "workflow_run": None,
                        "issue": None,
                        "quality_score": 90,
                        "review_strengths": ["Good"],
                        "review_weaknesses": ["Bad"],
                        "review_image_description": "A plot with points",
                        "review_criteria_checklist": {"visual": {"score": 35}},
                        "review_verdict": "APPROVED",
                        "impl_tags": None,
                    }
                ],
            }
        ]

        stats = sync_to_database(mock_session, plots)

        assert stats["impls_synced"] == 1
        mock_session.commit.assert_called_once()

    def test_sync_batches_multiple_specs_and_impls(self):
        """Should batch multiple specs and impls, calling execute fewer times than row count."""
        mock_session = MagicMock()
        mock_result = MagicMock()
        mock_result.fetchall.return_value = []
        mock_session.execute.return_value = mock_result

        def _make_plot(spec_id):
            return {
                "spec": {
                    "id": spec_id,
                    "title": f"Title {spec_id}",
                    "description": "",
                    "applications": [],
                    "data": [],
                    "notes": [],
                    "tags": None,
                    "created": None,
                    "updated": None,
                    "issue": None,
                    "suggested": None,
                },
                "implementations": [
                    {
                        "spec_id": spec_id,
                        "library_id": lib,
                        "code": "code",
                        "preview_url": None,
                        "preview_html": None,
                        "python_version": None,
                        "library_version": None,
                        "generated_at": None,
                        "updated": None,
                        "generated_by": None,
                        "workflow_run": None,
                        "issue": None,
                        "quality_score": None,
                        "review_strengths": [],
                        "review_weaknesses": [],
                        "review_image_description": None,
                        "review_criteria_checklist": None,
                        "review_verdict": None,
                        "impl_tags": None,
                    }
                    for lib in ["matplotlib", "seaborn", "plotly"]
                ],
            }

        plots = [_make_plot(f"spec-{i}") for i in range(5)]

        stats = sync_to_database(mock_session, plots)

        assert stats["specs_synced"] == 5
        assert stats["impls_synced"] == 15
        mock_session.commit.assert_called_once()
        # Batched: 1 library seed + 1 spec chunk + 1 impl chunk + 2 removal selects = 5
        # (much fewer than 5+15+2 = 22 calls in the old per-row approach)
        assert mock_session.execute.call_count == 5


class TestMain:
    """Tests for main function."""

    def test_main_no_database_configured(self):
        """Should return 1 when no database is configured."""
        with patch("automation.scripts.sync_to_postgres.is_db_configured", return_value=False):
            result = main()

        assert result == 1

    def test_main_success(self, tmp_path):
        """Should return 0 on successful sync."""
        # Create a minimal plot directory
        plots_dir = tmp_path / "plots"
        plots_dir.mkdir()
        plot_dir = plots_dir / "test-plot"
        plot_dir.mkdir()

        (plot_dir / "specification.md").write_text("""# test-plot: Test Plot

## Description
Test.

## Applications
- Test

## Data
- Test
""")

        mock_session = MagicMock()
        mock_result = MagicMock()
        mock_result.fetchall.return_value = []
        mock_session.execute.return_value = mock_result

        with (
            patch("automation.scripts.sync_to_postgres.is_db_configured", return_value=True),
            patch("automation.scripts.sync_to_postgres.PLOTS_DIR", plots_dir),
            patch("automation.scripts.sync_to_postgres.init_db_sync"),
            patch("automation.scripts.sync_to_postgres.get_db_context_sync") as mock_ctx,
            patch("automation.scripts.sync_to_postgres.close_db_sync"),
        ):
            mock_ctx.return_value.__enter__ = MagicMock(return_value=mock_session)
            mock_ctx.return_value.__exit__ = MagicMock(return_value=None)

            result = main()

        assert result == 0

    def test_main_exception_returns_1(self, tmp_path):
        """Should return 1 when sync fails."""
        plots_dir = tmp_path / "plots"
        plots_dir.mkdir()

        with (
            patch("automation.scripts.sync_to_postgres.is_db_configured", return_value=True),
            patch("automation.scripts.sync_to_postgres.PLOTS_DIR", plots_dir),
            patch("automation.scripts.sync_to_postgres.init_db_sync", side_effect=Exception("DB error")),
            patch("automation.scripts.sync_to_postgres.close_db_sync"),
        ):
            result = main()

        assert result == 1

    def test_main_skips_hidden_directories(self, tmp_path):
        """Should skip directories starting with dot."""
        plots_dir = tmp_path / "plots"
        plots_dir.mkdir()

        # Create hidden directory
        hidden_dir = plots_dir / ".hidden"
        hidden_dir.mkdir()
        (hidden_dir / "specification.md").write_text("# hidden")

        # Create normal directory
        normal_dir = plots_dir / "normal-plot"
        normal_dir.mkdir()
        (normal_dir / "specification.md").write_text("""# normal-plot: Normal

## Description
Normal plot.

## Applications
- Test

## Data
- Test
""")

        mock_session = MagicMock()
        mock_result = MagicMock()
        mock_result.fetchall.return_value = []
        mock_session.execute.return_value = mock_result

        with (
            patch("automation.scripts.sync_to_postgres.is_db_configured", return_value=True),
            patch("automation.scripts.sync_to_postgres.PLOTS_DIR", plots_dir),
            patch("automation.scripts.sync_to_postgres.init_db_sync"),
            patch("automation.scripts.sync_to_postgres.get_db_context_sync") as mock_ctx,
            patch("automation.scripts.sync_to_postgres.close_db_sync"),
        ):
            mock_ctx.return_value.__enter__ = MagicMock(return_value=mock_session)
            mock_ctx.return_value.__exit__ = MagicMock(return_value=None)

            result = main()

        assert result == 0

    def test_main_skips_non_directories(self, tmp_path):
        """Should skip files in plots directory."""
        plots_dir = tmp_path / "plots"
        plots_dir.mkdir()

        # Create a file (not directory)
        (plots_dir / "README.md").write_text("# Plots")

        # Create normal directory
        normal_dir = plots_dir / "test-plot"
        normal_dir.mkdir()
        (normal_dir / "specification.md").write_text("""# test-plot: Test

## Description
Test.

## Applications
- Test

## Data
- Test
""")

        mock_session = MagicMock()
        mock_result = MagicMock()
        mock_result.fetchall.return_value = []
        mock_session.execute.return_value = mock_result

        with (
            patch("automation.scripts.sync_to_postgres.is_db_configured", return_value=True),
            patch("automation.scripts.sync_to_postgres.PLOTS_DIR", plots_dir),
            patch("automation.scripts.sync_to_postgres.init_db_sync"),
            patch("automation.scripts.sync_to_postgres.get_db_context_sync") as mock_ctx,
            patch("automation.scripts.sync_to_postgres.close_db_sync"),
        ):
            mock_ctx.return_value.__enter__ = MagicMock(return_value=mock_session)
            mock_ctx.return_value.__exit__ = MagicMock(return_value=None)

            result = main()

        assert result == 0
