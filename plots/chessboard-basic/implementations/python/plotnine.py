"""anyplot.ai
chessboard-basic: Chess Board Grid Visualization
Library: plotnine 0.15.4 | Python 3.13.13
Quality: 94/100 | Updated: 2026-05-17
"""

import os

import pandas as pd
from plotnine import (
    aes,
    coord_fixed,
    element_blank,
    element_rect,
    element_text,
    geom_tile,
    ggplot,
    labs,
    scale_fill_manual,
    scale_x_discrete,
    scale_y_continuous,
    theme,
)


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Imprint palette: all eight positions, in canonical order (the board uses its own domain pair below)
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

# Constants
SQUARE_COLORS = {"light": "#EEEED2", "dark": "#769656"}  # classic ivory and green tournament board

# Columns: set these to your table's column names
FILE = "Column"  # role: columns
RANK = "Row"  # role: rows
SHADE = "Square shade"  # role: extra

# Data: replace this block with your own table, for example df = pd.read_csv("board.csv")
files = list("abcdefgh")
df = pd.DataFrame(
    [
        {FILE: letter, RANK: rank, SHADE: "light" if (file_no + rank) % 2 == 1 else "dark"}
        for file_no, letter in enumerate(files, start=1)
        for rank in range(1, 9)
    ]
)

# Plot: reads only df and the constants above
plot = (
    ggplot(df, aes(x=FILE, y=RANK, fill=SHADE))
    + geom_tile(color=INK_SOFT, size=0.3)
    + scale_fill_manual(values=SQUARE_COLORS, limits=list(SQUARE_COLORS))
    + scale_x_discrete(limits=df[FILE].unique().tolist(), expand=(0, 0))
    + scale_y_continuous(breaks=sorted(df[RANK].unique()), expand=(0, 0))
    + coord_fixed(ratio=1)
    + labs(title="chessboard-basic · python · plotnine · anyplot.ai")
    + theme(
        figure_size=(6, 6),
        plot_title=element_text(size=14, ha="center", weight="bold", color=INK),
        axis_title=element_text(size=12, color=INK),
        axis_text=element_text(size=12, weight="bold", color=INK_SOFT),
        axis_ticks=element_blank(),
        panel_background=element_rect(fill=PAGE_BG),
        panel_grid_major=element_blank(),
        panel_grid_minor=element_blank(),
        legend_position="none",
        plot_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
        panel_border=element_rect(color=INK_SOFT, size=1.5),
    )
)

# Save
plot.save(f"plot-{THEME}.png", dpi=400, width=6, height=6, units="in")
