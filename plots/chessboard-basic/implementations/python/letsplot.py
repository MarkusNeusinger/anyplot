""" anyplot.ai
chessboard-basic: Chess Board Grid Visualization
Library: letsplot 4.9.0 | Python 3.13.13
Quality: 87/100 | Updated: 2026-05-17
"""

import os
import shutil

import pandas as pd
from lets_plot import (
    LetsPlot,
    aes,
    coord_fixed,
    element_blank,
    element_text,
    geom_tile,
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

# Data - create 8x8 chess board grid
columns = list("abcdefgh")
rows = list(range(1, 9))

data = []
for col_idx, col in enumerate(columns):
    for row_idx, row in enumerate(rows):
        is_light = (col_idx + row_idx) % 2 == 1
        data.append({"column": col, "row": str(row), "color": "light" if is_light else "dark"})

df = pd.DataFrame(data)

# Create the chess board visualization
plot = (
    ggplot(df, aes(x="column", y="row", fill="color"))
    + geom_tile(color="#5D4037", size=0.5)
    + scale_fill_manual(values={"light": "#F5DEB3", "dark": "#8B4513"})
    + scale_x_discrete(limits=columns)
    + scale_y_discrete(limits=[str(r) for r in rows])
    + coord_fixed(ratio=1)
    + labs(title="chessboard-basic · letsplot · anyplot.ai")
    + theme(
        plot_background=element_blank(),
        panel_background=element_blank(),
        panel_grid=element_blank(),
        plot_title=element_text(size=24, color=INK),
        axis_title=element_blank(),
        axis_text_x=element_text(size=20, color=INK_SOFT),
        axis_text_y=element_text(size=20, color=INK_SOFT),
        legend_position="none",
    )
    + ggsize(1200, 1200)
)

# Save as PNG and HTML with theme-suffixed filenames
ggsave(plot, f"plot-{THEME}.png", scale=3)
ggsave(plot, f"plot-{THEME}.html")

if os.path.exists(f"lets-plot-images/plot-{THEME}.png"):
    shutil.move(f"lets-plot-images/plot-{THEME}.png", f"plot-{THEME}.png")
if os.path.exists(f"lets-plot-images/plot-{THEME}.html"):
    shutil.move(f"lets-plot-images/plot-{THEME}.html", f"plot-{THEME}.html")
