"""anyplot.ai
burndown-sprint: Agile Sprint Burndown Chart
Library: plotnine | Python 3.13
Quality: pending | Created: 2026-06-14
"""

import sys


sys.path.pop(0)  # prevent this file (plotnine.py) from shadowing the plotnine library

import os

import pandas as pd
from plotnine import (
    aes,
    annotate,
    coord_cartesian,
    element_blank,
    element_line,
    element_rect,
    element_text,
    geom_line,
    geom_rect,
    geom_step,
    geom_vline,
    ggplot,
    labs,
    scale_color_manual,
    scale_x_continuous,
    scale_y_continuous,
    theme,
    theme_minimal,
)


# Theme tokens — Imprint palette chrome
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
INK_MUTED = "#6B6A63" if THEME == "light" else "#A8A79F"
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]
ANYPLOT_AMBER = "#DDCC77"

# Sprint data: 10 working days (Jan 8–19 2024), days 0–11 include weekends
# Day 4 (Jan 12, Fri): scope +8 pushes remaining up from expected ~25 to 33
# Days 5–6 (Jan 13–14, Sat–Sun): weekend, remaining stays flat
days = list(range(12))
remaining = [40, 36, 33, 29, 33, 33, 33, 27, 21, 15, 8, 0]
ideal = [round(40 * (1 - d / 11), 2) for d in range(12)]

actual_df = pd.DataFrame({"day": days, "value": remaining, "series": "Actual Remaining"})
ideal_df = pd.DataFrame({"day": days, "value": ideal, "series": "Ideal Burndown"})
weekend_df = pd.DataFrame({"xmin": [4.5], "xmax": [6.5], "ymin": [-2.0], "ymax": [50.0]})

x_breaks = [0, 2, 4, 7, 9, 11]
x_labels = ["Jan 8\n(Mon)", "Jan 10\n(Wed)", "Jan 12\n(Fri)", "Jan 15\n(Mon)", "Jan 17\n(Wed)", "Jan 19\n(Fri)"]

ACTUAL_COLOR = IMPRINT_PALETTE[0]  # #009E73 — Imprint position 1, always first series
IDEAL_COLOR = INK_SOFT  # theme-adaptive muted reference line

title = "burndown-sprint · python · plotnine · anyplot.ai"

plot = (
    ggplot()
    # Weekend shading band — drawn first, behind all data layers
    + geom_rect(
        data=weekend_df, mapping=aes(xmin="xmin", xmax="xmax", ymin="ymin", ymax="ymax"), fill=INK_MUTED, alpha=0.15
    )
    # Ideal burndown: straight dashed reference from 40 → 0
    + geom_line(data=ideal_df, mapping=aes(x="day", y="value", color="series"), linetype="dashed", size=0.9)
    # Actual burndown: step series (work completed in discrete chunks)
    + geom_step(data=actual_df, mapping=aes(x="day", y="value", color="series"), size=1.4)
    # Scope change marker: amber dotted vline on day 4 (Jan 12)
    + geom_vline(xintercept=4.0, linetype="dotted", color=ANYPLOT_AMBER, size=0.8)
    # Scope change label (placed left of marker)
    + annotate("text", x=3.8, y=40.5, label="Scope\n+8 pts", color=ANYPLOT_AMBER, size=3.2, ha="right", va="top")
    # Weekend label inside the shaded band
    + annotate("text", x=5.5, y=20.0, label="Weekend", color=INK_MUTED, size=3.0, ha="center", va="center")
    # Color scale for legend
    + scale_color_manual(
        values={"Actual Remaining": ACTUAL_COLOR, "Ideal Burndown": IDEAL_COLOR},
        breaks=["Actual Remaining", "Ideal Burndown"],
        name="",
    )
    + scale_x_continuous(breaks=x_breaks, labels=x_labels)
    + scale_y_continuous(breaks=[0, 10, 20, 30, 40])
    # Clip view so weekend rect (ymin=-2, ymax=50) stays within the axes
    + coord_cartesian(xlim=(-0.5, 11.5), ylim=(0, 43))
    + labs(x="Sprint Day", y="Remaining Story Points", title=title)
    + theme_minimal()
    + theme(
        figure_size=(8, 4.5),
        plot_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
        panel_background=element_rect(fill=PAGE_BG),
        panel_grid_major_y=element_line(color=INK, size=0.3, alpha=0.12),
        panel_grid_major_x=element_blank(),
        panel_grid_minor=element_blank(),
        panel_border=element_blank(),
        axis_line=element_line(color=INK_SOFT, size=0.4),
        axis_title=element_text(color=INK, size=10),
        axis_text=element_text(color=INK_SOFT, size=8),
        plot_title=element_text(color=INK, size=12),
        legend_background=element_rect(fill=ELEVATED_BG, color=INK_SOFT),
        legend_text=element_text(color=INK_SOFT, size=8),
        legend_title=element_blank(),
        legend_position="bottom",
    )
)

plot.save(f"plot-{THEME}.png", dpi=400, width=8, height=4.5, units="in")
