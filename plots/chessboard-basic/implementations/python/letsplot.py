""" pyplots.ai
chessboard-basic: Chess Board Grid Visualization
Library: letsplot 4.8.2 | Python 3.13.11
Quality: 95/100 | Created: 2026-01-08
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

# Data - create 8x8 chess board grid
columns = list("abcdefgh")
rows = list(range(1, 9))

# Build data for all 64 squares
data = []
for col_idx, col in enumerate(columns):
    for row_idx, row in enumerate(rows):
        # Light square at h1 (col_idx=7, row_idx=0) means (col_idx + row_idx) % 2 == 1 is light
        is_light = (col_idx + row_idx) % 2 == 1
        data.append({"column": col, "row": str(row), "color": "light" if is_light else "dark"})

df = pd.DataFrame(data)

# Create the chess board visualization
plot = (
    ggplot(df, aes(x="column", y="row", fill="color"))
    + geom_tile(color="#5D4037", size=0.5)  # Brown borders for definition
    + scale_fill_manual(values={"light": "#F5DEB3", "dark": "#8B4513"})  # Cream and brown
    + scale_x_discrete(limits=columns)
    + scale_y_discrete(limits=[str(r) for r in rows])
    + coord_fixed(ratio=1)  # 1:1 aspect ratio for square cells
    + labs(title="chessboard-basic · letsplot · pyplots.ai")
    + theme(
        plot_title=element_text(size=24, face="bold"),
        axis_title=element_blank(),
        axis_text_x=element_text(size=20, face="bold"),
        axis_text_y=element_text(size=20, face="bold"),
        legend_position="none",
        panel_grid=element_blank(),
        panel_background=element_blank(),
        plot_background=element_blank(),
    )
    + ggsize(1200, 1200)  # Square canvas, scaled 3x = 3600x3600 px
)

# Save as PNG (scale 3x for 3600x3600 px output)
ggsave(plot, "plot.png", scale=3)

# Save interactive HTML version
ggsave(plot, "plot.html")

# lets-plot saves to a subdirectory by default - move files to current directory
if os.path.exists("lets-plot-images/plot.png"):
    shutil.move("lets-plot-images/plot.png", "plot.png")
if os.path.exists("lets-plot-images/plot.html"):
    shutil.move("lets-plot-images/plot.html", "plot.html")
if os.path.exists("lets-plot-images") and not os.listdir("lets-plot-images"):
    os.rmdir("lets-plot-images")
