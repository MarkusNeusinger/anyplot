""" anyplot.ai
scatter-text: Scatter Plot with Text Labels Instead of Points
Library: letsplot 4.9.0 | Python 3.13.13
Quality: 93/100 | Updated: 2026-05-17
"""

import os

import numpy as np
import pandas as pd
from lets_plot import (
    LetsPlot,
    aes,
    element_blank,
    element_line,
    element_rect,
    element_text,
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

# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Okabe-Ito palette (first series always #009E73)
IMPRINT = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477"]

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

# Position languages with good spacing to minimize overlap
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

# Map categories to Okabe-Ito colors
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

color_palette = {
    "General": IMPRINT[0],  # #009E73 (brand green)
    "Web": IMPRINT[1],  # #C475FD (vermillion)
    "Systems": IMPRINT[2],  # #4467A3 (blue)
    "Mobile": IMPRINT[3],  # #BD8233 (reddish purple)
    "Functional": IMPRINT[4],  # #AE3030 (orange)
    "Scripting": IMPRINT[5],  # #2ABCCD (sky blue)
    "Data Science": IMPRINT[6],  # #954477 (yellow)
    "Scientific": INK_SOFT,  # Neutral for scientific
    "Legacy": INK_SOFT,  # Neutral for legacy
}

# Create plot with interactive tooltips (lets-plot distinctive feature)
plot = (
    ggplot(df, aes(x="x", y="y", color="category"))
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
        title="scatter-text · Python · letsplot · anyplot.ai",
    )
    + theme_minimal()
    + theme(
        plot_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
        panel_background=element_rect(fill=PAGE_BG),
        panel_grid_major=element_line(color=INK, size=0.1),
        panel_grid_minor=element_blank(),
        axis_title=element_text(size=20, color=INK),
        axis_text=element_text(size=16, color=INK_SOFT),
        axis_line=element_line(color=INK_SOFT, size=0.5),
        plot_title=element_text(size=24, color=INK, face="bold"),
        legend_background=element_rect(fill=ELEVATED_BG, color=INK_SOFT),
        legend_text=element_text(size=16, color=INK_SOFT),
        legend_title=element_text(size=18, color=INK),
    )
    + ggsize(1600, 900)
)

# Save as PNG (scale 3x for 4800 × 2700 px)
ggsave(plot, f"plot-{THEME}.png", path=".", scale=3)

# Save interactive HTML version with tooltips
ggsave(plot, f"plot-{THEME}.html", path=".")
