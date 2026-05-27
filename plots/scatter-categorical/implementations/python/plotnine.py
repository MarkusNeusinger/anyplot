""" anyplot.ai
scatter-categorical: Categorical Scatter Plot
Library: plotnine 0.15.4 | Python 3.13.13
Quality: 87/100 | Updated: 2026-05-12
"""

import os
import pathlib
import sys


# Remove current directory from path to avoid circular import
current_dir = str(pathlib.Path(__file__).parent)
sys.path = [p for p in sys.path if p != current_dir and p != ""]

import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402
from plotnine import (  # noqa: E402
    aes,
    element_line,
    element_rect,
    element_text,
    geom_point,
    ggplot,
    labs,
    scale_color_manual,
    theme,
    theme_minimal,
)


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Okabe-Ito palette (canonical order)
IMPRINT = ["#009E73", "#C475FD", "#4467A3"]

# Data
np.random.seed(42)

# Create sample data with 3 categories showing different patterns
n_per_group = 40

# Group A: positive correlation
x_a = np.random.normal(25, 8, n_per_group)
y_a = x_a * 0.8 + np.random.normal(10, 4, n_per_group)

# Group B: higher values, positive correlation
x_b = np.random.normal(45, 10, n_per_group)
y_b = x_b * 0.6 + np.random.normal(15, 5, n_per_group)

# Group C: lower values, weaker correlation
x_c = np.random.normal(35, 12, n_per_group)
y_c = np.random.normal(35, 8, n_per_group)

df = pd.DataFrame(
    {
        "Temperature (°C)": np.concatenate([x_a, x_b, x_c]),
        "Growth Rate (cm/week)": np.concatenate([y_a, y_b, y_c]),
        "Plant Species": (["Species A"] * n_per_group + ["Species B"] * n_per_group + ["Species C"] * n_per_group),
    }
)

# Plot
plot = (
    ggplot(df, aes(x="Temperature (°C)", y="Growth Rate (cm/week)", color="Plant Species"))
    + geom_point(size=4, alpha=0.7)
    + scale_color_manual(values=IMPRINT)
    + labs(
        x="Temperature (°C)",
        y="Growth Rate (cm/week)",
        title="scatter-categorical · plotnine · anyplot.ai",
        color="Plant Species",
    )
    + theme_minimal()
    + theme(
        figure_size=(16, 9),
        plot_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
        panel_background=element_rect(fill=PAGE_BG),
        panel_grid_major=element_line(color=INK, size=0.3, alpha=0.10),
        panel_grid_minor=element_line(color=INK, size=0.2, alpha=0.05),
        axis_title=element_text(size=20, color=INK),
        axis_text=element_text(size=16, color=INK_SOFT),
        axis_line=element_line(color=INK_SOFT),
        plot_title=element_text(size=24, color=INK),
        legend_background=element_rect(fill=ELEVATED_BG, color=INK_SOFT),
        legend_text=element_text(size=16, color=INK_SOFT),
        legend_title=element_text(size=18, color=INK),
    )
)

# Save
output_dir = pathlib.Path(__file__).parent
plot.save(str(output_dir / f"plot-{THEME}.png"), dpi=300, verbose=False)
