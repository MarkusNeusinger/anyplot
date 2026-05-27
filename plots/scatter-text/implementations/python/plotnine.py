""" anyplot.ai
scatter-text: Scatter Plot with Text Labels Instead of Points
Library: plotnine 0.15.4 | Python 3.13.13
Quality: 90/100 | Updated: 2026-05-17
"""

import os

import numpy as np
import pandas as pd
from plotnine import aes, element_line, element_rect, element_text, geom_text, ggplot, labs, scale_color_manual, theme


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Okabe-Ito palette (categorical data only)
IMPRINT = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477"]

# Data: Simulated 2D projection of programming language embeddings
np.random.seed(42)

languages = [
    # Object-oriented / General purpose
    ("Python", -1.2, 2.1, "General"),
    ("Java", -0.8, 1.5, "General"),
    ("C#", -0.5, 1.3, "General"),
    ("Ruby", -1.5, 1.8, "General"),
    ("Kotlin", -0.3, 1.6, "General"),
    # Systems / Low-level
    ("C", 2.0, -0.5, "Systems"),
    ("C++", 1.8, 0.2, "Systems"),
    ("Rust", 1.5, 0.8, "Systems"),
    ("Go", 1.2, 1.0, "Systems"),
    ("Zig", 2.2, -0.2, "Systems"),
    # Functional
    ("Haskell", -2.0, -1.5, "Functional"),
    ("Scala", -1.0, -0.5, "Functional"),
    ("Clojure", -1.8, -1.0, "Functional"),
    ("F#", -0.7, -0.8, "Functional"),
    ("Erlang", -2.2, -1.2, "Functional"),
    # Web / Scripting
    ("JavaScript", 0.5, 2.5, "Web"),
    ("TypeScript", 0.3, 2.2, "Web"),
    ("PHP", 0.8, 1.8, "Web"),
    ("Perl", 1.0, 1.2, "Web"),
    ("Lua", 1.5, 1.5, "Web"),
    # Data / Scientific
    ("R", -1.8, 0.5, "Data"),
    ("Julia", -0.2, 0.3, "Data"),
    ("MATLAB", -1.5, 0.2, "Data"),
    ("SQL", 0.2, -1.5, "Data"),
    ("SAS", -1.2, -0.3, "Data"),
]

df = pd.DataFrame(languages, columns=["label", "x", "y", "category"])
df["x"] = df["x"] + np.random.normal(0, 0.1, len(df))
df["y"] = df["y"] + np.random.normal(0, 0.1, len(df))

# Map categories to Okabe-Ito colors
category_colors = {
    "General": IMPRINT[0],
    "Systems": IMPRINT[1],
    "Functional": IMPRINT[2],
    "Web": IMPRINT[3],
    "Data": IMPRINT[4],
}

# Plot
plot = (
    ggplot(df, aes(x="x", y="y", label="label", color="category"))
    + geom_text(size=11, alpha=0.9, fontweight="bold")
    + labs(
        x="Dimension 1 (Paradigm Similarity)",
        y="Dimension 2 (Abstraction Level)",
        title="scatter-text · Python · plotnine · anyplot.ai",
        color="Category",
    )
    + scale_color_manual(values=category_colors)
    + theme(
        figure_size=(16, 9),
        dpi=300,
        plot_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
        panel_background=element_rect(fill=PAGE_BG),
        panel_grid_major=element_line(color=INK, size=0.3, alpha=0.15),
        panel_grid_minor=element_line(color=INK, size=0.2, alpha=0.08),
        panel_border=element_rect(color=INK_SOFT, fill=None, size=0.4),
        axis_title=element_text(size=20, color=INK),
        axis_text=element_text(size=16, color=INK_SOFT),
        axis_line=element_line(color=INK_SOFT, size=0.4),
        plot_title=element_text(size=24, color=INK, ha="left"),
        legend_background=element_rect(fill=ELEVATED_BG, color=INK_SOFT),
        legend_text=element_text(size=16, color=INK_SOFT),
        legend_title=element_text(size=18, color=INK),
        legend_position="right",
    )
)

# Save
plot.save(f"plot-{THEME}.png", dpi=300, verbose=False)
