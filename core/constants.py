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
    ["altair", "bokeh", "highcharts", "letsplot", "matplotlib", "plotly", "plotnine", "pygal", "seaborn"]
)

# Supported programming languages
SUPPORTED_LANGUAGES = frozenset(["python"])

# Language metadata for database seeding (analog to LIBRARIES_METADATA)
LANGUAGES_METADATA = [
    {
        "id": "python",
        "name": "Python",
        "file_extension": ".py",
        "runtime_version": "3.13",
        "documentation_url": "https://www.python.org",
        "description": "The default language for anyplot plot implementations.",
    }
]

# Map from language id → file extension used by sync_to_postgres for discovery
LANGUAGE_FILE_EXTENSIONS = {lang["id"]: lang["file_extension"] for lang in LANGUAGES_METADATA}

# Library metadata for database seeding and display
LIBRARIES_METADATA = [
    {
        "id": "altair",
        "name": "Altair",
        "language_id": "python",
        "version": "5.2.0",
        "documentation_url": "https://altair-viz.github.io",
        "description": "Declarative visualization library for Python. Its simple, friendly and consistent API, built on top of the powerful Vega-Lite grammar, empowers you to spend less time writing code and more time exploring your data.",
    },
    {
        "id": "bokeh",
        "name": "Bokeh",
        "language_id": "python",
        "version": "3.4.0",
        "documentation_url": "https://bokeh.org",
        "description": "Interactive visualization library that makes it simple to create common plots, while also handling custom or specialized use-cases. Work in Python close to all the PyData tools you're already familiar with.",
    },
    {
        "id": "highcharts",
        "name": "Highcharts",
        "language_id": "python",
        "version": "1.10.0",
        "documentation_url": "https://www.highcharts.com",
        "description": "Powerful data visualization for real-world apps. Fast to implement, endlessly flexible. Makes it easy for developers to create charts and dashboards for web and mobile platforms.",
    },
    {
        "id": "letsplot",
        "name": "lets-plot",
        "language_id": "python",
        "version": "4.5.0",
        "documentation_url": "https://lets-plot.org",
        "description": "Multiplatform plotting library built on the principles of the Grammar of Graphics. A faithful adaptation of R's ggplot2 that extends Grammar of Graphics principles to both Python and Kotlin.",
    },
    {
        "id": "matplotlib",
        "name": "Matplotlib",
        "language_id": "python",
        "version": "3.9.0",
        "documentation_url": "https://matplotlib.org",
        "description": "Comprehensive library for creating static, animated, and interactive visualizations in Python. Matplotlib makes easy things easy and hard things possible.",
    },
    {
        "id": "plotly",
        "name": "Plotly",
        "language_id": "python",
        "version": "5.18.0",
        "documentation_url": "https://plotly.com/python",
        "description": "Python graphing library that makes interactive, publication-quality graphs. Create line plots, scatter plots, area charts, bar charts, error bars, box plots, histograms, heatmaps, subplots, and more.",
    },
    {
        "id": "plotnine",
        "name": "plotnine",
        "language_id": "python",
        "version": "0.13.0",
        "documentation_url": "https://plotnine.org",
        "description": "A grammar of graphics for Python. Data visualization package based on the grammar of graphics, a coherent system for describing and building graphs. From ad-hoc plots to publication-ready figures.",
    },
    {
        "id": "pygal",
        "name": "Pygal",
        "language_id": "python",
        "version": "3.0.0",
        "documentation_url": "http://www.pygal.org",
        "description": "Beautiful python charting. Simple python charting library that creates SVG charts that are both beautiful and easy to customize.",
    },
    {
        "id": "seaborn",
        "name": "Seaborn",
        "language_id": "python",
        "version": "0.13.0",
        "documentation_url": "https://seaborn.pydata.org",
        "description": "Python data visualization library based on matplotlib. Provides a high-level interface for drawing attractive and informative statistical graphics.",
    },
]

# Interactive libraries that generate HTML previews (not just PNG)
INTERACTIVE_LIBRARIES = frozenset(["altair", "bokeh", "highcharts", "letsplot", "plotly", "pygal"])

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
