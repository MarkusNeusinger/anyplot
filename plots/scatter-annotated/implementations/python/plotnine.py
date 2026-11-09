""" anyplot.ai
scatter-annotated: Annotated Scatter Plot with Text Labels
Library: plotnine 0.15.9 | Python 3.14.10
Quality: 84/100 | Updated: 2026-11-09
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
    geom_point,
    geom_text,
    ggplot,
    labs,
    scale_x_continuous,
    scale_y_continuous,
    theme,
    theme_minimal,
)


# Theme tokens (see prompts/default-style-guide.md "Theme-adaptive Chrome")
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
BRAND = "#009E73"  # Imprint palette position 1 — a single-series plot uses it alone

# Columns: set these to your table's column names
REVENUE = "Annual Revenue ($ Millions)"  # role: x
PROFIT_MARGIN = "Profit Margin (%)"  # role: y
COMPANY = "Company"  # role: label

# Data: replace this block with your own table, for example df = pd.read_csv("companies.csv")
np.random.seed(42)
companies = [
    "TechCorp",
    "DataFlow",
    "CloudNet",
    "AI Labs",
    "InfoSys",
    "AppWorks",
    "SoftCore",
    "CodeBase",
    "SmartSys",
    "WebDev",
]
revenue = np.array([35, 95, 140, 200, 65, 170, 110, 55, 125, 80]) + np.random.uniform(-3, 3, len(companies))
profit_margin = np.array([6, 12, 18, 23, 9, 20, 15, 8, 16, 11]) + np.random.uniform(-0.5, 0.5, len(companies))
df = pd.DataFrame({COMPANY: companies, REVENUE: revenue, PROFIT_MARGIN: profit_margin})

# Plot: reads only df and the constants above
label_offset = (df[PROFIT_MARGIN].max() - df[PROFIT_MARGIN].min()) * 0.045

# A label goes below its point when the nearest neighbour sits close above it, where a label above would collide
coords = df[[REVENUE, PROFIT_MARGIN]].to_numpy(dtype=float)
coords = (coords - np.nanmin(coords, axis=0)) / np.ptp(coords, axis=0)
gaps = np.linalg.norm(coords[:, None] - coords[None, :], axis=2)
np.fill_diagonal(gaps, np.inf)
nearest = np.argmin(gaps, axis=1)
below = (gaps.min(axis=1) < 0.08) & (coords[nearest, 1] > coords[:, 1])
above_df = df[~below]
below_df = df[below]

plot = (
    ggplot(df, aes(x=REVENUE, y=PROFIT_MARGIN))
    + geom_point(size=4.5, alpha=0.7, color=PAGE_BG, fill=BRAND, stroke=0.6)
    + geom_text(aes(label=COMPANY), data=above_df, size=8.5, nudge_y=label_offset, va="bottom", color=INK)
    + geom_text(aes(label=COMPANY), data=below_df, size=8.5, nudge_y=-label_offset, va="top", color=INK)
    + scale_x_continuous(expand=(0.06, 0))
    + scale_y_continuous(expand=(0.1, 0))
    + labs(title="scatter-annotated · python · plotnine · anyplot.ai")
    + theme_minimal()
    + theme(
        figure_size=(8, 4.5),
        plot_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
        panel_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
        panel_grid_major=element_line(color=INK, size=0.3, alpha=0.15),
        panel_grid_minor=element_blank(),
        axis_line=element_line(color=INK_SOFT, size=0.5),
        axis_ticks=element_blank(),
        text=element_text(size=7, color=INK),
        axis_title=element_text(size=10, color=INK),
        axis_text=element_text(size=8, color=INK_SOFT),
        plot_title=element_text(size=12, color=INK, weight="bold"),
    )
)

# Save
plot.save(f"plot-{THEME}.png", dpi=400, width=8, height=4.5, units="in", verbose=False)
