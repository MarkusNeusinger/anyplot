""" anyplot.ai
waffle-basic: Basic Waffle Chart
Library: letsplot 4.9.0 | Python 3.13.13
Quality: 93/100 | Updated: 2026-05-05
"""

import os

import pandas as pd
from lets_plot import (
    LetsPlot,
    aes,
    coord_fixed,
    element_blank,
    element_rect,
    element_text,
    geom_tile,
    ggplot,
    ggsize,
    labs,
    scale_fill_manual,
    theme,
    theme_void,
)
from lets_plot.export import ggsave


LetsPlot.setup_html()

# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Okabe-Ito palette (first series ALWAYS #009E73)
OKABE_ITO = ["#009E73", "#D55E00", "#0072B2", "#CC79A7"]

# Data - Survey results on voting preferences (values sum to 100%)
categories = ["Very Likely", "Likely", "Neutral", "Unlikely"]
values = [45, 28, 18, 9]  # Percentages

# Build 10x10 waffle grid (100 squares, each = 1%)
grid_data = []
square_idx = 0

for cat, val in zip(categories, values, strict=True):
    for _ in range(val):
        row = 9 - (square_idx // 10)
        col = square_idx % 10
        grid_data.append({"x": col, "y": row, "category": cat})
        square_idx += 1

df = pd.DataFrame(grid_data)
df["category"] = pd.Categorical(df["category"], categories=categories, ordered=True)

# Create legend labels with percentages
legend_labels = {cat: f"{cat} ({val}%)" for cat, val in zip(categories, values, strict=True)}
df["legend_label"] = df["category"].map(legend_labels)
df["legend_label"] = pd.Categorical(
    df["legend_label"], categories=[legend_labels[cat] for cat in categories], ordered=True
)

# Theme-adaptive custom theme
anyplot_theme = theme(
    plot_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
    panel_background=element_rect(fill=PAGE_BG),
    plot_title=element_text(size=24, color=INK, hjust=0.5),
    legend_background=element_rect(fill=ELEVATED_BG, color=INK_SOFT),
    legend_title=element_text(size=18, color=INK),
    legend_text=element_text(size=16, color=INK_SOFT),
    axis_title=element_blank(),
    axis_text=element_blank(),
    axis_line=element_blank(),
)

# Plot
plot = (
    ggplot(df, aes(x="x", y="y", fill="legend_label"))
    + geom_tile(width=0.88, height=0.88, size=0)
    + coord_fixed(ratio=1)
    + scale_fill_manual(values=OKABE_ITO)
    + labs(title="waffle-basic · letsplot · anyplot.ai", fill="Preference")
    + theme_void()
    + anyplot_theme
    + ggsize(1600, 900)
)

# Save outputs
ggsave(plot, f"plot-{THEME}.png", path=".", scale=3)
ggsave(plot, f"plot-{THEME}.html", path=".")
