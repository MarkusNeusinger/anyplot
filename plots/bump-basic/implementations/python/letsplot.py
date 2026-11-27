""" anyplot.ai
bump-basic: Basic Bump Chart
Library: letsplot 4.11.0 | Python 3.14.10
Quality: 83/100 | Updated: 2026-11-27
"""

import os

import pandas as pd
from lets_plot import (
    LetsPlot,
    aes,
    element_blank,
    element_line,
    element_rect,
    element_text,
    geom_line,
    geom_point,
    geom_text,
    ggplot,
    ggsave,
    ggsize,
    labs,
    layer_tooltips,
    scale_color_manual,
    scale_x_continuous,
    scale_y_reverse,
    theme,
    theme_minimal,
)


LetsPlot.setup_html()

# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
GRID = "rgba(26,26,23,0.15)" if THEME == "light" else "rgba(240,239,232,0.15)"

# Imprint palette: all eight positions in canonical order
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

# Columns: set these to your table's column names
ENTITY = "Company"  # role: entity
PERIOD = "Quarter"  # role: period
RANK = "Market rank"  # role: rank

# Data: replace this block with your own table, for example df = pd.read_csv("rankings.csv")
df = pd.DataFrame(
    {
        ENTITY: ["Northwind"] * 6
        + ["Brightline"] * 6
        + ["Cobalt Systems"] * 6
        + ["Meridian Foods"] * 6
        + ["Sable Energy"] * 6,
        PERIOD: ["Q1", "Q2", "Q3", "Q4", "Q5", "Q6"] * 5,
        RANK: [1, 2, 3, 2, 1, 1] + [3, 1, 1, 3, 4, 5] + [2, 3, 2, 1, 2, 3] + [4, 4, 5, 4, 3, 2] + [5, 5, 4, 5, 5, 4],
    }
)

# Plot: reads only df and the constants above
periods = list(dict.fromkeys(df[PERIOD]))
entities = list(dict.fromkeys(df[ENTITY]))
position = "period_pos"  # numeric x position of each period, in the data's order
df[position] = df[PERIOD].map({name: i + 1 for i, name in enumerate(periods)})
last = df[df[PERIOD] == periods[-1]]
ranks = sorted(df[RANK].dropna().unique())

tooltip_cfg = layer_tooltips().title(f"@{{{ENTITY}}}").line(f"{PERIOD}|@{{{PERIOD}}}").line(f"{RANK}|@{{{RANK}}}")

title = "bump-basic · python · letsplot · anyplot.ai"

plot = (
    ggplot(df, aes(x=position, y=RANK, color=ENTITY, group=ENTITY))
    + geom_line(size=1.6, tooltips=tooltip_cfg)
    + geom_point(size=5, tooltips=tooltip_cfg)
    # Direct entity labels right of each line's last point, in the line's color
    + geom_text(aes(label=ENTITY), data=last, nudge_x=0.15, hjust=0, size=6)
    + scale_y_reverse(breaks=ranks)
    + scale_x_continuous(breaks=list(range(1, len(periods) + 1)), labels=periods, limits=[0.7, len(periods) + 1.1])
    + scale_color_manual(values=IMPRINT_PALETTE[: len(entities)])
    + labs(x=PERIOD, y=RANK, title=title)
    + theme_minimal()
    + theme(
        plot_title=element_text(size=16, color=INK),
        axis_title=element_text(size=12, color=INK),
        axis_text=element_text(size=10, color=INK_SOFT),
        axis_line=element_blank(),
        axis_line_x=element_line(color=INK_SOFT),
        axis_line_y=element_line(color=INK_SOFT),
        panel_border=element_blank(),
        axis_ticks=element_blank(),
        legend_position="none",
        panel_grid_major_x=element_blank(),
        panel_grid_minor=element_blank(),
        panel_grid_major_y=element_line(color=GRID, size=0.3),
        plot_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
        panel_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
    )
    + ggsize(800, 450)
)

# Save
ggsave(plot, f"plot-{THEME}.png", path=".", scale=4)
ggsave(plot, f"plot-{THEME}.html", path=".")
