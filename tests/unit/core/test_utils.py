"""Tests for core.utils module."""

from core.utils import strip_noqa_comments


class TestStripNoqaComments:
    """Tests for strip_noqa_comments function."""

    def test_removes_noqa_f403(self):
        """Should remove # noqa: F403 comments."""
        code = "from lets_plot import *  # noqa: F403"
        result = strip_noqa_comments(code)
        assert result == "from lets_plot import *"

    def test_removes_noqa_f405(self):
        """Should remove # noqa: F405 comments."""
        code = "from lets_plot.export import ggsave  # noqa: F405"
        result = strip_noqa_comments(code)
        assert result == "from lets_plot.export import ggsave"

    def test_removes_multiple_noqa_comments(self):
        """Should remove multiple noqa comments from code."""
        code = """from lets_plot import *  # noqa: F403
from lets_plot.export import ggsave  # noqa: F405
LetsPlot.setup_html()"""
        result = strip_noqa_comments(code)
        expected = """from lets_plot import *
from lets_plot.export import ggsave
LetsPlot.setup_html()"""
        assert result == expected

    def test_preserves_regular_comments(self):
        """Should keep regular comments that are not noqa."""
        code = """# This is a regular comment
x = 1  # inline comment
# Another comment"""
        result = strip_noqa_comments(code)
        assert result == code

    def test_preserves_noqa_in_strings(self):
        """Should remove noqa even in edge cases (regex doesn't check context)."""
        # Note: This tests current behavior - regex-based removal
        code = 'print("# noqa: F403")'
        result = strip_noqa_comments(code)
        # The regex will remove it even in strings - this is acceptable
        # as noqa comments in string literals are extremely rare
        assert "# noqa:" not in result

    def test_handles_none(self):
        """Should return None for None input."""
        assert strip_noqa_comments(None) is None

    def test_handles_empty_string(self):
        """Should return empty string for empty input."""
        assert strip_noqa_comments("") == ""

    def test_removes_noqa_with_multiple_codes(self):
        """Should remove noqa with multiple error codes."""
        code = "from module import *  # noqa: F401, F403"
        result = strip_noqa_comments(code)
        assert result == "from module import *"

    def test_removes_whitespace_before_noqa(self):
        """Should remove leading whitespace before noqa comment."""
        code = "import os    # noqa: F401"
        result = strip_noqa_comments(code)
        assert result == "import os"

    def test_handles_noqa_at_line_start(self):
        """Should handle noqa comment at start of line."""
        code = "# noqa: F401\nimport os"
        result = strip_noqa_comments(code)
        assert result == "\nimport os"

    def test_real_world_letsplot_example(self):
        """Test with real lets-plot import pattern."""
        code = '''""" anyplot.ai
scatter-basic: Basic Scatter Plot
"""

from lets_plot import *  # noqa: F403
from lets_plot.export import ggsave as export_ggsave  # noqa: F405

LetsPlot.setup_html()
'''
        result = strip_noqa_comments(code)
        assert "# noqa:" not in result
        assert "from lets_plot import *" in result
        assert "from lets_plot.export import ggsave as export_ggsave" in result
        assert "LetsPlot.setup_html()" in result
