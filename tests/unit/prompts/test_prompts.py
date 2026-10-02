"""
Tests for AI prompts structure and content validation.

Best practices for prompt testing:
1. File existence - All expected prompts exist
2. Required sections - Core sections are present (## Role, ## Task, etc.)
3. No placeholders - No TODO, FIXME, or {placeholder} left behind
4. Cross-references valid - Referenced files exist
5. Consistent formatting - Markdown is well-formed
"""

import json
import re
import tomllib
from pathlib import Path

import pytest

from automation.scripts.regen_gate import DEFECT_RE, SUGGESTION_RE
from automation.scripts.spec_characteristics_lint import check_contract
from core.constants import INTERACTIVE_LIBRARIES, LANGUAGE_FILE_EXTENSIONS, LIBRARIES_METADATA, SUPPORTED_LANGUAGES


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

# Library prompts checked for the Python-style structure (## Import / ## Save /
# ## Colors). The JavaScript libraries (chartjs, d3, echarts, highcharts, and the
# React MUI X entry `muix`) follow a different convention — a mount-node / harness
# contract, "## Output Files", and (for muix) a default-exported React component —
# so they are intentionally excluded here, the same way the Phase-1 JS prompts
# are. highcharts moved Python → JavaScript in Phase 2; muix is the first React
# (.tsx) entry.
EXPECTED_LIBRARY_PROMPTS = [
    "matplotlib.md",
    "seaborn.md",
    "plotly.md",
    "bokeh.md",
    "altair.md",
    "plotnine.md",
    "pygal.md",
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
        assert "### Scoring principles" in quality_criteria_content

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

    @pytest.mark.parametrize(
        "prompt_path",
        [
            PROMPTS_DIR / "quality-criteria.md",
            PROMPTS_DIR / "quality-evaluator.md",
            PROMPTS_DIR / "workflow-prompts" / "ai-quality-review.md",
        ],
        ids=lambda p: p.name,
    )
    def test_the_reviewer_never_sees_the_approval_cascade(self, prompt_path: Path) -> None:
        """P10: a review scores without the bar in view. The thresholds and
        what follows from a score live in the workflow and in the docs."""
        content = prompt_path.read_text()
        for phrase in (
            "≥ 90",
            ">= 90",
            "Review 1",
            "ai-approved, merge",
            "repair loop exists",
            "Cascading",
            "cascade",
            "cannot pass on first review",
            "To reach 90+",
            "→ Repair loop",
            "current ~95% scoring 90+",
        ):
            assert phrase not in content, phrase
        overview = (PROMPTS_DIR.parent / "docs" / "workflows" / "overview.md").read_text()
        assert "Score >= 90" in overview and "Score >= 50" in overview

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


class TestFifteenLibraryCoverage:
    """Review prompts must know the full library registry.

    Guards against the drift the 2026-07-08 audit found (M#12): scoring
    prompts still describing the 9-Python-library era while the pipeline
    reviews R, Julia, and JavaScript implementations. Expectations derive
    from core.constants so a future library lands here as a failing test,
    not as silent scoring bias.
    """

    WORKFLOW_PROMPTS_DIR = PROMPTS_DIR / "workflow-prompts"

    SCORING_PROMPTS = [PROMPTS_DIR / "quality-evaluator.md", PROMPTS_DIR / "workflow-prompts" / "ai-quality-review.md"]

    @pytest.mark.parametrize("prompt_path", SCORING_PROMPTS, ids=lambda p: p.name)
    def test_interactive_library_list_matches_registry(self, prompt_path: Path) -> None:
        """The '**Interactive libraries**' line must EQUAL the canonical set —
        a missing entry biases scoring against that library, an extra entry
        makes reviewers expect HTML output the library never produces."""
        content = prompt_path.read_text()
        line = next((line for line in content.splitlines() if line.startswith("**Interactive libraries**")), None)
        assert line is not None, f"{prompt_path.name} has no '**Interactive libraries**' line"
        listed = {entry.strip().rstrip(".") for entry in line.rsplit(":", 1)[1].split(",")}
        assert listed == set(INTERACTIVE_LIBRARIES), (
            f"{prompt_path.name} interactive list drifted — "
            f"missing: {sorted(set(INTERACTIVE_LIBRARIES) - listed)}, "
            f"extra: {sorted(listed - set(INTERACTIVE_LIBRARIES))}"
        )

    @pytest.mark.parametrize("prompt_path", SCORING_PROMPTS, ids=lambda p: p.name)
    def test_every_file_extension_documented(self, prompt_path: Path) -> None:
        """Language defaults plus per-library overrides (.tsx) must all appear."""
        expected = set(LANGUAGE_FILE_EXTENSIONS.values()) | {
            lib["file_extension"] for lib in LIBRARIES_METADATA if "file_extension" in lib
        }
        content = prompt_path.read_text()
        missing = [ext for ext in sorted(expected) if f"`{ext}`" not in content]
        assert not missing, f"{prompt_path.name} missing file extensions: {missing}"

    @pytest.mark.parametrize(
        "prompt_path",
        [
            PROMPTS_DIR / "quality-criteria.md",
            PROMPTS_DIR / "quality-evaluator.md",
            PROMPTS_DIR / "workflow-prompts" / "ai-quality-review.md",
        ],
        ids=lambda p: p.name,
    )
    def test_sc04_title_rule_accepts_every_language(self, prompt_path: Path) -> None:
        """SC-04's language set must include every supported language, or every
        correct JS/Julia title costs points."""
        content = prompt_path.read_text()
        sc04_lines = [line for line in content.splitlines() if "language ∈" in line]
        assert sc04_lines, f"{prompt_path.name} has no SC-04 'language ∈' rule"
        joined = "\n".join(sc04_lines)
        missing = [lang for lang in sorted(SUPPORTED_LANGUAGES) if lang not in joined]
        assert not missing, f"{prompt_path.name} SC-04 language set missing: {missing}"

    def test_checklist_example_uses_canonical_six_keys(self) -> None:
        """The step-10 review_checklist.json example must show exactly the six
        canonical category keys (the website renders this shape directly)."""
        content = (self.WORKFLOW_PROMPTS_DIR / "ai-quality-review.md").read_text()
        for key in (
            "visual_quality",
            "design_excellence",
            "spec_compliance",
            "data_quality",
            "code_quality",
            "library_mastery",
        ):
            assert f'"{key}"' in content, f"checklist example missing key: {key}"
        assert "library_features" not in content, "stale 5-category checklist key resurfaced"


CHARACTERISTICS_HEADING = "## What a good version looks like"
PLOTS_DIR = PROMPTS_DIR.parent / "plots"
WORKFLOW_PROMPTS_DIR = PROMPTS_DIR / "workflow-prompts"

# Hand-seeded (owner-approved, one-off) characteristic sections for the most
# regenerated / central plot types, split to one kind per bullet ("A good
# version shows:" / "Expected, not a defect:") in the P0 lint PR. Every other
# spec gets the section from spec-create or the one-time backfill, or keeps
# relying on the review inferring it from Description/Notes.
SEEDED_CHARACTERISTIC_SPECS = [
    "bubble-basic",
    "scatter-basic",
    "line-basic",
    "bar-basic",
    "heatmap-basic",
    "heatmap-correlation",
    "violin-basic",
    "network-force-directed",
]


def _specs_with_characteristics() -> list[str]:
    return sorted(
        path.parent.name
        for path in PLOTS_DIR.glob("*/specification.md")
        if CHARACTERISTICS_HEADING in path.read_text(encoding="utf-8")
    )


class TestPlotTypeCharacteristics:
    """The per-spec "What a good version looks like" section and the review
    rules built on it (regen-stability experiment on bubble-basic, 2026-09-27:
    marks displaced by collision layouts, invisible size-legend glyphs and extra
    encodings on -basic specs were scored as strengths or not at all)."""

    def test_template_ends_with_characteristics_section(self) -> None:
        """Trailing, so sync_to_postgres' `(?=\\n##|\\Z)` split can't leak it into Notes."""
        content = (PROMPTS_DIR / "templates" / "specification.md").read_text()
        headings = re.findall(r"^## .+$", content, re.MULTILINE)
        assert headings[-2:] == ["## Notes", CHARACTERISTICS_HEADING]

    def test_template_placeholders_carry_the_kinds(self) -> None:
        content = (PROMPTS_DIR / "templates" / "specification.md").read_text()
        section = content[content.index(CHARACTERISTICS_HEADING) :]
        assert "\n- A good version shows: {" in section
        assert "\n- Expected, not a defect: {" in section
        assert "3-6 in total, one kind per bullet" in section
        assert "the basic variant's" in section
        assert "Derived layers (trend or fit lines" in section

    def test_quality_criteria_covers_new_rules(self) -> None:
        content = (PROMPTS_DIR / "quality-criteria.md").read_text()
        assert "## Plot-Type Characteristics" in content
        assert content.index("## Plot-Type Characteristics") < content.index("## Score Caps")
        assert "What a good version looks like" in content
        assert "Data-value integrity" in content
        assert "Legend glyphs" in content
        assert "hides information" in content
        assert "Variant creep on `-basic` specs" in content
        assert "Affirmative properties" in content
        assert "absence of a permitted thing never deducts" in content
        assert "not the render's chrome" in content
        # One kind per bullet, and what a permission never becomes.
        assert "`A good version shows:`" in content
        assert "`Expected, not a defect:`" in content
        assert "Nothing an `Expected, not a defect:` bullet names is ever a weakness" in content
        assert "A permission is not an aspect to exhibit" in content
        assert "Related but different form" in content
        assert "spline overshoot" in content

    @pytest.mark.parametrize(
        "prompt_path",
        [WORKFLOW_PROMPTS_DIR / "ai-quality-review.md", PROMPTS_DIR / "quality-evaluator.md"],
        ids=lambda p: p.name,
    )
    def test_scoring_prompts_mirror_the_rules(self, prompt_path: Path) -> None:
        """Both scoring prompts — the workflow reviewer and the one
        scripts/evaluate-plot.py concatenates with the rubric — carry the
        same characteristic-section rules, so neither scores by the old ones."""
        content = prompt_path.read_text()
        assert "What a good version looks like" in content
        assert "affirmative properties" in content
        assert "absence of a permitted thing never deducts" in content
        assert "hides information" in content
        assert "visible in BOTH themes" in content
        assert "Marks sit at their data values" in content
        assert "layout-positioned types" in content
        assert "any jitter, dodge or offset the spec's Data or Notes ask for" in content
        assert "neither requires nor offers as optional" in content
        assert "wrong variant" in content
        assert "are permissions, not features" in content
        assert "`A good version shows:` bullets are *affirmative properties*" in content
        assert "`Expected, not a defect:` bullets are *permissions*" in content
        assert "Nothing a permission names is ever a weakness" in content
        assert "A permission is not an aspect to exhibit" in content
        assert "a donut for a pie" in content
        assert "spline overshoot" in content
        assert "Check each Notes bullet and each `A good version shows:` bullet" in content

    def test_regen_step_8b_rules(self) -> None:
        """Step 8b: a permission is never an improvement ref, an unasked layer
        is never an improvement, and the regression wording carries the SC-03
        exemptions and the required-element exception."""
        content = (WORKFLOW_PROMPTS_DIR / "ai-quality-review.md").read_text()
        step = content[content.index("### 8b.") : content.index("### 9.")]
        assert "can never be an improvement `ref`" in step
        assert "is never an improvement, on any spec" in step
        assert "Chrome the criteria require (title format, legend, axis labels, color bar) is not an addition" in step
        assert "jitter in categorical strip and swarm plots" in step
        assert "layout-positioned types" in step
        assert "any jitter, dodge or offset the spec's Data or Notes ask for" in step
        assert "a required element the predecessor lacked is an improvement, not an addition" in step
        assert "every `C` ref an id of an `A good version shows:` bullet" in step
        assert "(jitter, force or declutter passes that move the marks)" not in step
        # P8: the code improvement bullet and the source carve-out for CQ items.
        assert "List it under `code_improvements`" in step
        assert "Only `W` ids qualify" in step
        assert "(or its source, `/tmp/anyplot-prev-impl${EXT}`, for CQ items" in step
        assert "code-only changes still never go under `improvements`" in step
        example = json.loads(step.split("```json\n", 1)[1].split("\n```", 1)[0])
        assert example["code_improvements"] == []

    def test_generation_prompts_forbid_moving_marks(self) -> None:
        for path in (
            WORKFLOW_PROMPTS_DIR / "impl-generate-claude.md",
            WORKFLOW_PROMPTS_DIR / "impl-repair-claude.md",
            PROMPTS_DIR / "plot-generator.md",
        ):
            content = path.read_text()
            assert "What a good version looks like" in content or "characteristic section" in content, path.name
            assert re.search(r"never (?:by )?mov(?:e|ing) marks", content, re.IGNORECASE), path.name
            # The SC-03 exemptions travel with the rule, or generation would
            # "fix" legitimate strip-plot jitter or network layouts.
            assert "layout-positioned types" in content, path.name
            assert "any jitter, dodge or offset the spec's Data or Notes ask for" in content, path.name
            # Permissions are never targets (the bubble-overlap leak: data
            # clustered to "show" the overlap a spec only permits).
            assert "`Expected, not a defect:` bullets are permissions, not targets" in content, path.name
            assert re.search(r"never shape the data to produce them", content, re.IGNORECASE), path.name

    @pytest.mark.parametrize(
        "prompt_path",
        [WORKFLOW_PROMPTS_DIR / "impl-generate-claude.md", WORKFLOW_PROMPTS_DIR / "impl-repair-claude.md"],
        ids=lambda p: p.name,
    )
    def test_regen_and_repair_decline_unreal_weaknesses(self, prompt_path: Path) -> None:
        content = prompt_path.read_text()
        assert 'Address every bullet under "Weaknesses"' not in content
        assert "(fix these problems - decide HOW yourself)" not in content
        assert "Keep the data scenario and the variant" in content
        assert "Don't add code for changes that don't show" in content
        assert "Declined:" in content

    def test_spec_polish_never_touches_the_section(self) -> None:
        content = (WORKFLOW_PROMPTS_DIR / "spec-polish-claude.md").read_text()
        assert "Do NOT author, rewrite" in content
        assert "What a good version looks like" in content
        assert "is out of scope for this audit" in content

    @pytest.mark.parametrize("spec_id", SEEDED_CHARACTERISTIC_SPECS)
    def test_seeded_spec_has_section(self, spec_id: str) -> None:
        content = (PLOTS_DIR / spec_id / "specification.md").read_text(encoding="utf-8")
        assert CHARACTERISTICS_HEADING in content, f"{spec_id} lost its seeded characteristic section"

    @pytest.mark.parametrize("spec_id", _specs_with_characteristics())
    def test_section_follows_parser_format(self, spec_id: str) -> None:
        """The parser contract the regen gate reads as C1..Cn, checked by the
        same lint CI runs (automation/scripts/spec_characteristics_lint.py
        `contract`): heading once, last section, column-0 `- ` bullets with a
        kind prefix, 2-8 of them. House style (3-6, one line each) is the
        lint's `style` check, which only warns."""
        content = (PLOTS_DIR / spec_id / "specification.md").read_text(encoding="utf-8")
        findings = check_contract(content)
        assert not findings, f"{spec_id}: " + "; ".join(f"{f.rule} line {f.line}: {f.message}" for f in findings)


REVIEW_PROMPT = WORKFLOW_PROMPTS_DIR / "ai-quality-review.md"
GENERATION_PROMPTS = [
    WORKFLOW_PROMPTS_DIR / "impl-generate-claude.md",
    WORKFLOW_PROMPTS_DIR / "impl-repair-claude.md",
    PROMPTS_DIR / "plot-generator.md",
]


class TestDefectsAndSuggestions:
    """P3: a weakness is a defect line or a `Suggestion:` line, a regen review
    classifies the previous weaknesses (obsolete included), and generation acts
    on defects only (regen round 1, 2026-09-27: 17 of 30 cited improvements
    were suggestions and six merges rested on no defect)."""

    def _section(self, content: str, start: str, end: str) -> str:
        return content[content.index(start) : content.index(end, content.index(start))]

    def test_template_weaknesses_use_the_two_formats(self) -> None:
        content = REVIEW_PROMPT.read_text()
        template = self._section(content, "### 9.", "### 10.")
        weaknesses = self._section(template, "### Weaknesses", "### Regeneration comparison")
        lines = [line[2:] for line in weaknesses.splitlines() if line.startswith("- ")]
        assert len(lines) >= 4
        assert all(DEFECT_RE.match(line) or SUGGESTION_RE.match(line) for line in lines), lines
        assert any(SUGGESTION_RE.match(line) for line in lines)
        assert sum(1 for line in lines if DEFECT_RE.match(line)) == 3

    def test_old_order_sections_are_gone(self) -> None:
        content = REVIEW_PROMPT.read_text()
        for phrase in ("Issues Found", "AI Feedback for Next Attempt", "Consider a more refined"):
            assert phrase not in content, phrase
        gate = (PROMPTS_DIR.parent / "automation" / "scripts" / "regen_gate.py").read_text()
        assert "FIX these" not in gate

    def test_every_review_reads_the_definitions(self) -> None:
        content = REVIEW_PROMPT.read_text()
        section = self._section(content, "### 8a.", "### 8b.")
        assert "(every review)" in section
        assert "`Suggestion: <idea>`" in section
        assert "At most three" in section
        assert "A behavior is never both a strength and a weakness" in section
        assert "Never write a defect that asks to add something the spec does not ask for" in section
        assert "never suggest a layer the spec does not ask for" in section
        assert "Never propose moving marks" in section

    def test_step_8b_classifies_and_keeps_the_scores_final(self) -> None:
        content = REVIEW_PROMPT.read_text()
        step = self._section(content, "### 8b.", "### 9.")
        for word in ("prev_checklist", "prev_weaknesses", "obsolete", "`rule`"):
            assert word in step, word
        assert "change the claim, never the scores" in step
        assert "`prev_checklist` and `review_checklist.json` are final" in step
        assert "an unclassified `W` counts as a suggestion" in step
        # D7: the gate list stays as it is until P6-B, and 8b never says what carries.
        assert "at least one improvement a viewer can see (non-empty `where_visible`)" in step
        for phrase in ("carrier", "carries a merge", "never carry", "DE and LM"):
            assert phrase not in step, phrase

    def test_step_10_runs_the_self_check(self) -> None:
        content = REVIEW_PROMPT.read_text()
        step = self._section(content, "### 10.", "### 11.")
        assert "python3 /tmp/anyplot-regen-gate.py check-feedback" in step
        assert "--regen review_regen.json --prev-weaknesses /tmp/anyplot-prev-weaknesses.json" in step
        # The regen flags are code the block runs when review_regen.json exists,
        # not a commented-out alternative a reviewer following it never runs.
        assert "if [ -f review_regen.json ]; then" in step
        regen_lines = [line for line in step.splitlines() if "--regen review_regen.json" in line]
        assert regen_lines and not any(line.lstrip().startswith("#") for line in regen_lines), regen_lines
        assert "never `prev_checklist` or `review_checklist.json`" in step
        assert '"prev_checklist": {' in step and '"prev_weaknesses": [' in step

    def test_important_list_carries_the_rules(self) -> None:
        important = REVIEW_PROMPT.read_text().split("## Important", 1)[1]
        assert "Every weakness line is a defect" in important
        assert "Never write a defect that asks to add something the spec does not ask for" in important
        assert "On a `-basic` spec, never suggest a layer the spec does not ask for" in important
        assert "Every weakness is acted on by the next generation" not in important

    def test_canvas_weakness_is_a_defect_line(self) -> None:
        content = REVIEW_PROMPT.read_text()
        assert "`VQ-05 (both): Canvas dimensions drifted from required target." in content

    @pytest.mark.parametrize("prompt_path", GENERATION_PROMPTS, ids=lambda p: p.name)
    def test_generation_acts_on_defects_only(self, prompt_path: Path) -> None:
        content = prompt_path.read_text()
        assert "`Suggestion:` line" in content
        assert "suggestion, not taken" in content
        assert "obsolete" in content
        assert "checklist is context" in content

    def test_step_8b_writes_the_rescore_as_a_full_review(self) -> None:
        """P9b: 8b step 5 writes review_prev.json, which a keep stores as the
        live implementation's review; its checklist is prev_checklist."""
        step = self._section(REVIEW_PROMPT.read_text(), "### 8b.", "### 9.")
        assert step.index("4. **Write `review_regen.json`**") < step.index("5. **Write `review_prev.json`**")
        for key in ("image_description", "criteria_checklist", "strengths", "weaknesses"):
            assert f"`{key}`" in step, key
        # P10: the reviewer writes no verdict; the write-back sets it.
        assert "`verdict`" not in step
        assert "Every item score equals the same item in `prev_checklist`" in step
        assert "each category's `score` is the sum of its items" in step
        assert "skip steps 1–5, do not write `review_regen.json` or `review_prev.json`" in step
        # P3.1: a P item of kind addition or polish is a suggestion line, not a defect line.
        assert (
            "They become the defect lines of `review_prev.json` (step 5), except the ones step 3 lists as an "
            "`addition` or `polish`"
        ) in step
        assert "without the `P` id, then at most three `Suggestion:` lines" in step
        assert "with kind `addition` or `polish` is one of those `Suggestion:` lines, not a defect line" in step
        assert "in that order" not in step
        assert "never mention the new render, the comparison, or the regeneration" in step
        assert "No score key and no verdict: the stored score is `prev_rescored`" in step
        assert "changes nothing you decided above" in step

    def test_step_10_has_the_review_prev_example_and_checks_it(self) -> None:
        content = REVIEW_PROMPT.read_text()
        step = self._section(content, "### 10.", "### 11.")
        example = step.split("cat > review_prev.json << 'EOF'\n", 1)[1].split("\nEOF", 1)[0]
        assert "python3 -c \"import json; json.load(open('review_prev.json'))\"" in step
        for key in ("image_description", "criteria_checklist", "strengths", "weaknesses"):
            assert f'"{key}"' in example, key
        assert '"quality_score"' not in example and '"prev_rescored"' not in example
        assert '"verdict"' not in example and "review_verdict.txt" not in step
        # The example agrees with the review_regen.json example: its items are
        # prev_checklist's, each category is the sum of its prev_checklist
        # items, and the categories add up to prev_rescored (no cap applies).
        regen = json.loads(step.split("cat > review_regen.json << 'EOF'\n", 1)[1].split("\nEOF", 1)[0])
        items = re.findall(r'"id": "([A-Z]{2}-\d{2})", "name": "[^"]*", "score": (\d+)', example)
        assert items and all(regen["prev_checklist"][cid] == int(score) for cid, score in items)
        categories = re.findall(r'"[a-z_]+": \{\s*"score": (\d+),\s*"max": (\d+)', example)
        assert len(categories) == 6
        assert [int(score) for score, _ in categories] == [
            sum(v for cid, v in regen["prev_checklist"].items() if cid.startswith(prefix))
            for prefix in ("VQ", "DE", "SC", "DQ", "CQ", "LM")
        ]
        assert sum(int(score) for score, _ in categories) == regen["prev_rescored"]
        assert [int(top) for _, top in categories] == [30, 20, 15, 15, 10, 10]
        weaknesses = json.loads(re.search(r'"weaknesses": (\[.*\])\n', example).group(1))
        assert DEFECT_RE.match(weaknesses[0]) and SUGGESTION_RE.match(weaknesses[-1])
        # The self-check covers the file whenever review_regen.json exists.
        flags = [line for line in step.splitlines() if "--prev-review review_prev.json" in line]
        assert len(flags) == 1 and "FLAGS+=(--regen review_regen.json" in flags[0]
        assert "goes only into `review_regen.json`" not in content
        assert (
            "except `review_regen.json` and `review_prev.json`, which describe your re-score of the predecessor" in step
        )
        assert "A `review_prev.json` problem is fixed in `review_prev.json`" in step

    def test_step_8b_names_the_improvement_kinds(self) -> None:
        """P3.1: every improvement names a kind; the prompt defines the four
        kinds but never says which carry (D7)."""
        content = REVIEW_PROMPT.read_text()
        step = self._section(content, "### 8b.", "### 9.")
        for kind in ("fix", "removal", "addition", "polish"):
            assert f"     - `{kind}` — " in step, kind
        assert "every improvement names one `kind`" in step
        assert "An `addition` or `polish` item names no violated rule (8a)" in step
        assert "in `review_prev.json` it is a `Suggestion:` line" in step
        # An addition or polish fixes no rule: it names none and claims no score delta.
        assert "or, for an `addition` or `polish` (see **Kind**), changes something no rule required" in step
        assert 'A `P` or `"new"` item of kind `fix` or `removal` also names its `rule`' in step
        assert "An improvement of kind `fix` or `removal` that claims a criterion" in step
        # Definitions only: nothing says which kinds count for the gate.
        for phrase in ("only a fix", "do not count", "does not count toward", "kinds that count", "gate ignores"):
            assert phrase not in step.lower(), phrase
        # Both examples carry a kind on every improvement.
        example = json.loads(step.split("```json\n", 1)[1].split("\n```", 1)[0])
        assert all(item.get("kind") in ("fix", "removal", "addition", "polish") for item in example["improvements"])
        one_liner = self._section(content, "### 10.", "### 11.")
        regen = json.loads(one_liner.split("cat > review_regen.json << 'EOF'\n", 1)[1].split("\nEOF", 1)[0])
        assert all(item.get("kind") == "fix" for item in regen["improvements"])

    def test_examples_use_an_in_scope_collision(self) -> None:
        """P3.1: the BEAU-001 callout is polish on bubble-basic, so the prompt's
        examples use the size legend's label, which the Notes require."""
        content = REVIEW_PROMPT.read_text()
        assert "BEAU-001" not in content
        assert '"Size-legend value labels clear of their reference bubbles"' in content
        assert 'the size legend\'s "500" label overlaps its reference bubble' in content

    def test_8a_scope_and_counter_examples(self) -> None:
        section = self._section(REVIEW_PROMPT.read_text(), "### 8a.", "### 8b.")
        assert (
            "polishing an element the spec's scope excludes (on a `-basic` spec, the layers SC-01 lists; on any "
            "spec, an annotation or callout the spec does not request), including moving another element clear of it"
        ) in section
        assert "moving the label clear of it, like recoloring the line, is a suggestion" in section
        assert "A count plot without percentage labels has no DQ-01 defect" in section
        assert '"if drawn"' in section and '"the Notes allow"' in section

    @pytest.mark.parametrize(
        "prompt_path",
        [WORKFLOW_PROMPTS_DIR / "ai-quality-review.md", PROMPTS_DIR / "quality-evaluator.md"],
        ids=lambda p: p.name,
    )
    def test_dq01_row_names_optional_features(self, prompt_path: Path) -> None:
        row = next(line for line in prompt_path.read_text().splitlines() if line.startswith("| DQ-01 |"))
        assert "neither is an optional feature the Notes only allow" in row
        assert "a missing optional feature deducts nothing" in row
        criteria = (PROMPTS_DIR / "quality-criteria.md").read_text()
        assert "**An optional feature is not an aspect to exhibit either.**" in criteria

    def test_important_list_names_the_stored_rescore(self) -> None:
        important = REVIEW_PROMPT.read_text().split("## Important", 1)[1]
        assert "including `review_prev.json`, which is stored as the live implementation's review" in important

    def test_f5_one_addition_is_creep(self) -> None:
        criteria = (PROMPTS_DIR / "quality-criteria.md").read_text()
        assert "one such addition is enough" in criteria
        assert "several annotation layers" not in criteria
        assert "the list names the likeliest additions, not all of them" in criteria
        for path in (REVIEW_PROMPT, *GENERATION_PROMPTS):
            content = path.read_text()
            assert "reference lines" in content or "reference or" in content, path.name
            assert "callouts" in content, path.name
        assert "one is enough, listed in the variant bullet or not" in REVIEW_PROMPT.read_text()


REPO_ROOT = PROMPTS_DIR.parent
JS_LIBRARY_PROMPTS = ["d3.md", "echarts.md", "chartjs.md", "highcharts.md", "muix.md"]
LANGUAGE_BLOCK_RE = re.compile(r"^\*\*(Python|R|Julia|JavaScript) — compute with:\*\*$")


def _language_blocks(content: str) -> dict[str, str]:
    """The four "compute with" blocks: the lead-in line and its list lines."""
    blocks: dict[str, str] = {}
    lines = content.splitlines()
    for i, line in enumerate(lines):
        m = LANGUAGE_BLOCK_RE.match(line)
        if not m:
            continue
        body = [line]
        for follow in lines[i + 1 :]:
            if not follow.startswith(("- ", "  ")):
                break
            body.append(follow)
        blocks[m.group(1)] = "\n".join(body)
    return blocks


class TestLeanCode:
    """P8: implementations compute with the runtime's libraries, and CQ-04
    deducts one point for a written-out algorithm an available call computes,
    naming the call and the lines."""

    def test_quality_criteria_carries_the_rule(self) -> None:
        criteria = (PROMPTS_DIR / "quality-criteria.md").read_text()
        cq04 = criteria[criteria.index("### CQ-04") : criteria.index("## Library Mastery")]
        assert "#### Available to compute with" in cq04
        assert "no algorithm written out that an available call computes" in cq04
        assert "``CQ-04 (code): lines A–B" in cq04 and "→ `<call>` (<package>)" in cq04
        assert "Without a concrete replacement it is a `Suggestion:` line" in cq04
        assert "never takes CQ-04 to 0" in cq04
        assert "never a new helper function" in cq04
        assert "never credit a hand-roll for avoiding one" in cq04
        assert "ok but slightly verbose" not in criteria

    def test_scoring_rows_name_the_rule(self) -> None:
        review_row = next(line for line in REVIEW_PROMPT.read_text().splitlines() if line.startswith("| CQ-04 |"))
        assert "No algorithm written out that an available call computes" in review_row
        assert "Name the call and the line range" in review_row
        evaluator = (PROMPTS_DIR / "quality-evaluator.md").read_text()
        evaluator_row = next(line for line in evaluator.splitlines() if line.startswith("| CQ-04 |"))
        assert "No algorithm written out that an available call computes" in evaluator_row
        important = REVIEW_PROMPT.read_text().split("## Important", 1)[1]
        assert "never credit a hand-roll for avoiding one" in important

    def test_generator_has_the_lean_code_section(self) -> None:
        content = (PROMPTS_DIR / "plot-generator.md").read_text()
        section = content[content.index("### Lean code") : content.index("## Visual Quality")]
        assert "never by hand" in section
        assert "never a new helper function" in section
        assert "no code golf" in section
        assert 'Installed packages are not "dependencies" to avoid' in section
        assert "(CQ-04 includes the lean-code rule below)" in content

    def test_regen_prompt_applies_only_a_named_replacement(self) -> None:
        content = (WORKFLOW_PROMPTS_DIR / "impl-generate-claude.md").read_text()
        assert "A `CQ-04` weakness names its replacement: apply exactly that replacement" in content
        assert "Without a CQ-04 weakness, leave computations as they are on a regeneration" in content
        assert "names a call the runtime does not provide" in content

    @pytest.mark.parametrize("filename", JS_LIBRARY_PROMPTS)
    def test_js_library_prompt_has_a_computation_line(self, filename: str) -> None:
        assert "**Computation:**" in (LIBRARY_PROMPTS_DIR / filename).read_text()


class TestAvailablePackages:
    """P8: the per-language "compute with" blocks exist twice — for the
    generator and for the reviewer, which read different files — and both
    copies match each other and what CI installs."""

    @pytest.fixture
    def blocks(self) -> dict[str, str]:
        generator = _language_blocks((PROMPTS_DIR / "plot-generator.md").read_text())
        criteria = _language_blocks((PROMPTS_DIR / "quality-criteria.md").read_text())
        assert set(generator) == set(criteria) == {"Python", "R", "Julia", "JavaScript"}
        return generator

    @pytest.mark.parametrize("language", ["Python", "R", "Julia", "JavaScript"])
    def test_blocks_are_identical(self, language: str) -> None:
        generator = _language_blocks((PROMPTS_DIR / "plot-generator.md").read_text())
        criteria = _language_blocks((PROMPTS_DIR / "quality-criteria.md").read_text())
        assert generator[language] == criteria[language]

    def test_python_block_matches_pyproject(self, blocks: dict[str, str]) -> None:
        project = tomllib.loads((REPO_ROOT / "pyproject.toml").read_text())
        extras = {k: v for k, v in project["project"]["optional-dependencies"].items() if k.startswith("lib-")}

        def names(specs: list[str]) -> set[str]:
            return {re.split(r"[<>=\[; ]", spec, maxsplit=1)[0].lower() for spec in specs}

        shared = set.intersection(*(names(v) for v in extras.values()))
        main = names(project["project"]["dependencies"])
        block = blocks["Python"].lower()
        for package in shared | ({"numpy", "matplotlib"} & main):
            assert package in block, package
        assert "its plotting calls belong only in matplotlib and seaborn implementations" in blocks["Python"]
        installed = set().union(*(names(v) for v in extras.values())) | main
        for package in ("networkx", "squarify", "cartopy"):
            assert package not in installed, package
            assert package in block, package

    def test_r_block_matches_setup_r(self, blocks: dict[str, str]) -> None:
        action = (REPO_ROOT / ".github" / "actions" / "setup-r" / "action.yml").read_text()
        call = action[action.index("install.packages(") : action.index("dependencies =")]
        installed = set(re.findall(r'"([A-Za-z0-9.]+)"', call))
        lead = blocks["R"].splitlines()[1]
        named = set(re.findall(r"\b[A-Za-z][A-Za-z0-9.]+\b", lead.split("their imports")[0]))
        named -= {"and"}
        assert installed == named, sorted(installed ^ named)
        recommended = set(re.findall(r"\(([^)]*)\)", lead)[0].replace(" ", "").split(","))
        assert recommended <= {
            "survival",
            "MASS",
            "class",
            "cluster",
            "lattice",
            "Matrix",
            "nlme",
            "mgcv",
            "KernSmooth",
        }

    def test_julia_block_matches_project_toml(self, blocks: dict[str, str]) -> None:
        deps = set(tomllib.loads((REPO_ROOT / "Project.toml").read_text())["deps"])
        lead = blocks["Julia"].splitlines()[1]
        packages, stdlibs = lead.split(", plus the standard libraries ")
        named = set(re.findall(r"\b[A-Z][A-Za-z]+\b", packages.split(". Examples")[0]))
        assert deps == named, sorted(deps ^ named)
        assert set(re.findall(r"\b[A-Z][A-Za-z]+\b", stdlibs.split(". Examples")[0])) <= {
            "LinearAlgebra",
            "Dates",
            "Printf",
            "Statistics",
            "Random",
        }
        missing = re.search(r"Not loadable: ([^.]*)\.", blocks["Julia"]).group(1)
        assert not set(re.findall(r"\b[A-Z][A-Za-z]+\b", missing)) & deps

    def test_javascript_block_matches_the_render_harness(self, blocks: dict[str, str]) -> None:
        render = (REPO_ROOT / "automation" / "js-render" / "render.mjs").read_text()
        bundles = render[render.index("const BUNDLES = {") : render.index("};", render.index("const BUNDLES = {"))]
        keys = set(re.findall(r"^\s{2}(\w+): \{", bundles, re.MULTILINE))
        listed = re.search(r"Only the snippet's own library is loaded: ([^.]*)\.", blocks["JavaScript"]).group(1)
        assert keys == set(re.findall(r"\b[a-z0-9]+\b", listed)) - {"or"}


CRITERIA_PROMPT = PROMPTS_DIR / "quality-criteria.md"
EVALUATOR_PROMPT = PROMPTS_DIR / "quality-evaluator.md"


class TestFirstReviewScoring:
    """P10: a deduction names its defect, the same gap costs the same
    criterion on every library, a review is blind to earlier ones and writes
    no verdict, and a spec's check values are verified (the 15 first reviews
    of line-tanabe-sugano, 2026-10-01: 7 of 27 deducted technical items had no
    defect line, and a wrong matrix scored DQ-03 at 4/4)."""

    def _section(self, content: str, start: str, end: str) -> str:
        return content[content.index(start) : content.index(end, content.index(start))]

    def test_criteria_start_at_the_maximum_or_the_default(self) -> None:
        principles = self._section(CRITERIA_PROMPT.read_text(), "### Scoring principles", "### Point Distribution")
        assert "Each starts at its **maximum**" in principles
        assert "is carried by a defect line that names that criterion" in principles
        assert "A deduction you cannot write that line for is no deduction" in principles
        assert "Each starts at its **default**" in principles
        assert "You never pick it" in principles
        assert "not your concern" in principles

    def test_review_lists_defects_before_it_scores(self) -> None:
        content = REVIEW_PROMPT.read_text()
        step = self._section(content, "### 7.", "### 8.")
        assert step.index("**List the defects first**") < step.index("**Score the 19 technical items**")
        assert step.index("**Score the 19 technical items**") < step.index("**Score the five judgment items**")
        assert "You never pick the total" in step
        assert "would deduct the same criterion for the same gap" in step
        rules = self._section(content, "### 8a.", "### 8b.")
        assert "every technical item (VQ, SC, DQ, CQ) below its maximum is named by a defect line" in rules
        assert "A suggestion costs no points, and a deducted technical item has a defect line" in rules
        # The DQ-02 guard: a generic-scenario deduction renames, it never replaces the scenario.
        assert "A DQ-02 line names the labels or values that read as generic or abstract, never the domain" in rules
        # The check runs before 8b, so a regeneration's comparison starts from final scores.
        assert "restore the point now, before step 8b and before you write any file" in rules
        assert "From here on your checklist is final" in rules

    def test_step_10_says_how_a_silent_deduction_is_fixed(self) -> None:
        step = REVIEW_PROMPT.read_text().split("### 10.", 1)[1].split("### 11.", 1)[0]
        assert "is fixed by writing the defect line the deduction rests on" in step
        # The checklist example models the rule: its one deducted item names its defect.
        example = step.split("cat > review_checklist.json << 'EOF'\n", 1)[1].split("\nEOF", 1)[0]
        items = re.findall(r'"id": "([A-Z]{2}-\d{2})", "name": "[^"]*", "score": (\d+), "max": (\d+)', example)
        assert items == [("VQ-01", "8", "8"), ("VQ-02", "5", "6")]

    def test_routing_table(self) -> None:
        criteria = CRITERIA_PROMPT.read_text()
        table = self._section(criteria, "### Which criterion a gap belongs to", "## Score Caps")
        rows = [line for line in table.splitlines() if line.startswith("| ") and not line.startswith("| Gap")]
        assert len(rows) == 7
        for gap, verdict in (
            ("A Notes bullet or an `A good version shows:` property that the render misses or breaks", "SC-02 defect"),
            ("A range, size or example of the Data section that the implementation departs from", "Nothing, unless"),
            ("A conditional requirement", "Nothing: not SC-02, not DQ-01"),
            ("names unconditionally", "DQ-01 defect"),
            ("an aspect nothing in the spec names", "At most a `Suggestion:`"),
            ("or a check value missed", "DQ-03 defect"),
            ("A comment or label that contradicts the code or the data it describes", "else CQ-04 defect"),
        ):
            row = next(r for r in rows if gap in r)
            assert verdict in row.split("|")[2], gap
        # Routing, never a threshold.
        assert "how many points it costs stays proportional" in table

    @pytest.mark.parametrize("prompt_path", [REVIEW_PROMPT, EVALUATOR_PROMPT], ids=lambda p: p.name)
    def test_scoring_prompts_name_check_values(self, prompt_path: Path) -> None:
        row = next(line for line in prompt_path.read_text().splitlines() if line.startswith("| DQ-03 |"))
        assert "`Check values:`" in row
        assert "must fall out of the computation" in row
        assert "claim no correctness you did not check" in row

    def test_check_values_rule(self) -> None:
        criteria = CRITERIA_PROMPT.read_text()
        dq03 = self._section(criteria, "### DQ-03", "## Code Quality")
        assert "bullet that starts with `Check values:`" in dq03
        assert "must **fall out of the computation**" in dq03
        assert "is a DQ-03 defect, not a pass" in dq03
        assert "the expected value, the observed value and the signed delta" in dq03
        assert "is skipped, and the comment says so" in dq03
        assert "is a `Suggestion:` that states the doubt, not a deduction" in dq03
        template = (PROMPTS_DIR / "templates" / "specification.md").read_text()
        notes = self._section(template, "## Notes", "## What a good version looks like")
        assert "`Check values:`" in notes and "never hard-coded" in notes

    def test_cq04_examples_are_not_a_whitelist(self) -> None:
        criteria = CRITERIA_PROMPT.read_text()
        row = next(line for line in criteria.splitlines() if line.startswith("| 1 | A named block"))
        assert "a fit," not in row
        assert "a fit that takes an iteration or a matrix solve" in row
        assert "The examples are not a list to match against" in row
        assert "makes a closed-form slope and intercept a suggestion" in row

    def test_the_review_is_blind_and_writes_no_verdict(self) -> None:
        content = REVIEW_PROMPT.read_text()
        assert "### Verdict" not in content and "review_verdict.txt" not in content
        assert "verdict = REJECTED" not in content
        assert "it does not change how you score" in content
        assert "review 1 of up to 5" not in content
        important = content.split("## Important", 1)[1]
        assert "Do not open earlier review comments on the pull request" in important
        assert "You write no verdict" in important
        # 8b still needs to say that a regeneration has one review and no repair.
        assert "and no repair loop" in content
        assert "there is no repair: the regen gate reads the same file" in content
        evaluator = EVALUATOR_PROMPT.read_text()
        assert '"pass"' not in evaluator and '"recommendation"' not in evaluator
        assert "Determine Recommendation" not in evaluator

    @pytest.mark.parametrize("prompt_path", [CRITERIA_PROMPT, REVIEW_PROMPT, EVALUATOR_PROMPT], ids=lambda p: p.name)
    def test_compliance_is_not_excellence(self, prompt_path: Path) -> None:
        """R4: what the spec or the style guide requires raises no DE or LM item."""
        content = prompt_path.read_text()
        assert "Compliance is not excellence" in content
        assert (
            "**beyond** what the spec's Notes and characteristic section require and beyond what the style guide "
            "mandates (removed top and right spines, a subtle grid, theme tokens, the Imprint palette, explicit "
            "font sizes)"
        ) in content
        assert "Meeting those is scored in SC and VQ" in content
        assert "The complete style-guide baseline earns exactly the defaults" in content.replace("**", "")
        # No ladder or check credits a mandated or a forbidden thing any more.
        for phrase in ("custom palette", "Custom palette", "Spines removed?", "spines partially removed"):
            assert phrase not in content, phrase
        assert "Raise only if spines removed" not in content

    def test_design_ladders_start_at_the_baseline(self) -> None:
        criteria = CRITERIA_PROMPT.read_text()
        de01 = self._section(criteria, "### DE-01", "### DE-02")
        assert (
            "| 8 | Publication-ready: typography, spacing and hierarchy decided beyond the baseline, within the" in de01
        )
        assert "| 4 | The complete style-guide baseline" in de01
        de02 = self._section(criteria, "### DE-02", "### DE-03")
        assert "| 6 | Perfect: every detail decided rather than inherited" in de02
        assert "| 4 | Good: refinement beyond the style-guide baseline" in de02
        assert "| 2 | The style-guide baseline" in de02
        assert "subtle grid (or none), spines removed" not in criteria
        # The 75 cap needs both items at 2 or below; the baseline keeps DE-01 at 4.
        caps = self._section(criteria, "## Score Caps", "## Anti-Inflation")
        assert "this cap never fires on a compliant implementation" in caps
        assert "A hierarchy the spec's Notes prescribe" in self._section(criteria, "### DE-03", "## Spec Compliance")
        assert "Compliance is not mastery" in self._section(criteria, "## Library Mastery", "## Plot-Type")

    def test_stale_distribution_is_gone_and_the_anchors_stay(self) -> None:
        criteria = CRITERIA_PROMPT.read_text()
        assert "Expected distribution" not in criteria
        assert "When in doubt, deduct" not in criteria
        assert "When in doubt whether evidence raises a design or library item, keep the default" in criteria
        assert "Median implementation should score 72-78" in criteria
        assert "median implementation should score 72-78" in REVIEW_PROMPT.read_text()
