"""anyplot.ai
area-cumulative-flow: Cumulative Flow Diagram for Workflow Analytics
Library: lets-plot | Python 3.13
Quality: pending | Created: 2026-08-18
"""

import os

import numpy as np
import pandas as pd
from lets_plot import (
    LetsPlot,
    aes,
    element_blank,
    element_line,
    element_rect,
    element_text,
    geom_area,
    geom_line,
    ggplot,
    ggsave,
    ggsize,
    ggtitle,
    labs,
    scale_color_manual,
    scale_fill_manual,
    scale_x_datetime,
    theme,
    theme_minimal,
)


LetsPlot.setup_html()

# Theme tokens (see prompts/default-style-guide.md "Background" + "Theme-adaptive Chrome")
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Imprint palette (categorical, canonical order) — position 1 always #009E73
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030"]

# Data — a production line's stage-by-stage cumulative item counts (manufacturing CFD)
np.random.seed(42)
n_days = 90
dates = pd.date_range("2024-04-01", periods=n_days, freq="D")
stages = ["Raw Materials", "Machining", "Assembly", "Quality Check", "Shipped"]
stage_capacity = [None, 19, 15, 11, 8]  # daily throughput ceiling per downstream stage

daily_intake = np.random.randint(15, 26, size=n_days)
cumulative = np.zeros((len(stages), n_days))
cumulative[0] = np.cumsum(daily_intake)

for stage_idx in range(1, len(stages)):
    upstream = cumulative[stage_idx - 1]
    capacity = stage_capacity[stage_idx]
    processed = 0.0
    for day in range(n_days):
        throughput = min(upstream[day] - processed, capacity)
        processed += throughput
        cumulative[stage_idx, day] = processed

# geom_area(position='identity') stacks layers by *factor level* order: the first
# level renders in front, the last level renders behind. The smallest (latest-stage)
# curve must be the first level so it sits in front, and the largest (earliest-stage)
# curve must be the last level so it sits behind and shows through as the top band.
z_order = list(reversed(stages))

flow_df = pd.DataFrame(
    {
        "date": np.tile(dates, len(stages)),
        "stage": pd.Categorical(np.repeat(stages, n_days), categories=z_order, ordered=True),
        "count": cumulative.flatten(),
    }
)

# Plot — see default-style-guide.md "Visual Sizing Defaults" for the canvas + sizing values
plot = (
    ggplot(flow_df, aes(x="date", y="count", fill="stage"))
    + geom_area(position="identity", color=PAGE_BG, size=0.6)
    + geom_line(aes(color="stage"), position="identity", size=0.9, show_legend=False)
    + scale_fill_manual(values=IMPRINT_PALETTE, breaks=stages, name="Stage")
    + scale_color_manual(values=IMPRINT_PALETTE, breaks=stages)
    + scale_x_datetime(format="%b %d")
    + labs(x="Date", y="Cumulative Items")
    + ggtitle("area-cumulative-flow · python · letsplot · anyplot.ai")
    + ggsize(800, 450)
)

# Style — theme-adaptive chrome (see prompts/library/letsplot.md)
plot = (
    plot
    + theme_minimal()
    + theme(
        plot_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
        panel_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
        panel_grid_major_x=element_blank(),
        panel_grid_minor=element_blank(),
        panel_grid_major_y=element_line(color=INK, size=0.3),
        panel_border=element_blank(),
        axis_title=element_text(color=INK, size=12),
        axis_text=element_text(color=INK_SOFT, size=10),
        axis_line_x=element_line(color=INK_SOFT),
        axis_line_y=element_line(color=INK_SOFT),
        plot_title=element_text(color=INK, size=16),
        legend_background=element_rect(fill=ELEVATED_BG, color=INK_SOFT),
        legend_text=element_text(color=INK_SOFT, size=10),
        legend_title=element_text(color=INK, size=11),
        legend_position="right",
    )
)

# Save
ggsave(plot, f"plot-{THEME}.png", path=".", scale=4)
ggsave(plot, f"plot-{THEME}.html", path=".")
