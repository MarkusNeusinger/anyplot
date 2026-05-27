""" anyplot.ai
violin-split: Split Violin Plot
Library: plotnine 0.15.4 | Python 3.13.13
Quality: 88/100 | Updated: 2026-05-08
"""

import os

import numpy as np
import pandas as pd
from plotnine import (
    aes,
    element_line,
    element_rect,
    element_text,
    geom_boxplot,
    geom_violin,
    ggplot,
    labs,
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

# Okabe-Ito palette - first series is always #009E73 (brand)
IMPRINT = ["#009E73", "#C475FD"]

# Data - Employee satisfaction scores before and after training program
np.random.seed(42)

categories = ["Engineering", "Marketing", "Sales", "Support"]

data = []
for category in categories:
    # Generate different distributions for each category and time point
    if category == "Engineering":
        before = np.random.normal(65, 12, 80)
        after = np.random.normal(78, 10, 80)
    elif category == "Marketing":
        before = np.random.normal(58, 15, 100)
        after = np.random.normal(72, 12, 100)
    elif category == "Sales":
        before = np.random.normal(70, 10, 90)
        after = np.random.normal(82, 8, 90)
    else:  # Support
        before = np.random.normal(55, 18, 70)
        after = np.random.normal(75, 14, 70)

    for val in before:
        data.append({"category": category, "value": val, "split_group": "Before Training"})
    for val in after:
        data.append({"category": category, "value": val, "split_group": "After Training"})

df = pd.DataFrame(data)

# Clip values to realistic range (0-100 for satisfaction scores)
df["value"] = df["value"].clip(0, 100)

# Plot - True split violin with left-right style for side-by-side halves
plot = (
    ggplot(df, aes(x="category", y="value", fill="split_group"))
    + geom_violin(style="left-right", alpha=0.8, size=0.8, scale="width", trim=True)
    + geom_boxplot(width=0.15, alpha=0.9, outlier_alpha=0.5, outlier_size=2, size=0.6, position="identity")
    + scale_fill_manual(values=IMPRINT)
    + labs(x="Department", y="Satisfaction Score (0-100)", fill="Period", title="violin-split · plotnine · anyplot.ai")
    + theme_minimal()
    + theme(
        figure_size=(16, 9),
        plot_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
        panel_background=element_rect(fill=PAGE_BG),
        panel_grid_major_y=element_line(color=INK, alpha=0.10, size=0.3),
        panel_grid_major_x=element_line(color=INK, alpha=0.05, size=0.2),
        panel_border=element_rect(color=INK_SOFT, fill=None),
        axis_title_x=element_text(size=20, color=INK),
        axis_title_y=element_text(size=20, color=INK),
        axis_text_x=element_text(size=16, color=INK_SOFT),
        axis_text_y=element_text(size=16, color=INK_SOFT),
        axis_line=element_line(color=INK_SOFT),
        plot_title=element_text(size=24, color=INK, ha="center"),
        legend_background=element_rect(fill=ELEVATED_BG, color=INK_SOFT),
        legend_title=element_text(size=18, color=INK),
        legend_text=element_text(size=16, color=INK_SOFT),
        legend_position="right",
    )
)

# Save
plot.save(f"plot-{THEME}.png", dpi=300, verbose=False)
