#!/usr/bin/env python3
"""
Local Plot Quality Evaluator (v2)

Two-stage evaluation:
1. Auto-Reject: Quick checks (Syntax, Runtime, Output, Library usage)
2. Quality: AI-based scoring (0-100)

Usage:
    # Quick auto-reject check (no API)
    python scripts/evaluate-plot.py scatter-basic matplotlib --quick

    # Full evaluation with AI
    python scripts/evaluate-plot.py scatter-basic matplotlib

    # Generate plot before evaluating
    python scripts/evaluate-plot.py scatter-basic matplotlib --generate

    # Evaluate all libraries
    python scripts/evaluate-plot.py scatter-basic --all --quick
"""

import argparse
import ast
import json
import os
import subprocess
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

# Local imports must come AFTER sys.path is patched so the script remains
# runnable from any working directory (Copilot review: PR #5414).
from core.config import settings  # noqa: E402

SUPPORTED_LIBRARIES = [
    "matplotlib", "seaborn", "plotly", "bokeh", "altair",
    "plotnine", "pygal", "highcharts", "letsplot",
]

# Library-specific plot function patterns
LIBRARY_PATTERNS = {
    "seaborn": {
        "import": ["import seaborn", "from seaborn"],
        "plot_functions": [
            "sns.scatterplot", "sns.lineplot", "sns.barplot", "sns.histplot",
            "sns.boxplot", "sns.violinplot", "sns.heatmap", "sns.pairplot",
            "sns.relplot", "sns.catplot", "sns.displot", "sns.jointplot",
            "sns.regplot", "sns.lmplot", "sns.countplot", "sns.kdeplot",
            "sns.stripplot", "sns.swarmplot", "sns.pointplot", "sns.rugplot",
            "sns.clustermap", "sns.FacetGrid",
        ],
        "style_only": ["sns.set_style", "sns.set_theme", "sns.set_context", "sns.set_palette", "sns.despine"],
    },
    "plotly": {
        "import": ["import plotly", "from plotly"],
        "plot_functions": [
            "px.scatter", "px.line", "px.bar", "px.histogram", "px.box",
            "px.violin", "px.pie", "px.sunburst", "px.treemap", "px.funnel",
            "px.choropleth", "px.density_heatmap", "px.imshow",
            "go.Figure", "go.Scatter", "go.Bar", "go.Heatmap", "go.Pie",
            "go.Candlestick", "go.Ohlc", "go.Sankey", "go.Choropleth",
        ],
        "style_only": [],
    },
    "bokeh": {
        "import": ["from bokeh", "import bokeh"],
        "plot_functions": [
            "figure(", ".scatter(", ".line(", ".circle(", ".square(",
            ".triangle(", ".vbar(", ".hbar(", ".rect(", ".segment(",
            ".multi_line(", ".patch(", ".patches(", ".quad(",
        ],
        "style_only": [],
    },
    "altair": {
        "import": ["import altair", "from altair"],
        "plot_functions": [
            "alt.Chart", ".mark_point", ".mark_line", ".mark_bar", ".mark_circle",
            ".mark_square", ".mark_rect", ".mark_area", ".mark_boxplot",
            ".mark_rule", ".mark_text", ".mark_geoshape",
        ],
        "style_only": [".configure_"],
    },
    "plotnine": {
        "import": ["from plotnine", "import plotnine"],
        "plot_functions": [
            "ggplot(", "geom_point", "geom_line", "geom_bar", "geom_histogram",
            "geom_boxplot", "geom_violin", "geom_area", "geom_tile",
            "geom_col", "geom_density", "geom_smooth", "geom_text",
        ],
        "style_only": ["theme(", "theme_"],
    },
    "pygal": {
        "import": ["import pygal", "from pygal"],
        "plot_functions": [
            "pygal.Bar", "pygal.Line", "pygal.Pie", "pygal.Histogram",
            "pygal.XY", "pygal.Dot", "pygal.Radar", "pygal.Box",
            "pygal.Treemap", "pygal.Gauge", "pygal.StackedBar",
        ],
        "style_only": [],
    },
    "highcharts": {
        "import": ["from highcharts", "import highcharts"],
        "plot_functions": [
            "Chart(", "Highcharts", "highcharts.Chart",
            "HighchartsStockChart", "HighchartsMapsChart",
        ],
        "style_only": [],
    },
    "letsplot": {
        "import": ["from lets_plot", "import lets_plot"],
        "plot_functions": [
            "ggplot(", "geom_point", "geom_line", "geom_bar", "geom_histogram",
            "geom_boxplot", "geom_violin", "geom_area", "geom_tile",
            "geom_density", "geom_smooth", "geom_text", "geom_polygon",
        ],
        "style_only": ["theme(", "ggsize(", "flavor_"],
    },
    "matplotlib": {
        "import": ["import matplotlib", "from matplotlib"],
        "plot_functions": [
            "ax.scatter", "ax.plot", "ax.bar", "ax.hist", "ax.boxplot",
            "plt.scatter", "plt.plot", "plt.bar", "plt.hist", "plt.boxplot",
            "ax.imshow", "ax.contour", "ax.pie", "ax.fill_between",
            "ax.errorbar", "ax.violinplot", "ax.hexbin", "ax.pcolormesh",
            "ax.quiver", "ax.streamplot", "ax.stem", "ax.step",
        ],
        "style_only": [],
    },
}


def get_plot_paths(spec_id: str, library: str) -> dict:
    """Get all relevant paths for a plot implementation."""
    plots_dir = PROJECT_ROOT / "plots" / spec_id
    return {
        "spec": plots_dir / "specification.md",
        "impl": plots_dir / "implementations" / f"{library}.py",
        "metadata": plots_dir / "metadata" / f"{library}.yaml",
        "image": plots_dir / "implementations" / "plot.png",
        "library_rules": PROJECT_ROOT / "prompts" / "library" / f"{library}.md",
        "quality_criteria": PROJECT_ROOT / "prompts" / "quality-criteria.md",
    }


# =============================================================================
# STAGE 1: AUTO-REJECT CHECKS
# =============================================================================

class AutoRejectResult:
    """Result of an auto-reject check."""
    def __init__(self, passed: bool, code: str, message: str):
        self.passed = passed
        self.code = code
        self.message = message

    def __repr__(self):
        status = "PASS" if self.passed else "FAIL"
        return f"{self.code}: {status} - {self.message}"


def check_ar01_syntax(impl_path: Path) -> AutoRejectResult:
    """AR-01: Check if code has syntax errors."""
    try:
        with open(impl_path) as f:
            code = f.read()
        ast.parse(code)
        return AutoRejectResult(True, "AR-01", "Syntax OK")
    except SyntaxError as e:
        return AutoRejectResult(False, "AR-01", f"Syntax error: {e}")


def check_ar02_runtime(impl_path: Path, timeout: int = 60) -> AutoRejectResult:
    """AR-02: Check if code runs without exceptions."""
    env = os.environ.copy()
    env["MPLBACKEND"] = "Agg"

    # Create a temp copy to run from a clean directory (avoids matplotlib.py shadowing)
    import tempfile
    import shutil
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_script = Path(tmpdir) / "plot_script.py"
        shutil.copy(impl_path, tmp_script)

        try:
            result = subprocess.run(
                [sys.executable, str(tmp_script)],
                cwd=tmpdir,
                env=env,
                capture_output=True,
                text=True,
                timeout=timeout,
            )
            if result.returncode == 0:
                # Copy plot.png back if created
                tmp_plot = Path(tmpdir) / "plot.png"
                if tmp_plot.exists():
                    shutil.copy(tmp_plot, impl_path.parent / "plot.png")
                return AutoRejectResult(True, "AR-02", "Runtime OK")
            else:
                # Get last line of error
                error_lines = result.stderr.strip().split('\n')
                error_msg = error_lines[-1] if error_lines else "Unknown error"
                return AutoRejectResult(False, "AR-02", f"Runtime error: {error_msg[:100]}")
        except subprocess.TimeoutExpired:
            return AutoRejectResult(False, "AR-02", f"Timeout after {timeout}s")
        except Exception as e:
            return AutoRejectResult(False, "AR-02", f"Execution failed: {e}")


def check_ar03_output(impl_path: Path) -> AutoRejectResult:
    """AR-03: Check if plot.png was created."""
    plot_path = impl_path.parent / "plot.png"
    if plot_path.exists():
        return AutoRejectResult(True, "AR-03", f"Output exists: {plot_path.name}")
    else:
        return AutoRejectResult(False, "AR-03", "No plot.png created")


def check_ar04_empty(impl_path: Path) -> AutoRejectResult:
    """AR-04: Check if plot.png is not empty (< 10KB or mostly white)."""
    plot_path = impl_path.parent / "plot.png"
    if not plot_path.exists():
        return AutoRejectResult(False, "AR-04", "No plot.png to check")

    # Check file size
    size_kb = plot_path.stat().st_size / 1024
    if size_kb < 10:
        return AutoRejectResult(False, "AR-04", f"Plot too small: {size_kb:.1f}KB")

    # Try to check if mostly white (optional, requires PIL)
    try:
        from PIL import Image
        import numpy as np
        img = Image.open(plot_path).convert('RGB')
        arr = np.array(img)
        # Check if > 95% of pixels are white (> 250 in all channels)
        white_pixels = np.all(arr > 250, axis=2).sum()
        total_pixels = arr.shape[0] * arr.shape[1]
        white_ratio = white_pixels / total_pixels
        if white_ratio > 0.95:
            return AutoRejectResult(False, "AR-04", f"Plot is {white_ratio*100:.0f}% white")
    except ImportError:
        pass  # PIL not available, skip this check

    return AutoRejectResult(True, "AR-04", f"Plot OK ({size_kb:.0f}KB)")


def check_ar05_library(impl_path: Path, library: str) -> AutoRejectResult:
    """AR-05: Check if library plot functions are actually used."""
    if library not in LIBRARY_PATTERNS:
        return AutoRejectResult(True, "AR-05", f"Unknown library: {library}")

    with open(impl_path) as f:
        code = f.read()

    patterns = LIBRARY_PATTERNS[library]

    # Check if library is imported
    has_import = any(p in code for p in patterns["import"])
    if not has_import:
        return AutoRejectResult(False, "AR-05", f"No {library} import found")

    # Check for plot functions
    plot_functions_used = [p for p in patterns["plot_functions"] if p in code]
    style_only_used = [p for p in patterns["style_only"] if p in code]

    if plot_functions_used:
        funcs = ", ".join(plot_functions_used[:3])
        return AutoRejectResult(True, "AR-05", f"Uses: {funcs}")
    elif style_only_used:
        funcs = ", ".join(style_only_used[:2])
        return AutoRejectResult(False, "AR-05", f"Only styling: {funcs}")
    else:
        return AutoRejectResult(False, "AR-05", f"{library} imported but no plot functions used")


def check_ar07_format(impl_path: Path, library: str) -> AutoRejectResult:
    """AR-07: Check if output format is correct."""
    # Static libraries should produce .png
    static_libraries = ["matplotlib", "seaborn", "plotnine"]
    # Interactive libraries can produce .png or .html
    interactive_libraries = ["plotly", "bokeh", "altair", "pygal", "highcharts", "letsplot"]

    plot_png = impl_path.parent / "plot.png"
    plot_html = impl_path.parent / "plot.html"

    if library in static_libraries:
        if plot_png.exists():
            return AutoRejectResult(True, "AR-07", "Correct format: PNG")
        else:
            return AutoRejectResult(False, "AR-07", "Static library must produce PNG")
    else:
        if plot_png.exists() or plot_html.exists():
            fmt = "PNG" if plot_png.exists() else "HTML"
            return AutoRejectResult(True, "AR-07", f"Correct format: {fmt}")
        else:
            return AutoRejectResult(False, "AR-07", "No valid output format")


def run_auto_reject_checks(spec_id: str, library: str, run_code: bool = True) -> dict:
    """Run all auto-reject checks and return results."""
    paths = get_plot_paths(spec_id, library)
    impl_path = paths["impl"]

    if not impl_path.exists():
        return {
            "passed": False,
            "failed_check": "FILE",
            "message": f"Implementation not found: {impl_path}",
            "checks": [],
        }

    checks = []

    # AR-01: Syntax
    ar01 = check_ar01_syntax(impl_path)
    checks.append(ar01)
    if not ar01.passed:
        return {"passed": False, "failed_check": "AR-01", "message": ar01.message, "checks": checks}

    # AR-02: Runtime (optional - can be slow)
    if run_code:
        ar02 = check_ar02_runtime(impl_path)
        checks.append(ar02)
        if not ar02.passed:
            return {"passed": False, "failed_check": "AR-02", "message": ar02.message, "checks": checks}

        # AR-03: Output exists
        ar03 = check_ar03_output(impl_path)
        checks.append(ar03)
        if not ar03.passed:
            return {"passed": False, "failed_check": "AR-03", "message": ar03.message, "checks": checks}

        # AR-04: Not empty
        ar04 = check_ar04_empty(impl_path)
        checks.append(ar04)
        if not ar04.passed:
            return {"passed": False, "failed_check": "AR-04", "message": ar04.message, "checks": checks}

        # AR-07: Correct format
        ar07 = check_ar07_format(impl_path, library)
        checks.append(ar07)
        if not ar07.passed:
            return {"passed": False, "failed_check": "AR-07", "message": ar07.message, "checks": checks}

    # AR-05: Library usage
    ar05 = check_ar05_library(impl_path, library)
    checks.append(ar05)
    if not ar05.passed:
        return {"passed": False, "failed_check": "AR-05", "message": ar05.message, "checks": checks}

    return {"passed": True, "failed_check": None, "message": "All checks passed", "checks": checks}


# =============================================================================
# STAGE 2: QUALITY EVALUATION
# =============================================================================

def create_evaluation_prompt(spec_id: str, library: str, paths: dict) -> str:
    """Create the evaluation prompt for Claude (v2 criteria)."""
    spec_content = paths["spec"].read_text() if paths["spec"].exists() else "NOT FOUND"
    impl_content = paths["impl"].read_text() if paths["impl"].exists() else "NOT FOUND"
    criteria_content = paths["quality_criteria"].read_text() if paths["quality_criteria"].exists() else "NOT FOUND"
    library_rules = paths["library_rules"].read_text() if paths["library_rules"].exists() else ""

    return f"""## Task: Evaluate Plot Quality (v2 Criteria)

You are evaluating a **{library}** implementation of **{spec_id}**.

**Important:** This implementation has already passed Auto-Reject checks (syntax, runtime, output, library usage).
Focus purely on QUALITY evaluation.

### Specification
```markdown
{spec_content}
```

### Implementation ({library}.py)
```python
{impl_content}
```

### Library Rules
```markdown
{library_rules}
```

### Quality Criteria
```markdown
{criteria_content}
```

### Your Task

Evaluate STRICTLY. Remember:
- 90-100 = Publication quality (Nature/Science)
- 70-89 = Professional
- 50-69 = Acceptable
- <50 = Rejected

Provide evaluation as JSON:

```json
{{
  "score": <0-100>,
  "tier": "<Excellent|Good|Acceptable|Poor>",

  "visual_quality": {{
    "vq01_text_legibility": {{"score": <0-10>, "note": "..."}},
    "vq02_no_overlap": {{"score": <0-8>, "note": "..."}},
    "vq03_element_visibility": {{"score": <0-8>, "note": "..."}},
    "vq04_color_accessibility": {{"score": <0-5>, "note": "..."}},
    "vq05_layout_balance": {{"score": <0-5>, "note": "..."}},
    "vq06_axis_labels": {{"score": <0-2>, "note": "..."}},
    "vq07_grid_legend": {{"score": <0-2>, "note": "..."}},
    "total": <0-40>
  }},

  "spec_compliance": {{
    "sc01_plot_type": {{"score": <0-8>, "note": "..."}},
    "sc02_data_mapping": {{"score": <0-5>, "note": "..."}},
    "sc03_required_features": {{"score": <0-5>, "note": "..."}},
    "sc04_data_range": {{"score": <0-3>, "note": "..."}},
    "sc05_legend_accuracy": {{"score": <0-2>, "note": "..."}},
    "sc06_title_format": {{"score": <0-2>, "note": "..."}},
    "total": <0-25>
  }},

  "data_quality": {{
    "dq01_feature_coverage": {{"score": <0-8>, "note": "..."}},
    "dq02_realistic_context": {{"score": <0-7>, "note": "..."}},
    "dq03_appropriate_scale": {{"score": <0-5>, "note": "..."}},
    "total": <0-20>
  }},

  "code_quality": {{
    "cq01_kiss_structure": {{"score": <0-3>, "note": "..."}},
    "cq02_reproducibility": {{"score": <0-3>, "note": "..."}},
    "cq03_clean_imports": {{"score": <0-2>, "note": "..."}},
    "cq04_no_deprecated_api": {{"score": <0-1>, "note": "..."}},
    "cq05_output_correct": {{"score": <0-1>, "note": "..."}},
    "total": <0-10>
  }},

  "library_features": {{
    "lf01_distinctive_features": {{"score": <0-5>, "note": "..."}},
    "total": <0-5>
  }},

  "strengths": ["..."],
  "weaknesses": ["..."],
  "improvements": ["..."],
  "summary": "One sentence summary"
}}
```

Be STRICT - a "good" plot should score around 70-80, not 95.
"""


def evaluate_with_claude(prompt: str, image_path: Path | None = None) -> dict:
    """Send the evaluation prompt to Claude API.

    Returns one of three shapes:
      - success: parsed quality result dict (has `score`, `tier`, etc.)
      - API failure: `{"error": str, "error_type": "missing_dep" | "missing_key" | "api_error", ...}`
      - parse failure (API call succeeded but response isn't valid fenced JSON):
        `{"error": str, "error_type": "json_parse_failure" | "no_json_block", "raw_response": str}`
    """
    try:
        import anthropic
    except ImportError:
        return {"error": "anthropic package not installed. Run: pip install anthropic", "error_type": "missing_dep"}

    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        return {"error": "ANTHROPIC_API_KEY not set", "error_type": "missing_key"}

    # timeout caps a single request; SDK default max_retries is fine here.
    client = anthropic.Anthropic(api_key=api_key, timeout=300.0)
    content = [{"type": "text", "text": prompt}]

    if image_path and image_path.exists():
        import base64
        with open(image_path, "rb") as f:
            image_data = base64.standard_b64encode(f.read()).decode("utf-8")
        content.insert(0, {
            "type": "image",
            "source": {"type": "base64", "media_type": "image/png", "data": image_data}
        })
        content.insert(1, {"type": "text", "text": "Plot image to evaluate:"})

    try:
        response = client.messages.create(
            model=settings.claude_model,
            max_tokens=4096,
            messages=[{"role": "user", "content": content}],
        )
    except anthropic.APIError as e:
        # RateLimitError / APIStatusError / APITimeoutError / APIConnectionError all subclass APIError.
        return {"error": str(e), "error_type": "api_error", "exception": type(e).__name__}

    response_text = response.content[0].text

    import re
    json_match = re.search(r'```json\s*(.*?)\s*```', response_text, re.DOTALL)
    if json_match is None:
        return {
            "error": "Response contained no ```json fenced block",
            "error_type": "no_json_block",
            "raw_response": response_text,
        }
    try:
        return json.loads(json_match.group(1))
    except json.JSONDecodeError as e:
        return {
            "error": f"Failed to parse JSON from fenced block: {e}",
            "error_type": "json_parse_failure",
            "raw_response": response_text,
        }


# =============================================================================
# OUTPUT FORMATTING
# =============================================================================

def print_auto_reject_result(result: dict):
    """Print auto-reject check results."""
    if result["passed"]:
        print("\n✅ AUTO-REJECT: PASSED")
    else:
        print(f"\n❌ AUTO-REJECT: FAILED ({result['failed_check']})")
        print(f"   {result['message']}")

    print("\nChecks:")
    for check in result["checks"]:
        status = "✓" if check.passed else "✗"
        print(f"  {status} {check}")


def print_quality_result(result: dict, verbose: bool = False):
    """Print quality evaluation results."""
    if "error" in result:
        error_type = result.get("error_type", "error")
        print(f"\n❌ {error_type}: {result['error']}")
        # For parse failures the API call succeeded — show what came back so the user can debug.
        if "raw_response" in result:
            print("\nRaw response from model:")
            print(result["raw_response"])
        return

    score = result.get("score", 0)
    tier = result.get("tier", "Unknown")

    print("\n" + "="*60)
    print(f"QUALITY SCORE: {score}/100 ({tier})")
    print("="*60)

    # Category scores
    vq = result.get("visual_quality", {}).get("total", "?")
    sc = result.get("spec_compliance", {}).get("total", "?")
    dq = result.get("data_quality", {}).get("total", "?")
    cq = result.get("code_quality", {}).get("total", "?")
    lf = result.get("library_features", {}).get("total", "?")

    print(f"\n  Visual Quality:    {vq}/40")
    print(f"  Spec Compliance:   {sc}/25")
    print(f"  Data Quality:      {dq}/20")
    print(f"  Code Quality:      {cq}/10")
    print(f"  Library Features:  {lf}/5")

    if verbose:
        for category in ["visual_quality", "spec_compliance", "data_quality", "code_quality", "library_features"]:
            cat_data = result.get(category, {})
            print(f"\n{category.upper()}:")
            for key, val in cat_data.items():
                if key != "total" and isinstance(val, dict):
                    print(f"    {key}: {val.get('score', '?')} - {val.get('note', '')[:50]}")

    if result.get("strengths"):
        print("\n+ Strengths:")
        for s in result["strengths"][:3]:
            print(f"    {s}")

    if result.get("weaknesses"):
        print("\n- Weaknesses:")
        for w in result["weaknesses"][:3]:
            print(f"    {w}")

    print(f"\nSummary: {result.get('summary', 'N/A')}")


# =============================================================================
# MAIN
# =============================================================================

def main():
    parser = argparse.ArgumentParser(
        description="Evaluate plot implementation (v2: Auto-Reject + Quality)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("spec_id", help="Specification ID (e.g., scatter-basic)")
    parser.add_argument("library", nargs="?", help="Library name (e.g., matplotlib)")
    parser.add_argument("--all", action="store_true", help="Evaluate all libraries")
    parser.add_argument("--quick", "-q", action="store_true", help="Only run auto-reject (no AI)")
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")
    parser.add_argument("--generate", "-g", action="store_true", help="Generate plot before evaluation")
    parser.add_argument("--no-run", action="store_true", help="Skip runtime check (faster)")
    parser.add_argument("--json", action="store_true", help="Output as JSON")

    args = parser.parse_args()

    libraries = SUPPORTED_LIBRARIES if args.all else ([args.library] if args.library else None)
    if not libraries:
        parser.error("Must specify a library or use --all")

    all_results = {}

    for library in libraries:
        print(f"\n{'='*60}")
        print(f"Evaluating: {args.spec_id} / {library}")
        print("="*60)

        paths = get_plot_paths(args.spec_id, library)

        if not paths["impl"].exists():
            print(f"⚠ Skipping: implementation not found")
            continue

        # Generate plot if requested
        if args.generate:
            print("\nGenerating plot...")
            import tempfile
            import shutil
            env = os.environ.copy()
            env["MPLBACKEND"] = "Agg"
            with tempfile.TemporaryDirectory() as tmpdir:
                tmp_script = Path(tmpdir) / "plot_script.py"
                shutil.copy(paths["impl"], tmp_script)
                subprocess.run(
                    [sys.executable, str(tmp_script)],
                    cwd=tmpdir,
                    env=env,
                    capture_output=True,
                    timeout=60,
                )
                tmp_plot = Path(tmpdir) / "plot.png"
                if tmp_plot.exists():
                    shutil.copy(tmp_plot, paths["impl"].parent / "plot.png")

        # Stage 1: Auto-Reject
        print("\n--- STAGE 1: AUTO-REJECT ---")
        ar_result = run_auto_reject_checks(args.spec_id, library, run_code=not args.no_run)
        print_auto_reject_result(ar_result)

        result = {"auto_reject": ar_result}

        if not ar_result["passed"]:
            result["score"] = 0
            result["tier"] = "Rejected"
            result["verdict"] = f"AUTO-REJECT: {ar_result['failed_check']}"
        elif not args.quick:
            # Stage 2: Quality (only if auto-reject passed)
            print("\n--- STAGE 2: QUALITY EVALUATION ---")
            prompt = create_evaluation_prompt(args.spec_id, library, paths)

            image_path = paths["image"] if paths["image"].exists() else None
            quality_result = evaluate_with_claude(prompt, image_path)
            result["quality"] = quality_result

            if not args.json:
                print_quality_result(quality_result, verbose=args.verbose)

        all_results[library] = result

    if args.json:
        # Clean up for JSON output
        for lib, res in all_results.items():
            if "auto_reject" in res:
                res["auto_reject"]["checks"] = [str(c) for c in res["auto_reject"]["checks"]]
        print(json.dumps(all_results, indent=2))


if __name__ == "__main__":
    main()
