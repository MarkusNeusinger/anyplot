""" anyplot.ai
box-grouped: Grouped Box Plot
Library: letsplot 4.9.0 | Python 3.13.13
Quality: 91/100 | Updated: 2026-05-08
"""

import os
import shutil

import numpy as np
import pandas as pd
from lets_plot import (
    LetsPlot,
    aes,
    element_line,
    element_rect,
    element_text,
    geom_boxplot,
    ggplot,
    ggsave,
    ggsize,
    labs,
    scale_fill_manual,
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

IMPRINT = ["#009E73", "#C475FD", "#4467A3"]

# Data: Employee performance scores by department and experience level
np.random.seed(42)

departments = ["Engineering", "Marketing", "Sales", "Operations"]
experience_levels = ["Junior", "Mid-Level", "Senior"]

data = []
for dept in departments:
    for exp in experience_levels:
        n = 40
        if exp == "Junior":
            base = 50 + np.random.choice([0, 5, 10])
            spread = 12
        elif exp == "Mid-Level":
            base = 60 + np.random.choice([0, 3, 6])
            spread = 10
        else:
            base = 72 + np.random.choice([0, 2, 4])
            spread = 8

        dept_offset = {"Engineering": 3, "Marketing": 0, "Sales": -2, "Operations": 1}[dept]
        values = np.random.normal(base + dept_offset, spread, n)

        if np.random.random() > 0.5:
            outlier_low = base - 3 * spread + np.random.randn(2) * 2
            outlier_high = base + 3 * spread + np.random.randn(2) * 2
            values = np.concatenate([values, outlier_low, outlier_high])

        for v in values:
            data.append({"Department": dept, "Experience": exp, "Performance Score": v})

df = pd.DataFrame(data)
df["Experience"] = pd.Categorical(df["Experience"], categories=experience_levels, ordered=True)
df["Department"] = pd.Categorical(df["Department"], categories=departments, ordered=True)

# Plot
plot = (
    ggplot(df, aes(x="Department", y="Performance Score", fill="Experience"))
    + geom_boxplot(alpha=0.85, outlier_size=3, outlier_alpha=0.7, width=0.7)
    + scale_fill_manual(values=IMPRINT)
    + labs(title="box-grouped · letsplot · anyplot.ai", x="Department", y="Performance Score", fill="Experience Level")
    + theme_minimal()
    + theme(
        plot_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
        panel_background=element_rect(fill=PAGE_BG),
        panel_grid_major=element_line(color=INK_SOFT, size=0.3),
        plot_title=element_text(size=24, face="bold", color=INK),
        axis_title=element_text(size=20, color=INK),
        axis_text=element_text(size=16, color=INK_SOFT),
        legend_background=element_rect(fill=ELEVATED_BG, color=INK_SOFT),
        legend_title=element_text(size=16, color=INK),
        legend_text=element_text(size=16, color=INK_SOFT),
        legend_position="right",
    )
    + ggsize(1600, 900)
)

# Save
ggsave(plot, f"plot-{THEME}.png", scale=3)
ggsave(plot, f"plot-{THEME}.html")

# Move files from lets-plot-images to current directory
shutil.move(f"lets-plot-images/plot-{THEME}.png", f"plot-{THEME}.png")
shutil.move(f"lets-plot-images/plot-{THEME}.html", f"plot-{THEME}.html")
