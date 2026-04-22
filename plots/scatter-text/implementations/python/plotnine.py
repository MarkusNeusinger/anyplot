""" pyplots.ai
scatter-text: Scatter Plot with Text Labels Instead of Points
Library: plotnine 0.15.2 | Python 3.13.11
Quality: 92/100 | Created: 2026-01-09
"""

import numpy as np
import pandas as pd
from plotnine import aes, element_line, element_text, geom_text, ggplot, labs, scale_color_manual, theme, theme_minimal


# Data: Simulated 2D projection of programming language embeddings
np.random.seed(42)

# Programming languages grouped by paradigm
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

# Add some jitter for realism
df = pd.DataFrame(languages, columns=["label", "x", "y", "category"])
df["x"] = df["x"] + np.random.normal(0, 0.1, len(df))
df["y"] = df["y"] + np.random.normal(0, 0.1, len(df))

# Define color palette (Python Blue as primary, colorblind-safe palette)
colors = {
    "General": "#306998",  # Python Blue
    "Systems": "#E69F00",  # Orange
    "Functional": "#56B4E9",  # Sky Blue
    "Web": "#FFD43B",  # Python Yellow
    "Data": "#009E73",  # Teal
}

# Create plot
plot = (
    ggplot(df, aes(x="x", y="y", label="label", color="category"))
    + geom_text(size=12, alpha=0.85, fontweight="bold")
    + labs(
        x="Dimension 1 (Paradigm Similarity)",
        y="Dimension 2 (Abstraction Level)",
        title="scatter-text · plotnine · pyplots.ai",
        color="Category",
    )
    + scale_color_manual(values=colors)
    + theme_minimal()
    + theme(
        figure_size=(16, 9),
        text=element_text(size=14),
        axis_title=element_text(size=20),
        axis_text=element_text(size=16),
        plot_title=element_text(size=24, ha="center"),
        legend_title=element_text(size=18),
        legend_text=element_text(size=16),
        legend_position="right",
        panel_grid_major=element_line(color="#CCCCCC", size=0.5, alpha=0.3),
        panel_grid_minor=element_line(color="#EEEEEE", size=0.3, alpha=0.2),
    )
)

# Save
plot.save("plot.png", dpi=300, verbose=False)
