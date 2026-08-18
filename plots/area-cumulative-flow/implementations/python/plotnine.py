""" anyplot.ai
area-cumulative-flow: Cumulative Flow Diagram for Workflow Analytics
Library: plotnine 0.15.8 | Python 3.13.15
Quality: 88/100 | Updated: 2026-08-18
"""

import os
import sys


# Remove current directory from sys.path to avoid shadowing the plotnine package
_here = os.path.dirname(os.path.abspath(__file__))
_cleaned = [p for p in sys.path if os.path.abspath(p) != _here]
sys.path.clear()
sys.path.extend(_cleaned)

import numpy as np
import pandas as pd
from plotnine import (
    aes,
    annotate,
    element_blank,
    element_line,
    element_rect,
    element_text,
    geom_area,
    ggplot,
    labs,
    scale_fill_manual,
    scale_x_datetime,
    scale_y_continuous,
    theme,
)


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

IMPRINT = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030"]

# Data
np.random.seed(42)
n_days = 90
dates = pd.date_range("2024-01-01", periods=n_days)
t = np.arange(n_days)

# Throughput ramps as the team finds its rhythm (~90 items completed over 90 days)
throughput = (0.4 + 0.013 * t + np.random.randn(n_days) * 0.2).clip(0.1)
cum_done = np.round(np.cumsum(throughput)).astype(int)
cum_done = np.maximum.accumulate(cum_done)

# WIP per stage — Development is the bottleneck (widest band)
testing_wip = (7 + 2 * np.sin(t / 25) + np.random.randn(n_days) * 1.0).clip(3).round().astype(int)
dev_wip = (13 + 4 * np.sin(t / 20) + np.random.randn(n_days) * 1.5).clip(6).round().astype(int)
analysis_wip = (5 + np.random.randn(n_days) * 1.0).clip(2).round().astype(int)
backlog_wip = (20 - 0.05 * t + np.random.randn(n_days) * 2.0).clip(8).round().astype(int)

# Cumulative boundary lines (monotonically non-decreasing)
cum_testing = np.maximum.accumulate(cum_done + testing_wip)
cum_dev = np.maximum.accumulate(cum_testing + dev_wip)
cum_analysis = np.maximum.accumulate(cum_dev + analysis_wip)
cum_backlog = np.maximum.accumulate(cum_analysis + backlog_wip)

# Band heights: WIP in each stage (difference between adjacent boundary lines).
# plotnine stacks geom_area with the LAST factor level at the bottom.
# Spec: earliest stage (Backlog) on top, latest stage (Done) on bottom.
# Factor order → Done last so it renders at the bottom of the chart.
stage_order = ["Backlog", "Analysis", "Development", "Testing", "Done"]
bands = [
    cum_backlog - cum_analysis,  # Backlog WIP   → visual top
    cum_analysis - cum_dev,  # Analysis WIP
    cum_dev - cum_testing,  # Development WIP (bottleneck)
    cum_testing - cum_done,  # Testing WIP
    cum_done,  # Done (cumulative completed) → visual bottom
]

df = pd.concat(
    [pd.DataFrame({"date": dates, "stage": stage, "wip": wip}) for stage, wip in zip(stage_order, bands, strict=True)],
    ignore_index=True,
)
df["stage"] = pd.Categorical(df["stage"], categories=stage_order, ordered=True)

# Colors assigned to visual layers (bottom → top): Done, Testing, Development, Analysis, Backlog
visual_order = ["Done", "Testing", "Development", "Analysis", "Backlog"]
stage_colors = dict(zip(visual_order, IMPRINT, strict=True))

# Annotation: pinpoint the Development bottleneck at day 55 (band midpoint in stacked space)
idx = 55
x_annot = dates[idx]
y_annot = int((cum_testing[idx] + cum_dev[idx]) / 2)

# Title — canonical format, well under the 67-char baseline so no fontsize scaling needed
title = "area-cumulative-flow · python · plotnine · anyplot.ai"

# Plot
anyplot_theme = theme(
    figure_size=(8, 4.5),
    plot_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
    panel_background=element_rect(fill=PAGE_BG),
    panel_grid_major_x=element_blank(),
    panel_grid_major_y=element_line(color=INK_SOFT, size=0.3, alpha=0.20),
    panel_grid_minor=element_blank(),
    panel_border=element_blank(),
    axis_title=element_text(color=INK, size=10),
    axis_text=element_text(color=INK_SOFT, size=8),
    # L-shaped frame: bottom x-axis line and left y-axis line only
    axis_line_x=element_line(color=INK_SOFT),
    axis_line_y=element_line(color=INK_SOFT),
    plot_title=element_text(color=INK, size=12, face="bold"),
    legend_background=element_rect(fill=ELEVATED_BG, color=INK_SOFT),
    legend_text=element_text(color=INK_SOFT, size=8),
    # Slightly larger legend title for visual hierarchy within the legend
    legend_title=element_text(color=INK, size=9, face="bold"),
    legend_position="right",
    # Tight breathing room between plot area and legend — avoids the excess
    # right-side whitespace flagged in the previous review
    legend_box_spacing=0.02,
    plot_margin=0.02,
)

plot = (
    ggplot(df, aes(x="date", y="wip", fill="stage"))
    + geom_area(position="stack", alpha=0.88, color=PAGE_BG, size=0.3)
    + scale_fill_manual(values=stage_colors)
    # date axis hugs the data range — no leading/trailing padding
    + scale_x_datetime(date_labels="%b %d", date_breaks="2 weeks", expand=(0, 0))
    # y axis: no padding at the baseline, a touch of headroom above the stack top
    + scale_y_continuous(expand=(0, 0, 0.04, 0))
    + labs(x="Date", y="Cumulative Items", fill="Stage", title=title)
    # Callout draws the viewer's eye to the Development bottleneck
    + annotate(
        "text",
        x=x_annot,
        y=y_annot,
        label="← bottleneck",
        color="#FFFFFF",
        size=3.5,
        ha="left",
        va="center",
        fontstyle="italic",
    )
    + anyplot_theme
)

# Save
plot.save(f"plot-{THEME}.png", dpi=400, width=8, height=4.5, units="in", verbose=False)
