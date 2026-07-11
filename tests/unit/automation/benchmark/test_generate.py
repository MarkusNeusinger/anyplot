"""Tests for automation.benchmark.generate CLI helpers."""

import pytest

from automation.benchmark.generate import PYTHON_LIBRARIES, parse_args, slugify_model


class TestSlugifyModel:
    def test_publisher_prefixed_id(self):
        assert slugify_model("google/gemini-2.5-pro") == "google-gemini-2-5-pro"

    def test_versioned_claude_id(self):
        assert slugify_model("claude-sonnet-4-5@20250929") == "claude-sonnet-4-5-20250929"

    def test_uppercase_is_lowered(self):
        assert slugify_model("MistralAI/Mistral-Large-2411") == "mistralai-mistral-large-2411"


class TestPythonLibraries:
    def test_only_python_libraries_are_allowed(self):
        assert "matplotlib" in PYTHON_LIBRARIES
        assert "seaborn" in PYTHON_LIBRARIES
        # Non-Python catalogue entries are excluded from benchmark v1
        for non_python in ("ggplot2", "makie", "chartjs", "d3", "echarts", "muix"):
            assert non_python not in PYTHON_LIBRARIES


class TestParseArgs:
    def test_defaults(self):
        args = parse_args(["--spec-id", "scatter-basic", "--library", "matplotlib", "--model", "gemini-2.5-pro"])
        assert args.max_attempts == 3
        assert args.location == "us-central1"
        assert args.anthropic_location == "us-east5"
        assert args.output_dir == "benchmark-results"

    def test_non_python_library_rejected(self):
        with pytest.raises(SystemExit):
            parse_args(["--spec-id", "scatter-basic", "--library", "ggplot2", "--model", "gemini-2.5-pro"])
