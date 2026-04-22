""" pyplots.ai
chessboard-basic: Chess Board Grid Visualization
Library: plotnine 0.15.2 | Python 3.13.11
Quality: 95/100 | Created: 2026-01-08
"""

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
    + geom_tile(color="#8B7355", size=0.3)
    + scale_fill_manual(values={"light": light_color, "dark": dark_color})
    + scale_x_continuous(breaks=list(range(1, 9)), labels=col_labels, expand=(0, 0))
    + scale_y_continuous(breaks=list(range(1, 9)), labels=[str(i) for i in range(1, 9)], expand=(0, 0))
    + coord_fixed(ratio=1)
    + labs(x="", y="", title="chessboard-basic · plotnine · pyplots.ai")
    + theme(
        figure_size=(12, 12),
        plot_title=element_text(size=24, ha="center", weight="bold"),
        axis_text_x=element_text(size=20, weight="bold"),
        axis_text_y=element_text(size=20, weight="bold"),
        axis_ticks=element_blank(),
        panel_background=element_rect(fill="white"),
        panel_grid_major=element_blank(),
        panel_grid_minor=element_blank(),
        legend_position="none",
        plot_background=element_rect(fill="white"),
        panel_border=element_rect(color="#8B7355", size=2),
    )
)

# Save
plot.save("plot.png", dpi=300, width=12, height=12)
