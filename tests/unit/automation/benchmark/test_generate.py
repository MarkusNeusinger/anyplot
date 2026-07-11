"""Tests for automation.benchmark.generate CLI helpers and main loop."""

import pytest
import yaml

from automation.benchmark import generate as generate_mod
from automation.benchmark.generate import PYTHON_LIBRARIES, accumulate_tokens, main, parse_args, slugify_model
from automation.benchmark.vertex_client import GenerationResult


# Self-contained "generated implementation" that satisfies the runner contract
# without importing any plotting library.
WORKING_CODE = """
import os
from PIL import Image
theme = os.getenv("ANYPLOT_THEME", "light")
Image.new("RGB", (64, 64)).save(f"plot-{theme}.png")
"""


class FakeVertexClient:
    """Stands in for VertexClient; yields scripted responses per attempt."""

    responses: list[str] = []

    def __init__(self, **kwargs):
        self.init_kwargs = kwargs
        self._iter = iter(type(self).responses)

    def generate(self, model, system, prompt, max_tokens, temperature):
        item = next(self._iter)
        if isinstance(item, Exception):
            raise item
        return GenerationResult(
            text=item, model=model, provider="openapi", latency_seconds=0.5, input_tokens=10, output_tokens=5
        )


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


class TestAccumulateTokens:
    def test_unreported_usage_stays_none(self):
        assert accumulate_tokens(None, None) is None

    def test_first_report_starts_from_zero(self):
        assert accumulate_tokens(None, 120) == 120

    def test_reports_accumulate(self):
        assert accumulate_tokens(120, 80) == 200

    def test_missing_report_keeps_prior_total(self):
        assert accumulate_tokens(120, None) == 120

    def test_zero_is_a_real_report_not_unknown(self):
        assert accumulate_tokens(None, 0) == 0


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

    def test_non_positive_numeric_args_rejected(self):
        base = ["--spec-id", "scatter-basic", "--library", "matplotlib", "--model", "gemini-2.5-pro"]
        for flag in ("--max-attempts", "--max-tokens", "--render-timeout"):
            for bad in ("0", "-1"):
                with pytest.raises(SystemExit):
                    parse_args([*base, flag, bad])


class TestMain:
    """End-to-end main() runs against the real repo prompts/spec with a fake client."""

    def _run(self, tmp_path, monkeypatch, responses, max_attempts=3):
        FakeVertexClient.responses = responses
        monkeypatch.setattr(generate_mod, "VertexClient", FakeVertexClient)
        exit_code = main(
            [
                "--spec-id",
                "scatter-basic",
                "--library",
                "matplotlib",
                "--model",
                "google/gemini-2.5-pro",
                "--output-dir",
                str(tmp_path),
                "--max-attempts",
                str(max_attempts),
            ]
        )
        result_file = tmp_path / "scatter-basic" / "matplotlib" / "google-gemini-2-5-pro" / "result.yaml"
        return exit_code, (yaml.safe_load(result_file.read_text(encoding="utf-8")) if result_file.is_file() else None)

    def test_successful_run_writes_result_yaml(self, tmp_path, monkeypatch):
        exit_code, result = self._run(tmp_path, monkeypatch, [f"```python\n{WORKING_CODE}\n```"])
        assert exit_code == 0
        assert result["success"] is True
        assert result["attempts"] == 1
        assert result["code_fenced"] is True
        assert result["canvas_ok"] is False  # 64x64 misses the canonical canvas
        assert result["input_tokens"] == 10
        assert result["output_tokens"] == 5
        assert result["provider"] == "openapi"
        assert result["error"] is None
        impl = tmp_path / "scatter-basic" / "matplotlib" / "google-gemini-2-5-pro" / "matplotlib.py"
        assert impl.is_file()

    def test_extraction_failure_retries_then_succeeds(self, tmp_path, monkeypatch):
        exit_code, result = self._run(
            tmp_path, monkeypatch, ["I cannot find any code to write here.", f"```python\n{WORKING_CODE}\n```"]
        )
        assert exit_code == 0
        assert result["success"] is True
        assert result["attempts"] == 2
        # Token usage accumulated across both attempts
        assert result["input_tokens"] == 20

    def test_provider_error_is_recorded_and_fails(self, tmp_path, monkeypatch):
        exit_code, result = self._run(tmp_path, monkeypatch, [RuntimeError("Vertex says no")])
        assert exit_code == 1
        assert result["success"] is False
        assert "Vertex says no" in result["error"]
        assert result["attempts"] == 1

    def test_render_failure_exhausts_attempts(self, tmp_path, monkeypatch):
        broken = "```python\nraise SystemExit('render boom')\n```"
        exit_code, result = self._run(tmp_path, monkeypatch, [broken, broken], max_attempts=2)
        assert exit_code == 1
        assert result["success"] is False
        assert result["attempts"] == 2
        assert "render boom" in result["error"]
