""" pyplots.ai
scatter-text: Scatter Plot with Text Labels Instead of Points
Library: letsplot 4.8.2 | Python 3.13.11
Quality: 90/100 | Created: 2026-01-09
"""

import numpy as np
import pandas as pd
from lets_plot import (
    LetsPlot,
    aes,
    element_text,
    geom_point,
    geom_text,
    ggplot,
    ggsave,
    ggsize,
    labs,
    layer_tooltips,
    scale_color_manual,
    theme,
    theme_minimal,
)


LetsPlot.setup_html()

# Data - Programming languages positioned by paradigm (functional vs object-oriented)
# and level of abstraction (low vs high)
np.random.seed(42)

languages = [
    "Python",
    "JavaScript",
    "Java",
    "C++",
    "Ruby",
    "Go",
    "Rust",
    "Swift",
    "Kotlin",
    "TypeScript",
    "Scala",
    "Haskell",
    "Clojure",
    "Elixir",
    "F#",
    "C#",
    "PHP",
    "Perl",
    "R",
    "Julia",
    "MATLAB",
    "Lua",
    "Dart",
    "Groovy",
    "OCaml",
    "Erlang",
    "Fortran",
    "COBOL",
    "Assembly",
    "Lisp",
]

# Position languages with better spacing to reduce overlap
# Adjusted coordinates for dense regions
paradigm_scores = {
    "Python": (0.58, 0.88),
    "JavaScript": (0.42, 0.72),
    "Java": (0.28, 0.68),
    "C++": (0.18, 0.38),
    "Ruby": (0.72, 0.92),
    "Go": (0.22, 0.58),
    "Rust": (0.12, 0.48),
    "Swift": (0.38, 0.80),
    "Kotlin": (0.48, 0.85),
    "TypeScript": (0.55, 0.68),
    "Scala": (0.72, 0.62),
    "Haskell": (0.95, 0.90),
    "Clojure": (0.88, 0.82),
    "Elixir": (0.82, 0.88),
    "F#": (0.78, 0.72),
    "C#": (0.32, 0.78),
    "PHP": (0.35, 0.60),
    "Perl": (0.48, 0.52),
    "R": (0.68, 0.78),
    "Julia": (0.62, 0.58),
    "MATLAB": (0.52, 0.48),
    "Lua": (0.42, 0.45),
    "Dart": (0.32, 0.52),
    "Groovy": (0.45, 0.62),
    "OCaml": (0.90, 0.68),
    "Erlang": (0.85, 0.58),
    "Fortran": (0.08, 0.32),
    "COBOL": (0.05, 0.22),
    "Assembly": (0.02, 0.12),
    "Lisp": (0.92, 0.52),
}

x_coords = [paradigm_scores[lang][0] for lang in languages]
y_coords = [paradigm_scores[lang][1] for lang in languages]

# Categorize by primary use
categories = [
    "General",
    "Web",
    "General",
    "Systems",
    "Web",
    "Systems",
    "Systems",
    "Mobile",
    "Mobile",
    "Web",
    "General",
    "Functional",
    "Functional",
    "Functional",
    "Functional",
    "General",
    "Web",
    "Scripting",
    "Data Science",
    "Data Science",
    "Data Science",
    "Scripting",
    "Mobile",
    "General",
    "Functional",
    "Functional",
    "Scientific",
    "Legacy",
    "Systems",
    "Functional",
]

df = pd.DataFrame({"x": x_coords, "y": y_coords, "label": languages, "category": categories})

# Define colors for categories
color_palette = {
    "General": "#306998",
    "Web": "#E6A700",
    "Systems": "#2E86AB",
    "Mobile": "#A23B72",
    "Functional": "#F18F01",
    "Scripting": "#C73E1D",
    "Data Science": "#3A86A9",
    "Scientific": "#6B8E23",
    "Legacy": "#708090",
}

category_order = [
    "General",
    "Web",
    "Systems",
    "Mobile",
    "Functional",
    "Scripting",
    "Data Science",
    "Scientific",
    "Legacy",
]

# Create plot with interactive tooltips (lets-plot distinctive feature)
plot = (
    ggplot(df, aes(x="x", y="y", color="category"))
    # Invisible points for legend (show colored squares instead of 'a')
    + geom_point(aes(size="category"), alpha=0, show_legend=True)
    # Text labels with interactive tooltips
    + geom_text(
        aes(label="label"),
        size=11,
        alpha=0.9,
        fontface="bold",
        tooltips=layer_tooltips()
        .title("@label")
        .line("Category|@category")
        .line("Paradigm|@x")
        .line("Abstraction|@y")
        .format("x", ".2f")
        .format("y", ".2f"),
    )
    + scale_color_manual(values=color_palette, limits=category_order, name="Primary Use")
    + labs(
        x="Object-Oriented ← Paradigm → Functional",
        y="Abstraction Level (Low → High)",
        title="scatter-text · letsplot · pyplots.ai",
    )
    + theme_minimal()
    + theme(
        plot_title=element_text(size=28, face="bold"),
        axis_title=element_text(size=22),
        axis_text=element_text(size=16),
        legend_title=element_text(size=18),
        legend_text=element_text(size=14),
    )
    + ggsize(1600, 900)
)

# Save as PNG (scale 3x for 4800 × 2700 px)
ggsave(plot, "plot.png", path=".", scale=3)

# Save interactive HTML version with tooltips
ggsave(plot, "plot.html", path=".")
