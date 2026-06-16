"""
Central constants and configuration for the anyplot project.

This module provides a single source of truth for library definitions,
labels, and other constants used throughout the application.
"""

from __future__ import annotations


# =============================================================================
# SUPPORTED PLOTTING LIBRARIES
# =============================================================================

# Canonical set of all supported plotting libraries (IDs)
SUPPORTED_LIBRARIES = frozenset(
    [
        "altair",
        "bokeh",
        "chartjs",
        "d3",
        "echarts",
        "ggplot2",
        "highcharts",
        "letsplot",
        "makie",
        "matplotlib",
        "muix",
        "plotly",
        "plotnine",
        "pygal",
        "seaborn",
    ]
)

# Supported programming languages
SUPPORTED_LANGUAGES = frozenset(["python", "r", "julia", "javascript"])

# Language metadata for database seeding (analog to LIBRARIES_METADATA)
LANGUAGES_METADATA = [
    {
        "id": "python",
        "name": "Python",
        "file_extension": ".py",
        "runtime_version": "3.13",
        "documentation_url": "https://www.python.org",
        "description": "General-purpose, high-level programming language with a clean, readable syntax. The lingua franca of data science, scientific computing, and the SciPy / PyData ecosystem.",
    },
    {
        "id": "r",
        "name": "R",
        "file_extension": ".R",
        "runtime_version": "4.4",
        "documentation_url": "https://www.r-project.org",
        "description": "Language and environment for statistical computing and graphics. Widely used in academia, biotech, and finance research, with a rich package ecosystem on CRAN.",
    },
    {
        "id": "julia",
        "name": "Julia",
        "file_extension": ".jl",
        "runtime_version": "1.11",
        "documentation_url": "https://julialang.org",
        "description": "High-level, high-performance dynamic language for technical computing. Combines the productivity of Python/R with the speed of compiled languages; popular in scientific computing, numerical analysis, and machine learning research.",
    },
    {
        "id": "javascript",
        "name": "JavaScript",
        "file_extension": ".js",
        # Node 22 LTS — the runtime that drives the browser render harness
        # (automation/js-render/render.mjs). Confirm against CI on first run.
        "runtime_version": "22",
        "documentation_url": "https://developer.mozilla.org/en-US/docs/Web/JavaScript",
        "description": "The language of the web. Every dashboard, embed, and BI tool renders charts in the browser via JavaScript. anyplot authors snippets in plain JS (TSX for React-only libraries); TypeScript is treated as the same language.",
    },
]

# Map from language id → default file extension used by sync_to_postgres for
# discovery. This is the 1:1 language→extension default; libraries that diverge
# from it declare a per-library "file_extension" in LIBRARIES_METADATA (see
# LIBRARY_FILE_EXTENSION_OVERRIDES / language_file_extensions below).
LANGUAGE_FILE_EXTENSIONS = {lang["id"]: lang["file_extension"] for lang in LANGUAGES_METADATA}

# Library metadata for database seeding and display.
#
# `framework` (default "none") models the UI-framework runtime constraint a
# library imposes — one of: none | react | vue | svelte | angular. It lets a
# single `javascript` language entry cover both framework-agnostic libs and
# React-only libs (e.g. a future MUI X entry) without duplicating the registry
# or inventing per-framework "languages" (see docs/concepts/library-expansion.md
# §6). All Phase-1 JS libraries are framework-agnostic ("none").
#
# `file_extension` is an OPTIONAL per-library override of the language default
# (LANGUAGE_FILE_EXTENSIONS). Most libraries omit it and inherit the default
# (.py / .R / .jl / .js). It exists because JavaScript breaks the 1:1
# language→extension assumption: framework-agnostic JS libs are `.js`, but the
# React lib MUI X (`muix`) is `.tsx`. MUI X is the first — and currently only —
# library to set it; the mechanism is wired through language_file_extensions() +
# sync_to_postgres so JavaScript discovery scans both `.js` and `.tsx`.
LIBRARIES_METADATA = [
    {
        "id": "altair",
        "name": "Altair",
        "language_id": "python",
        "framework": "none",
        "version": "5.2.0",
        "documentation_url": "https://altair-viz.github.io",
        "description": "Declarative visualization library for Python. Its simple, friendly and consistent API, built on top of the powerful Vega-Lite grammar, empowers you to spend less time writing code and more time exploring your data.",
    },
    {
        "id": "bokeh",
        "name": "Bokeh",
        "language_id": "python",
        "framework": "none",
        "version": "3.4.0",
        "documentation_url": "https://bokeh.org",
        "description": "Interactive visualization library that makes it simple to create common plots, while also handling custom or specialized use-cases. Work in Python close to all the PyData tools you're already familiar with.",
    },
    {
        "id": "chartjs",
        "name": "Chart.js",
        "language_id": "javascript",
        "framework": "none",
        "version": "4.4.7",
        "documentation_url": "https://www.chartjs.org",
        "description": "Simple yet flexible HTML5-canvas charting. The most popular open-source JavaScript charting library; eight core chart types, responsive, animated.",
    },
    {
        "id": "d3",
        "name": "D3.js",
        "language_id": "javascript",
        "framework": "none",
        "version": "7.9.0",
        "documentation_url": "https://d3js.org",
        "description": "Data-Driven Documents. The low-level standard for bespoke, SVG-based data visualization on the web — bind data to the DOM and apply data-driven transformations. Maximum control, steep curve.",
    },
    {
        "id": "echarts",
        "name": "Apache ECharts",
        "language_id": "javascript",
        "framework": "none",
        "version": "5.5.1",
        "documentation_url": "https://echarts.apache.org",
        "description": "Powerful, interactive charting and data-visualization library for the browser. Apache-licensed, Canvas/SVG rendering, an enormous catalog of chart types.",
    },
    {
        "id": "ggplot2",
        "name": "ggplot2",
        "language_id": "r",
        "framework": "none",
        "version": "3.5.1",
        "documentation_url": "https://ggplot2.tidyverse.org",
        "description": "The de facto standard for data visualization in R. ggplot2 is an implementation of the grammar of graphics: declarative, layered charts that compose with a small set of primitives (geoms, aesthetics, scales, facets, themes).",
    },
    {
        # Migrated Python → JavaScript (library-expansion.md §6, "most-used variant"):
        # native highcharts.js (~1 M npm downloads/wk) vastly outweighs the
        # highcharts-core Python wrapper (~5 k/wk), so the canonical entry is the JS
        # library, rendered through the browser harness like the Phase-1 JS libs.
        "id": "highcharts",
        "name": "Highcharts",
        "language_id": "javascript",
        "framework": "none",
        "version": "12.6.0",
        "documentation_url": "https://www.highcharts.com",
        "description": "The industry-standard JavaScript charting library for finance, news, and BI dashboards — SVG-rendered, endlessly flexible, battle-tested. Commercial license, free for non-commercial use.",
    },
    {
        "id": "letsplot",
        "name": "lets-plot",
        "language_id": "python",
        "framework": "none",
        "version": "4.5.0",
        "documentation_url": "https://lets-plot.org",
        "description": "Multiplatform plotting library built on the principles of the Grammar of Graphics. A faithful adaptation of R's ggplot2 that extends Grammar of Graphics principles to both Python and Kotlin.",
    },
    {
        "id": "makie",
        "name": "Makie.jl",
        "language_id": "julia",
        "framework": "none",
        "version": "0.22",
        "documentation_url": "https://docs.makie.org",
        "description": "High-performance, extensible visualization ecosystem for Julia. CairoMakie renders publication-quality static PNG/SVG/PDF; GLMakie/WGLMakie handle interactive use. anyplot uses CairoMakie for the static gallery.",
    },
    {
        "id": "matplotlib",
        "name": "Matplotlib",
        "language_id": "python",
        "framework": "none",
        "version": "3.9.0",
        "documentation_url": "https://matplotlib.org",
        "description": "Comprehensive library for creating static, animated, and interactive visualizations in Python. Matplotlib makes easy things easy and hard things possible.",
    },
    {
        # First React (framework != none) and first `.tsx` entry — the real
        # end-to-end test of both the `framework` field and the per-library
        # file_extension override (both stood up in Phase 1). language_id stays
        # `javascript`: React is a runtime constraint, not a language
        # (library-expansion.md §6). Rendered through the Node + Playwright
        # harness, but via its esbuild `framework: react` branch (snippet is a
        # default-exported component, bundled with react + @mui, mounted in a MUI
        # ThemeProvider) — not the UMD-global path the other JS libs use.
        # Community @mui/x-charts only (MIT); Pro/Premium are out of scope (§9).
        "id": "muix",
        "name": "MUI X Charts",
        "language_id": "javascript",
        "framework": "react",
        "version": "7.29.1",
        "documentation_url": "https://mui.com/x/react-charts/",
        "file_extension": ".tsx",  # per-library override; the JavaScript default is .js
        "description": "Charting components for the MUI (Material UI) React ecosystem. The community @mui/x-charts package (MIT) covers bar, line, pie, scatter and more. anyplot uses only the MIT community surface; Pro/Premium features are out of scope.",
    },
    {
        "id": "plotly",
        "name": "Plotly",
        "language_id": "python",
        "framework": "none",
        "version": "5.18.0",
        "documentation_url": "https://plotly.com/python",
        "description": "Python graphing library that makes interactive, publication-quality graphs. Create line plots, scatter plots, area charts, bar charts, error bars, box plots, histograms, heatmaps, subplots, and more.",
    },
    {
        "id": "plotnine",
        "name": "plotnine",
        "language_id": "python",
        "framework": "none",
        "version": "0.13.0",
        "documentation_url": "https://plotnine.org",
        "description": "A grammar of graphics for Python. Data visualization package based on the grammar of graphics, a coherent system for describing and building graphs. From ad-hoc plots to publication-ready figures.",
    },
    {
        "id": "pygal",
        "name": "Pygal",
        "language_id": "python",
        "framework": "none",
        "version": "3.0.0",
        "documentation_url": "http://www.pygal.org",
        "description": "Beautiful python charting. Simple python charting library that creates SVG charts that are both beautiful and easy to customize.",
    },
    {
        "id": "seaborn",
        "name": "Seaborn",
        "language_id": "python",
        "framework": "none",
        "version": "0.13.0",
        "documentation_url": "https://seaborn.pydata.org",
        "description": "Python data visualization library based on matplotlib. Provides a high-level interface for drawing attractive and informative statistical graphics.",
    },
]

# Optional per-library file-extension overrides. A library inherits its
# language's default extension (LANGUAGE_FILE_EXTENSIONS) unless it declares a
# "file_extension" in LIBRARIES_METADATA above. Currently just `{"muix": ".tsx"}`
# — the React MUI X entry, whose snippets are authored as TSX while the other
# JavaScript libs stay `.js`. Discovery honours it so the language directory can
# hold both extensions.
LIBRARY_FILE_EXTENSION_OVERRIDES = {
    lib["id"]: lib["file_extension"] for lib in LIBRARIES_METADATA if lib.get("file_extension")
}

# Interactive libraries that generate HTML previews (not just PNG). The
# browser-rendered JS libraries (Chart.js, D3, ECharts, Highcharts, and the
# React MUI X entry) render in a browser; the harness emits both a static PNG
# (gallery grid + og:image) and a self-contained interactive HTML page (detail
# view). For MUI X the page is the esbuild-bundled React app inlined whole.
INTERACTIVE_LIBRARIES = frozenset(
    ["altair", "bokeh", "chartjs", "d3", "echarts", "highcharts", "letsplot", "muix", "plotly", "pygal"]
)

# =============================================================================
# GITHUB LABELS
# =============================================================================

# Library-specific labels (for issues and PRs)
LIBRARY_LABELS = frozenset([f"library:{lib}" for lib in SUPPORTED_LIBRARIES])

# Status labels (mutually exclusive)
STATUS_LABELS = frozenset(
    [
        "pending",
        "generating",
        "testing",
        "reviewing",
        "ai-approved",
        "ai-rejected",
        "ai-review-failed",
        "merged",
        "not-feasible",
        "completed",
    ]
)

# Quality score labels (mutually exclusive)
QUALITY_LABELS = frozenset(["quality:excellent", "quality:good", "quality:needs-work", "quality:poor"])

# Attempt labels
ATTEMPT_LABELS = frozenset(["ai-attempt-1", "ai-attempt-2", "ai-attempt-3", "ai-attempt-4"])

# =============================================================================
# QUALITY THRESHOLDS
# =============================================================================

QUALITY_THRESHOLD_EXCELLENT = 90
QUALITY_THRESHOLD_GOOD = 85
QUALITY_THRESHOLD_NEEDS_WORK = 75
QUALITY_THRESHOLD_APPROVAL = 90  # Minimum score for immediate approval (Review 1)
QUALITY_THRESHOLD_FINAL_APPROVAL = 50  # Minimum score for approval after 4 repair attempts (Review 5)

# =============================================================================
# HELPER FUNCTIONS
# =============================================================================


def is_valid_library(library: str) -> bool:
    """
    Check if a library name is one of the supported libraries.

    Args:
        library: Library name to validate

    Returns:
        True if valid, False otherwise

    Examples:
        >>> is_valid_library('matplotlib')
        True

        >>> is_valid_library('pandas')
        False
    """
    return library.lower() in SUPPORTED_LIBRARIES


def get_library_label(library: str) -> str:
    """
    Get library label for a library name.

    Args:
        library: Library name

    Returns:
        Library label (e.g., 'library:matplotlib')

    Examples:
        >>> get_library_label('matplotlib')
        'library:matplotlib'
    """
    return f"library:{library.lower()}"


def is_interactive_library(library: str) -> bool:
    """
    Check if a library generates interactive HTML previews.

    Args:
        library: Library name

    Returns:
        True if library generates HTML, False if only PNG

    Examples:
        >>> is_interactive_library('plotly')
        True

        >>> is_interactive_library('matplotlib')
        False
    """
    return library.lower() in INTERACTIVE_LIBRARIES


def library_file_extension(library: str) -> str:
    """
    File extension for a library's implementation file.

    Returns the library's per-library override if it declares one in
    LIBRARIES_METADATA, otherwise the default extension for the library's
    language. Falls back to ``.py`` for unknown libraries.

    Args:
        library: Library id (e.g. "chartjs", "matplotlib")

    Returns:
        Extension including the leading dot (e.g. ".js", ".py")

    Examples:
        >>> library_file_extension('chartjs')
        '.js'

        >>> library_file_extension('matplotlib')
        '.py'
    """
    lib = library.lower()
    if lib in LIBRARY_FILE_EXTENSION_OVERRIDES:
        return LIBRARY_FILE_EXTENSION_OVERRIDES[lib]
    for entry in LIBRARIES_METADATA:
        if entry["id"] == lib:
            return LANGUAGE_FILE_EXTENSIONS.get(entry["language_id"], ".py")
    return ".py"


def language_file_extensions(language_id: str) -> set[str]:
    """
    All file extensions that may appear under a language's implementation dir.

    This is the language default plus any per-library overrides for libraries in
    that language. ``sync_to_postgres`` scans for each, so a single language
    directory can hold more than one extension (e.g. JavaScript: ``.js`` for
    framework-agnostic libs, ``.tsx`` for a future React lib).

    Args:
        language_id: Language id (e.g. "javascript", "python")

    Returns:
        Set of extensions including the leading dot (e.g. {".js"})
    """
    exts: set[str] = set()
    default = LANGUAGE_FILE_EXTENSIONS.get(language_id)
    if default:
        exts.add(default)
    for entry in LIBRARIES_METADATA:
        if entry["language_id"] == language_id and entry.get("file_extension"):
            exts.add(entry["file_extension"])
    return exts
