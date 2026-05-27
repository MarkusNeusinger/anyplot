""" anyplot.ai
bar-stacked: Stacked Bar Chart
Library: plotnine 0.15.4 | Python 3.13.13
Quality: 90/100 | Updated: 2026-05-09
"""

import os
import pathlib
import sys

import pandas as pd


# Remove local module from path to avoid shadowing the plotnine library
sys.path = [p for p in sys.path if "bar-stacked/implementations/python" not in p]

from plotnine import (  # noqa: E402
    aes,
    element_line,
    element_rect,
    element_text,
    geom_bar,
    geom_text,
    ggplot,
    labs,
    position_stack,
    scale_fill_manual,
    theme,
    theme_minimal,
)


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Okabe-Ito palette (first series always #009E73)
IMPRINT = ["#009E73", "#C475FD", "#4467A3", "#BD8233"]

# Data - Quarterly sales by product category
data = {
    "Quarter": ["Q1", "Q2", "Q3", "Q4"] * 4,
    "Category": ["Electronics"] * 4 + ["Clothing"] * 4 + ["Home"] * 4 + ["Sports"] * 4,
    "Sales": [45, 52, 48, 68, 32, 38, 55, 42, 28, 31, 35, 38, 18, 22, 28, 25],
}

df = pd.DataFrame(data)

# Order categories for consistent stacking (largest at bottom)
category_order = ["Sports", "Home", "Clothing", "Electronics"]
df["Category"] = pd.Categorical(df["Category"], categories=category_order, ordered=True)

# Plot
plot = (
    ggplot(df, aes(x="Quarter", y="Sales", fill="Category"))
    + geom_bar(stat="identity", position="stack", width=0.7)
    + geom_text(aes(label="Sales"), position=position_stack(vjust=0.5), size=12, color="white", fontweight="bold")
    + scale_fill_manual(values=IMPRINT)
    + labs(title="bar-stacked · plotnine · anyplot.ai", x="Quarter", y="Sales (thousands USD)", fill="Category")
    + theme_minimal()
    + theme(
        figure_size=(16, 9),
        plot_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
        panel_background=element_rect(fill=PAGE_BG),
        panel_grid_major=element_line(color=INK, size=0.3, alpha=0.10),
        panel_grid_minor=element_line(color=INK, size=0.2, alpha=0.05),
        panel_border=element_rect(color=INK_SOFT, fill=None),
        plot_title=element_text(size=24, weight="bold", color=INK),
        axis_title=element_text(size=20, color=INK),
        axis_text=element_text(size=16, color=INK_SOFT),
        legend_background=element_rect(fill=ELEVATED_BG, color=INK_SOFT),
        legend_title=element_text(size=18, color=INK),
        legend_text=element_text(size=16, color=INK_SOFT),
        legend_position="right",
    )
)

# Save
output_dir = pathlib.Path(__file__).parent
plot.save(output_dir / f"plot-{THEME}.png", dpi=300, verbose=False)
