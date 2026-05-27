""" anyplot.ai
box-grouped: Grouped Box Plot
Library: plotnine 0.15.4 | Python 3.13.13
Quality: 91/100 | Updated: 2026-05-08
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
    ggplot,
    ggsave,
    labs,
    position_dodge2,
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
IMPRINT = ["#009E73", "#C475FD", "#4467A3"]

# Data: Employee performance scores by department and experience level
np.random.seed(42)

departments = ["Engineering", "Marketing", "Sales", "Support"]
experience_levels = ["Junior", "Mid-Level", "Senior"]

data = []
for dept in departments:
    for exp in experience_levels:
        # Create realistic performance distributions that vary by dept and experience
        n = 40
        if dept == "Engineering":
            base = 70 if exp == "Junior" else 78 if exp == "Mid-Level" else 85
            spread = 12 if exp == "Junior" else 10 if exp == "Mid-Level" else 8
        elif dept == "Marketing":
            base = 68 if exp == "Junior" else 75 if exp == "Mid-Level" else 82
            spread = 14 if exp == "Junior" else 11 if exp == "Mid-Level" else 9
        elif dept == "Sales":
            base = 65 if exp == "Junior" else 77 if exp == "Mid-Level" else 88
            spread = 15 if exp == "Junior" else 12 if exp == "Mid-Level" else 7
        else:  # Support
            base = 72 if exp == "Junior" else 76 if exp == "Mid-Level" else 80
            spread = 10 if exp == "Junior" else 9 if exp == "Mid-Level" else 8

        values = np.random.normal(base, spread, n)
        # Add some outliers
        if exp == "Senior" and dept == "Sales":
            values = np.append(values, [55, 98])
        if exp == "Junior" and dept == "Engineering":
            values = np.append(values, [42, 95])

        for v in values:
            data.append({"Department": dept, "Experience": exp, "Score": v})

df = pd.DataFrame(data)

# Order experience levels properly
df["Experience"] = pd.Categorical(df["Experience"], categories=experience_levels, ordered=True)

# Create theme
anyplot_theme = theme(
    plot_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
    panel_background=element_rect(fill=PAGE_BG),
    panel_grid_major=element_line(color=INK, size=0.3, alpha=0.10),
    panel_grid_minor=element_line(color=INK, size=0.2, alpha=0.05),
    panel_border=element_rect(color=INK_SOFT, fill=None),
    axis_title=element_text(color=INK, size=20),
    axis_text=element_text(color=INK_SOFT, size=16),
    axis_line=element_line(color=INK_SOFT),
    plot_title=element_text(color=INK, size=24),
    legend_background=element_rect(fill=ELEVATED_BG, color=INK_SOFT),
    legend_text=element_text(color=INK_SOFT, size=16),
    legend_title=element_text(color=INK, size=18),
    figure_size=(16, 9),
)

# Create grouped box plot
plot = (
    ggplot(df, aes(x="Department", y="Score", fill="Experience"))
    + geom_boxplot(
        position=position_dodge2(preserve="single", padding=0.1), width=0.7, outlier_size=3, outlier_alpha=0.7
    )
    + scale_fill_manual(values=IMPRINT)
    + labs(
        x="Department",
        y="Performance Score (0-100)",
        title="box-grouped · plotnine · anyplot.ai",
        fill="Experience Level",
    )
    + theme_minimal()
    + anyplot_theme
)

# Save
ggsave(plot, filename=f"plot-{THEME}.png", dpi=300, width=16, height=9)
