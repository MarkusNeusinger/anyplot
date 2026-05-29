""" anyplot.ai
violin-basic: Basic Violin Plot
Library: plotnine 0.15.4 | Python 3.13.13
Quality: 88/100 | Updated: 2026-05-29
"""

import os

import numpy as np
import pandas as pd
from plotnine import (
    aes,
    element_blank,
    element_line,
    element_rect,
    element_text,
    geom_violin,
    ggplot,
    labs,
    scale_fill_manual,
    theme,
    theme_minimal,
)


# Theme tokens (Imprint palette — theme-adaptive chrome)
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Imprint categorical palette — positions 1–4 in canonical order
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233"]

# Data — annual salary distributions across 4 departments
np.random.seed(42)

records = []

# Engineering: right-skewed (many mid-range, few senior high earners)
salaries_eng = np.concatenate([np.random.normal(95000, 12000, 180), np.random.normal(148000, 7000, 40)])
records.extend([("Engineering", s) for s in salaries_eng])

# Design: bimodal (junior / senior pay split)
salaries_design = np.concatenate([np.random.normal(70000, 7000, 100), np.random.normal(108000, 7000, 100)])
records.extend([("Design", s) for s in salaries_design])

# Marketing: tight normal (narrow pay band)
salaries_mkt = np.random.normal(82000, 5000, 200)
records.extend([("Marketing", s) for s in salaries_mkt])

# Sales: wide spread (base + commission-driven variance)
salaries_sales = np.random.normal(90000, 22000, 200)
records.extend([("Sales", s) for s in salaries_sales])

df = pd.DataFrame(records, columns=["department", "salary"])
df["salary"] = df["salary"].clip(35000, 200000)
df["department"] = pd.Categorical(
    df["department"], categories=["Engineering", "Design", "Marketing", "Sales"], ordered=True
)

departments = ["Engineering", "Design", "Marketing", "Sales"]
palette = dict(zip(departments, IMPRINT_PALETTE, strict=True))

# Plot
title = "violin-basic · python · plotnine · anyplot.ai"

plot = (
    ggplot(df, aes(x="department", y="salary", fill="department"))
    + geom_violin(draw_quantiles=[0.25, 0.5, 0.75], alpha=0.82, color=INK_SOFT, size=0.6, trim=False)
    + scale_fill_manual(values=palette)
    + labs(x="Department", y="Annual Salary (USD)", title=title)
    + theme_minimal()
    + theme(
        figure_size=(8, 4.5),
        text=element_text(size=7, color=INK),
        axis_title=element_text(size=10, color=INK),
        axis_text=element_text(size=8, color=INK_SOFT),
        plot_title=element_text(size=12, color=INK),
        legend_position="none",
        panel_grid_major_x=element_blank(),
        panel_grid_minor=element_blank(),
        panel_grid_major_y=element_line(color=INK, size=0.3, alpha=0.15),
        plot_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
        panel_background=element_rect(fill=PAGE_BG),
    )
)

# Save
plot.save(f"plot-{THEME}.png", dpi=400, width=8, height=4.5, units="in", verbose=False)
