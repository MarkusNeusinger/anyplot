"""anyplot.ai
chessboard-basic: Chess Board Grid Visualization
Library: plotnine | Python 3.13
Quality: pending | Created: 2026-05-17
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
    scale_x_continuous,
    scale_y_continuous,
    theme,
)


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Data - create 8x8 chess board grid
rows = list(range(1, 9))
cols = list(range(1, 9))
col_labels = ["a", "b", "c", "d", "e", "f", "g", "h"]

# Create grid data
data = []
for row in rows:
    for col in cols:
        # Light squares where (row + col) is even, dark where odd
        # This ensures h1 (row=1, col=8) is light: 1+8=9 is odd, so we flip
        is_light = (row + col) % 2 == 1
        data.append({"col": col, "row": row, "color": "light" if is_light else "dark"})

df = pd.DataFrame(data)

# Chess board colors - classic cream and brown
light_color = "#F0D9B5"
dark_color = "#B58863"

# Create plot
plot = (
    ggplot(df, aes(x="col", y="row", fill="color"))
    + geom_tile(color=INK_SOFT, size=0.3)
    + scale_fill_manual(values={"light": light_color, "dark": dark_color})
    + scale_x_continuous(breaks=list(range(1, 9)), labels=col_labels, expand=(0, 0))
    + scale_y_continuous(breaks=list(range(1, 9)), labels=[str(i) for i in range(1, 9)], expand=(0, 0))
    + coord_fixed(ratio=1)
    + labs(x="Column", y="Row", title="chessboard-basic · plotnine · anyplot.ai")
    + theme(
        figure_size=(9, 9),
        plot_title=element_text(size=24, ha="center", weight="bold", color=INK),
        axis_title=element_text(size=20, color=INK),
        axis_text_x=element_text(size=20, weight="bold", color=INK_SOFT),
        axis_text_y=element_text(size=20, weight="bold", color=INK_SOFT),
        axis_ticks=element_blank(),
        panel_background=element_rect(fill=PAGE_BG),
        panel_grid_major=element_blank(),
        panel_grid_minor=element_blank(),
        legend_position="none",
        plot_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
        panel_border=element_rect(color=INK_SOFT, size=2),
    )
)

# Save
plot.save(f"plot-{THEME}.png", dpi=300, width=9, height=9)
