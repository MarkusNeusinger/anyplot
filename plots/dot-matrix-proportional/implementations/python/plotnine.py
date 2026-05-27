""" anyplot.ai
dot-matrix-proportional: Dot Matrix Chart for Proportional Counts
Library: plotnine 0.15.4 | Python 3.13.13
Quality: 88/100 | Created: 2026-05-08
"""

import os
import sys


# Prevent this file from shadowing the installed plotnine package
sys.path = [p for p in sys.path if p != os.path.dirname(os.path.abspath(__file__)) and p != ""]

import pandas as pd  # noqa: E402
from plotnine import (  # noqa: E402
    aes,
    coord_fixed,
    element_rect,
    element_text,
    geom_point,
    ggplot,
    ggsave,
    labs,
    scale_color_manual,
    theme,
    theme_void,
)


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

IMPRINT = ["#009E73", "#C475FD", "#4467A3"]

# Data – Household Solar Panel Adoption Survey (100 homes, 10×10 grid)
categories = ["Fully Solar-Powered", "Partially Solar-Powered", "No Solar Panels"]
counts = [24, 41, 35]
total = sum(counts)  # 100

cols = 10
labels = []
for cat, cnt in zip(categories, counts, strict=True):
    labels.extend([cat] * cnt)

df = pd.DataFrame(
    {
        "x": [i % cols for i in range(total)],
        "y": [-(i // cols) for i in range(total)],
        "category": pd.Categorical(labels, categories=categories),
    }
)

# Legend labels include counts
legend_labels = [f"{cat}  ({cnt})" for cat, cnt in zip(categories, counts, strict=True)]

# Plot
plot = (
    ggplot(df, aes(x="x", y="y", color="category"))
    + geom_point(size=9)
    + scale_color_manual(values=IMPRINT, labels=legend_labels)
    + coord_fixed()
    + labs(
        title="dot-matrix-proportional · plotnine · anyplot.ai",
        subtitle="Household Solar Panel Adoption Survey  ·  n = 100 homes",
        color="",
    )
    + theme_void()
    + theme(
        plot_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
        panel_background=element_rect(fill=PAGE_BG),
        plot_title=element_text(color=INK, size=24, ha="left", weight="bold"),
        plot_subtitle=element_text(color=INK_SOFT, size=18, ha="left"),
        legend_background=element_rect(fill=ELEVATED_BG, color=INK_SOFT),
        legend_text=element_text(color=INK_SOFT, size=16),
        legend_title=element_text(color=INK, size=16),
        legend_key=element_rect(fill=ELEVATED_BG, color="None"),
        legend_position="right",
        plot_margin=0.05,
    )
)

# Save
ggsave(plot, filename=f"plot-{THEME}.png", dpi=300, width=12, height=10)
