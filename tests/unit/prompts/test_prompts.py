"""
Tests for AI prompts structure and content validation.

Best practices for prompt testing:
1. File existence - All expected prompts exist
2. Required sections - Core sections are present (## Role, ## Task, etc.)
3. No placeholders - No TODO, FIXME, or {placeholder} left behind
4. Cross-references valid - Referenced files exist
5. Consistent formatting - Markdown is well-formed
"""

import re
from pathlib import Path

import pytest


# Base paths
PROMPTS_DIR = Path(__file__).parent.parent.parent.parent / "prompts"
LIBRARY_PROMPTS_DIR = PROMPTS_DIR / "library"

# Expected files
EXPECTED_BASE_PROMPTS = [
    "plot-generator.md",
    "quality-criteria.md",
    "quality-evaluator.md",
    "spec-id-generator.md",
    "default-style-guide.md",
]

EXPECTED_LIBRARY_PROMPTS = [
    "matplotlib.md",
    "seaborn.md",
    "plotly.md",
    "bokeh.md",
    "altair.md",
    "plotnine.md",
    "pygal.md",
    "highcharts.md",
    "letsplot.md",
]

STATIC_LIBRARIES = ["matplotlib.md", "seaborn.md", "plotnine.md"]


class TestPromptFileExistence:
    """Test that all expected prompt files exist."""

    def test_prompts_directory_exists(self) -> None:
        """Prompts directory should exist."""
        assert PROMPTS_DIR.exists(), f"Prompts directory not found: {PROMPTS_DIR}"
        assert PROMPTS_DIR.is_dir(), f"Prompts path is not a directory: {PROMPTS_DIR}"

    def test_library_directory_exists(self) -> None:
        """Library prompts subdirectory should exist."""
        assert LIBRARY_PROMPTS_DIR.exists(), f"Library prompts not found: {LIBRARY_PROMPTS_DIR}"
        assert LIBRARY_PROMPTS_DIR.is_dir()

    @pytest.mark.parametrize("filename", EXPECTED_BASE_PROMPTS)
    def test_base_prompt_exists(self, filename: str) -> None:
        """Each base prompt file should exist."""
        filepath = PROMPTS_DIR / filename
        assert filepath.exists(), f"Missing base prompt: {filename}"

    @pytest.mark.parametrize("filename", EXPECTED_LIBRARY_PROMPTS)
    def test_library_prompt_exists(self, filename: str) -> None:
        """Each library-specific prompt file should exist."""
        filepath = LIBRARY_PROMPTS_DIR / filename
        assert filepath.exists(), f"Missing library prompt: {filename}"


class TestPromptStructure:
    """Test prompt structure and required sections."""

    @pytest.fixture
    def plot_generator_content(self) -> str:
        """Load plot-generator.md content."""
        return (PROMPTS_DIR / "plot-generator.md").read_text()

    @pytest.fixture
    def quality_criteria_content(self) -> str:
        """Load quality-criteria.md content."""
        return (PROMPTS_DIR / "quality-criteria.md").read_text()

    @pytest.fixture
    def quality_evaluator_content(self) -> str:
        """Load quality-evaluator.md content."""
        return (PROMPTS_DIR / "quality-evaluator.md").read_text()

    def test_plot_generator_has_required_sections(self, plot_generator_content: str) -> None:
        """Plot generator should have Role, Task, Output sections."""
        # Core sections at level 2
        required_sections = ["## Role", "## Task", "## Output"]
        for section in required_sections:
            assert section in plot_generator_content, f"Missing section: {section}"
        # Rules can be at level 2 or 3 (### Rules under ## Output)
        assert "Rules" in plot_generator_content, "Missing Rules section"

    def test_plot_generator_has_code_template(self, plot_generator_content: str) -> None:
        """Plot generator should include a code template."""
        assert "```python" in plot_generator_content, "Missing Python code template"
        # KISS style: simple scripts with comments, not functions
        assert "plt.savefig" in plot_generator_content, "Missing plot save example"

    def test_plot_generator_has_fake_functionality_section(self, plot_generator_content: str) -> None:
        """Plot generator should have Fake Functionality section."""
        assert "## Fake Functionality is Forbidden" in plot_generator_content
        assert "NOT_FEASIBLE" in plot_generator_content
        assert "Feasibility Pre-Check" in plot_generator_content

    def test_plot_generator_has_code_style_section(self, plot_generator_content: str) -> None:
        """Plot generator should have Code Style section."""
        assert "## Code Style: Clean and Pythonic" in plot_generator_content
        assert "Variable Naming" in plot_generator_content

    def test_quality_criteria_has_scoring_section(self, quality_criteria_content: str) -> None:
        """Quality criteria should have scoring information."""
        assert "## Stage 2: Quality Scoring" in quality_criteria_content
        assert "90" in quality_criteria_content, "Pass threshold (90) not mentioned"

    def test_quality_criteria_has_six_categories(self, quality_criteria_content: str) -> None:
        """Quality criteria should have all 6 scoring categories."""
        assert "## Visual Quality" in quality_criteria_content
        assert "## Design Excellence" in quality_criteria_content
        assert "## Spec Compliance" in quality_criteria_content
        assert "## Data Quality" in quality_criteria_content
        assert "## Code Quality" in quality_criteria_content
        assert "## Library Mastery" in quality_criteria_content

    def test_quality_criteria_has_ar08(self, quality_criteria_content: str) -> None:
        """Quality criteria should include AR-08 FAKE_FUNCTIONALITY."""
        assert "AR-08" in quality_criteria_content
        assert "FAKE_FUNCTIONALITY" in quality_criteria_content

    def test_quality_criteria_has_design_excellence(self, quality_criteria_content: str) -> None:
        """Quality criteria should have Design Excellence criteria."""
        assert "DE-01" in quality_criteria_content
        assert "DE-02" in quality_criteria_content
        assert "DE-03" in quality_criteria_content
        assert "Aesthetic Sophistication" in quality_criteria_content
        assert "Data Storytelling" in quality_criteria_content

    def test_quality_criteria_has_library_mastery(self, quality_criteria_content: str) -> None:
        """Quality criteria should have Library Mastery criteria."""
        assert "LM-01" in quality_criteria_content
        assert "LM-02" in quality_criteria_content
        assert "Idiomatic Usage" in quality_criteria_content
        assert "Distinctive Features" in quality_criteria_content

    def test_quality_criteria_has_score_caps(self, quality_criteria_content: str) -> None:
        """Quality criteria should include the correct-but-boring cap."""
        assert "## Score Caps" in quality_criteria_content
        assert "DE-01" in quality_criteria_content
        assert "75" in quality_criteria_content

    def test_quality_criteria_has_anti_inflation(self, quality_criteria_content: str) -> None:
        """Quality criteria should have anti-inflation calibration anchors."""
        assert "## Anti-Inflation" in quality_criteria_content
        assert "72-78" in quality_criteria_content

    def test_quality_criteria_points_sum_to_100(self, quality_criteria_content: str) -> None:
        """Quality criteria point distribution should sum to 100."""
        # Check that the point distribution table contains 30+20+15+15+10+10=100
        assert "| Visual Quality | 30 |" in quality_criteria_content
        assert "| Design Excellence | 20 |" in quality_criteria_content
        assert "| Spec Compliance | 15 |" in quality_criteria_content
        assert "| Data Quality | 15 |" in quality_criteria_content
        assert "| Code Quality | 10 |" in quality_criteria_content
        assert "| Library Mastery | 10 |" in quality_criteria_content
        assert "| **Total** | **100** |" in quality_criteria_content

    def test_quality_evaluator_has_six_categories(self, quality_evaluator_content: str) -> None:
        """Quality evaluator should have all 6 scoring categories."""
        assert "Design Excellence" in quality_evaluator_content
        assert "Library Mastery" in quality_evaluator_content
        assert "design_excellence" in quality_evaluator_content
        assert "library_mastery" in quality_evaluator_content

    def test_quality_evaluator_has_ar08_check(self, quality_evaluator_content: str) -> None:
        """Quality evaluator should have AR-08 check step."""
        assert "AR-08" in quality_evaluator_content
        assert "Fake Functionality" in quality_evaluator_content or "FAKE_FUNCTIONALITY" in quality_evaluator_content

    def test_quality_evaluator_has_anti_inflation(self, quality_evaluator_content: str) -> None:
        """Quality evaluator should have anti-inflation rules."""
        assert "Anti-Inflation" in quality_evaluator_content
        assert "72-78" in quality_evaluator_content

    @pytest.mark.parametrize("filename", EXPECTED_LIBRARY_PROMPTS)
    def test_library_prompt_has_required_sections(self, filename: str) -> None:
        """Each library prompt should have import, create figure, and save sections."""
        content = (LIBRARY_PROMPTS_DIR / filename).read_text()
        library_name = filename.replace(".md", "")

        # Check for header (normalize by removing hyphens for comparison)
        content_normalized = content.lower().replace("-", "")
        assert f"# {library_name}" in content_normalized, f"Missing header for {library_name}"

        # Check for import section
        assert "## Import" in content or "import" in content.lower(), f"Missing import section in {filename}"

        # Check for code examples
        assert "```python" in content, f"Missing Python code examples in {filename}"

    @pytest.mark.parametrize("filename", EXPECTED_LIBRARY_PROMPTS)
    def test_library_prompt_has_save_section(self, filename: str) -> None:
        """Each library prompt should show how to save the plot."""
        content = (LIBRARY_PROMPTS_DIR / filename).read_text()
        # KISS style: prompts show how to save, not function return types
        save_patterns = ["## Save", "savefig", "save(", "write_image", "save_screenshot", "export_png"]
        has_save_info = any(pattern in content for pattern in save_patterns)
        assert has_save_info, f"Missing save/output section in {filename}"

    @pytest.mark.parametrize("filename", STATIC_LIBRARIES)
    def test_static_library_has_interactive_handling(self, filename: str) -> None:
        """Static library prompts should have Interactive Spec Handling section."""
        content = (LIBRARY_PROMPTS_DIR / filename).read_text()
        assert "## Interactive Spec Handling" in content, f"{filename} missing Interactive Spec Handling section"
        assert "NOT_FEASIBLE" in content, f"{filename} missing NOT_FEASIBLE guidance"
        assert "AR-08" in content, f"{filename} missing AR-08 reference"

    @pytest.mark.parametrize("filename", EXPECTED_LIBRARY_PROMPTS)
    def test_library_prompt_has_color_section(self, filename: str) -> None:
        """Each library prompt should have a Colors section with the anyplot brand color."""
        content = (LIBRARY_PROMPTS_DIR / filename).read_text()
        assert "## Colors" in content, f"{filename} missing ## Colors section"
        # The brand bluish green (#009E73) is mandated as the first-series color
        # across all library prompts — anyplot palette position 1.
        assert "#009E73" in content, f"{filename} missing anyplot brand color reference"

    @pytest.mark.parametrize("filename", EXPECTED_LIBRARY_PROMPTS)
    def test_library_prompt_no_hardcoded_yellow(self, filename: str) -> None:
        """Library prompts should not hardcode Python Yellow as automatic second color."""
        content = (LIBRARY_PROMPTS_DIR / filename).read_text()
        # Check that FFD43B is not in the colors section as a recommended color
        # It may appear in old comments or examples, but should not be in ## Colors
        colors_section_match = re.search(r"## Colors\n(.*?)(?=\n## |\Z)", content, re.DOTALL)
        if colors_section_match:
            colors_section = colors_section_match.group(1)
            assert "#FFD43B" not in colors_section, f"{filename} still has hardcoded Python Yellow in Colors section"


class TestNoPlaceholders:
    """Test that no placeholder text is left in prompts."""

    PLACEHOLDER_PATTERNS = [
        r"\{TODO\}",
        r"\bTODO\b",
        r"\bFIXME\b",
        r"\bXXX\b",
        r"\{placeholder\}",
        r"\{PLACEHOLDER\}",
        r"<INSERT.*>",
        r"\[TBD\]",
    ]

    def _get_all_prompt_files(self) -> list[Path]:
        """Get all markdown files in prompts directory."""
        files = list(PROMPTS_DIR.glob("*.md"))
        files.extend(LIBRARY_PROMPTS_DIR.glob("*.md"))
        return files

    @pytest.mark.parametrize("pattern", PLACEHOLDER_PATTERNS, ids=[p.replace("\\", "") for p in PLACEHOLDER_PATTERNS])
    def test_no_placeholder_pattern(self, pattern: str) -> None:
        """No placeholder patterns should exist in any prompt."""
        regex = re.compile(pattern, re.IGNORECASE)

        for filepath in self._get_all_prompt_files():
            content = filepath.read_text()
            matches = regex.findall(content)
            assert not matches, f"Found placeholder '{pattern}' in {filepath.name}: {matches}"

    def test_no_empty_sections(self) -> None:
        """No empty sections (## Header followed by another ## or end of file)."""
        # Find all level-2 headers and their positions
        header_pattern = re.compile(r"^## .+$", re.MULTILINE)

        for filepath in self._get_all_prompt_files():
            content = filepath.read_text()
            headers = list(header_pattern.finditer(content))

            empty_sections = []
            for i, match in enumerate(headers):
                header = match.group()
                start = match.end()
                # End is either the next header or end of content
                end = headers[i + 1].start() if i + 1 < len(headers) else len(content)
                section_content = content[start:end].strip()

                # Check if section content is empty (only whitespace)
                if not section_content:
                    empty_sections.append(header)

            assert not empty_sections, f"Found empty sections in {filepath.name}: {empty_sections}"


class TestCrossReferences:
    """Test that cross-references in prompts are valid."""

    def test_plot_generator_references_exist(self) -> None:
        """Files referenced in plot-generator.md should exist."""
        content = (PROMPTS_DIR / "plot-generator.md").read_text()

        # Check for references to library prompts
        if "prompts/library/" in content:
            # All library prompts should exist
            for lib_file in EXPECTED_LIBRARY_PROMPTS:
                assert (LIBRARY_PROMPTS_DIR / lib_file).exists()

    def test_no_broken_internal_links(self) -> None:
        """Internal markdown links should point to existing files."""
        link_pattern = re.compile(r"\[.*?\]\((?!http)([^)]+\.md)\)")

        for filepath in PROMPTS_DIR.glob("**/*.md"):
            content = filepath.read_text()
            links = link_pattern.findall(content)

            for link in links:
                # Resolve relative to the file's directory
                target = (filepath.parent / link).resolve()
                # Also check relative to prompts root
                target_alt = (PROMPTS_DIR / link).resolve()

                exists = target.exists() or target_alt.exists()
                assert exists, f"Broken link in {filepath.name}: {link}"


class TestPromptConsistency:
    """Test consistency across prompts."""

    def test_all_libraries_have_same_structure(self) -> None:
        """All library prompts should have consistent structure."""
        structures: dict[str, set[str]] = {}
        section_pattern = re.compile(r"^## (.+)$", re.MULTILINE)

        for lib_file in EXPECTED_LIBRARY_PROMPTS:
            content = (LIBRARY_PROMPTS_DIR / lib_file).read_text()
            sections = set(section_pattern.findall(content))
            structures[lib_file] = sections

        # Check that all have at least the common sections
        common_sections = {"Import", "Colors"}
        for lib_file, sections in structures.items():
            missing = common_sections - sections
            assert not missing, f"{lib_file} missing common sections: {missing}"

    def test_quality_score_threshold_consistent(self) -> None:
        """Quality threshold (90) should be consistent across scoring prompts."""
        files_to_check = [PROMPTS_DIR / "quality-criteria.md", PROMPTS_DIR / "quality-evaluator.md"]

        for filepath in files_to_check:
            if filepath.exists():
                content = filepath.read_text()
                assert ">= 90" in content or "≥ 90" in content, f"Approval threshold (90) not found in {filepath.name}"

    def test_scoring_categories_consistent(self) -> None:
        """Quality criteria and evaluator should have the same 6 categories."""
        criteria = (PROMPTS_DIR / "quality-criteria.md").read_text()
        evaluator = (PROMPTS_DIR / "quality-evaluator.md").read_text()

        categories = [
            "Visual Quality",
            "Design Excellence",
            "Spec Compliance",
            "Data Quality",
            "Code Quality",
            "Library Mastery",
        ]

        for category in categories:
            assert category in criteria, f"Missing {category} in quality-criteria.md"
            assert category in evaluator, f"Missing {category} in quality-evaluator.md"


class TestPromptQuality:
    """Test overall prompt quality."""

    def test_prompts_not_too_short(self) -> None:
        """Prompts should have substantial content (>100 chars)."""
        min_length = 100

        for filepath in PROMPTS_DIR.glob("**/*.md"):
            if filepath.name == "README.md":
                continue
            content = filepath.read_text()
            assert len(content) > min_length, f"{filepath.name} too short ({len(content)} chars)"

    def test_prompts_have_headers(self) -> None:
        """All prompts should have at least one header."""
        for filepath in PROMPTS_DIR.glob("**/*.md"):
            if filepath.name == "README.md":
                continue
            content = filepath.read_text()
            assert re.search(r"^#+ ", content, re.MULTILINE), f"{filepath.name} has no markdown headers"

    def test_code_blocks_have_language(self) -> None:
        """Code blocks should specify language for syntax highlighting."""
        # Pattern for code blocks without language
        unlabeled_pattern = re.compile(r"^```\s*$", re.MULTILINE)
        labeled_pattern = re.compile(r"^```\w+", re.MULTILINE)

        for filepath in PROMPTS_DIR.glob("**/*.md"):
            content = filepath.read_text()
            unlabeled = len(unlabeled_pattern.findall(content))
            labeled = len(labeled_pattern.findall(content))

            # If there are code blocks, at least some should have language hints
            # Prompts often use unlabeled blocks for output examples
            total = unlabeled + labeled
            if total > 0:
                labeled_ratio = labeled / total
                assert labeled_ratio >= 0.2, (
                    f"{filepath.name} has too few labeled code blocks "
                    f"({labeled}/{total} = {labeled_ratio:.0%}, need ≥20%)"
                )
