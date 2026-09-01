"""Tests for automation.benchmark.prompting."""

import pytest

from automation.benchmark.prompting import build_generation_prompt, build_repair_prompt, extract_code_block


@pytest.fixture
def repo_root(tmp_path):
    """Minimal repo layout with the four prompt inputs the builder reads."""
    (tmp_path / "prompts" / "library").mkdir(parents=True)
    (tmp_path / "plots" / "scatter-basic").mkdir(parents=True)
    (tmp_path / "prompts" / "plot-generator.md").write_text("BASE RULES", encoding="utf-8")
    (tmp_path / "prompts" / "default-style-guide.md").write_text("STYLE GUIDE", encoding="utf-8")
    (tmp_path / "prompts" / "library" / "matplotlib.md").write_text("LIBRARY RULES", encoding="utf-8")
    (tmp_path / "plots" / "scatter-basic" / "specification.md").write_text("THE SPEC", encoding="utf-8")
    return tmp_path


class TestBuildGenerationPrompt:
    def test_includes_all_inputs_and_contract(self, repo_root):
        system, user = build_generation_prompt(repo_root, "scatter-basic", "matplotlib")

        assert "data-visualization engineer" in system
        for fragment in ("BASE RULES", "STYLE GUIDE", "LIBRARY RULES", "THE SPEC"):
            assert fragment in user
        # Single-shot contract essentials
        assert "ANYPLOT_THEME" in user
        assert "3200x1800" in user
        assert "ONE fenced code block" in user

    def test_missing_spec_raises(self, repo_root):
        with pytest.raises(FileNotFoundError, match="specification.md"):
            build_generation_prompt(repo_root, "does-not-exist", "matplotlib")

    def test_missing_library_prompt_raises(self, repo_root):
        with pytest.raises(FileNotFoundError, match="nosuchlib.md"):
            build_generation_prompt(repo_root, "scatter-basic", "nosuchlib")


class TestBuildRepairPrompt:
    def test_appends_code_and_error(self):
        repaired = build_repair_prompt("BASE", "import x", "Traceback: boom")
        assert repaired.startswith("BASE")
        assert "import x" in repaired
        assert "Traceback: boom" in repaired
        assert "Previous attempt failed" in repaired

    def test_error_is_truncated_to_tail(self):
        long_error = "x" * 10000 + "THE END"
        repaired = build_repair_prompt("BASE", "code", long_error)
        assert "THE END" in repaired
        assert len(repaired) < 10000


class TestExtractCodeBlock:
    def test_python_fence(self):
        text = "Here you go:\n```python\nimport matplotlib\n```\nEnjoy!"
        assert extract_code_block(text) == "import matplotlib"

    def test_bare_fence(self):
        assert extract_code_block("```\nimport numpy\n```") == "import numpy"

    def test_longest_block_wins(self):
        text = "```python\nprint('short')\n```\n\n```python\nimport pandas\nimport numpy\nprint('real one')\n```"
        assert "real one" in extract_code_block(text)
        assert "short" not in extract_code_block(text)

    def test_unfenced_code_falls_back_to_raw_text(self):
        text = "import matplotlib.pyplot as plt\nplt.plot([1, 2])"
        assert extract_code_block(text) == text

    def test_prose_without_code_raises(self):
        with pytest.raises(ValueError, match="No fenced code block"):
            extract_code_block("I am sorry, I cannot help with that.")
