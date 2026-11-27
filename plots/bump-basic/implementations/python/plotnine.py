""" anyplot.ai
bump-basic: Basic Bump Chart
Library: plotnine 0.15.9 | Python 3.14.10
Quality: 85/100 | Updated: 2026-11-27
"""

import os

import pandas as pd
from plotnine import (
    aes,
    element_blank,
    element_line,
    element_rect,
    element_text,
    geom_line,
    geom_point,
    geom_text,
    ggplot,
    labs,
    scale_color_manual,
    scale_x_continuous,
    scale_y_reverse,
    theme,
    theme_minimal,
)


# Theme tokens — Imprint palette, theme-adaptive chrome
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Imprint palette: all eight positions, one per entity in order
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

# Columns: set these to your table's column names
PLATFORM = "Platform"  # role: entity
QUARTER = "Quarter"  # role: period
RANK = "Market share rank"  # role: rank

# Data: replace this block with your own table, for example df = pd.read_csv("rankings.csv")
# Streaming platform market share rankings over 8 quarters
quarters = ["Q1'24", "Q2'24", "Q3'24", "Q4'24", "Q1'25", "Q2'25", "Q3'25", "Q4'25"]
rankings = {
    "StreamVue": [1, 1, 1, 2, 2, 3, 3, 4],
    "WavePlay": [2, 3, 3, 1, 1, 1, 1, 1],
    "CloudCast": [4, 2, 2, 3, 3, 2, 2, 2],
    "PixelFlix": [3, 4, 4, 4, 5, 5, 4, 3],
    "SonicNet": [5, 5, 5, 5, 4, 4, 5, 5],
    "EchoTV": [6, 6, 6, 6, 6, 6, 6, 6],
}
df = pd.DataFrame(
    [
        {PLATFORM: platform, QUARTER: quarter, RANK: rank}
        for platform, ranks in rankings.items()
        for quarter, rank in zip(quarters, ranks, strict=True)
    ]
)

# Plot
platforms = df[PLATFORM].unique().tolist()
periods = df[QUARTER].unique().tolist()
period_pos = "Period position"
df[period_pos] = df[QUARTER].map({period: i + 1 for i, period in enumerate(periods)})
df_end = df[df[period_pos] == len(periods)]
rank_breaks = range(int(df[RANK].min()), int(df[RANK].max()) + 1)

title = "bump-basic · python · plotnine · anyplot.ai"

plot = (
    ggplot(df, aes(x=period_pos, y=RANK, color=PLATFORM, group=PLATFORM))
    + geom_line(size=1.4, alpha=0.9)
    + geom_point(size=3.5)
    # Direct end labels instead of a legend
    + geom_text(aes(label=PLATFORM), data=df_end, nudge_x=0.3, ha="left", size=8, color=INK)
    + scale_y_reverse(breaks=rank_breaks)
    + scale_x_continuous(breaks=range(1, len(periods) + 1), labels=periods, limits=(0.7, len(periods) + 1.7))
    + scale_color_manual(values=IMPRINT_PALETTE, limits=platforms)
    + labs(x=QUARTER, y=RANK, title=title)
    + theme_minimal()
    + theme(
        figure_size=(8, 4.5),
        text=element_text(size=7, color=INK_SOFT),
        axis_title=element_text(size=10, color=INK),
        axis_text=element_text(size=8, color=INK_SOFT),
        plot_title=element_text(size=12, weight="bold", color=INK),
        panel_grid_major_x=element_blank(),
        panel_grid_minor=element_blank(),
        panel_grid_major_y=element_line(alpha=0.15, size=0.3, color=INK),
        panel_background=element_rect(fill=PAGE_BG, color="none"),
        plot_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
        legend_position="none",
    )
)

plot.save(f"plot-{THEME}.png", dpi=400, width=8, height=4.5, units="in")
