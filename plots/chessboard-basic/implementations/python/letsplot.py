""" anyplot.ai
chessboard-basic: Chess Board Grid Visualization
Library: letsplot 4.11.0 | Python 3.14.10
Quality: 83/100 | Updated: 2026-11-26
"""

import os
import shutil

import pandas as pd
from lets_plot import (
    LetsPlot,
    aes,
    coord_fixed,
    element_blank,
    element_rect,
    element_text,
    geom_tile,
    gggrid,
    ggplot,
    ggsave,
    ggsize,
    labs,
    scale_fill_manual,
    scale_x_discrete,
    scale_y_discrete,
    theme,
)


LetsPlot.setup_html()

# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Imprint palette: all eight positions, in canonical order
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

# Constants
SQUARE_COLORS = {"light": "#F5DEB3", "dark": "#8B4513"}  # classic cream / brown board
BORDER = "#5D4037"

# Columns: set these to your table's column names
FILE = "File"  # role: columns
RANK = "Rank"  # role: rows
SHADE = "Shade"  # role: extra

# Data: replace this block with your own table, one row per square
files = list("abcdefgh")
ranks = [str(r) for r in range(1, 9)]
df = pd.DataFrame(
    [
        {FILE: f, RANK: r, SHADE: "light" if (f_idx + r_idx) % 2 == 1 else "dark"}
        for f_idx, f in enumerate(files)
        for r_idx, r in enumerate(ranks)
    ]
)

# Plot
plot = (
    ggplot(df, aes(x=FILE, y=RANK, fill=SHADE))
    + geom_tile(color=BORDER, size=0.5)
    + scale_fill_manual(values=SQUARE_COLORS)
    + scale_x_discrete(limits=list(df[FILE].unique()))
    + scale_y_discrete(limits=list(df[RANK].unique()))
    + coord_fixed(ratio=1)
    + labs(title="chessboard-basic · python · letsplot · anyplot.ai")
    + theme(
        plot_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
        panel_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
        panel_grid=element_blank(),
        plot_title=element_text(size=16, color=INK),
        axis_title=element_blank(),
        axis_text_x=element_text(size=12, color=INK_SOFT),
        axis_text_y=element_text(size=12, color=INK_SOFT),
        axis_ticks=element_blank(),
        axis_line=element_blank(),
        panel_border=element_blank(),
        legend_position="none",
    )
)

# The fixed aspect leaves the canvas edges transparent: a one-panel grid paints the page color there
plot = gggrid([plot]) + ggsize(600, 600) + theme(plot_background=element_rect(fill=PAGE_BG, color=PAGE_BG))

# Save as PNG and HTML with theme-suffixed filenames
ggsave(plot, f"plot-{THEME}.png", scale=4)
ggsave(plot, f"plot-{THEME}.html")

if os.path.exists(f"lets-plot-images/plot-{THEME}.png"):
    shutil.move(f"lets-plot-images/plot-{THEME}.png", f"plot-{THEME}.png")
if os.path.exists(f"lets-plot-images/plot-{THEME}.html"):
    shutil.move(f"lets-plot-images/plot-{THEME}.html", f"plot-{THEME}.html")
