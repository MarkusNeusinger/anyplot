"""anyplot.ai
sudoku-basic: Basic Sudoku Grid
Library: letsplot 4.10.1 | Python 3.13.14
Quality: pending | Updated: 2026-06-25
"""

import os

import pandas as pd
from lets_plot import (
    LetsPlot,
    aes,
    coord_fixed,
    element_blank,
    element_rect,
    element_text,
    geom_segment,
    geom_text,
    geom_tile,
    gggrid,
    ggplot,
    ggsave,
    ggsize,
    labs,
    layer_tooltips,
    scale_x_continuous,
    scale_y_continuous,
    theme,
    theme_void,
)


LetsPlot.setup_html()

# Imprint palette theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Columns: set these to your table's column names
DIGIT = "Digit"  # role: grid

# Data: replace this block with your own table, for example df = pd.read_csv("puzzle.csv")
# One row per cell in reading order (left to right, top to bottom); a digit of 0 is an empty cell.
grid = [
    [5, 3, 0, 0, 7, 0, 0, 0, 0],
    [6, 0, 0, 1, 9, 5, 0, 0, 0],
    [0, 9, 8, 0, 0, 0, 0, 6, 0],
    [8, 0, 0, 0, 6, 0, 0, 0, 3],
    [4, 0, 0, 8, 0, 3, 0, 0, 1],
    [7, 0, 0, 0, 2, 0, 0, 0, 6],
    [0, 6, 0, 0, 0, 0, 2, 8, 0],
    [0, 0, 0, 4, 1, 9, 0, 0, 5],
    [0, 0, 0, 0, 8, 0, 0, 7, 9],
]
df = pd.DataFrame({DIGIT: [v for r in grid for v in r]})

# Plot: reads only df and the constants above
n = round(len(df) ** 0.5)  # cells per side
row = df.index // n + 1  # numbered from 1 at the top
col = df.index % n + 1
box = round(n**0.5)  # cells per box side

cells = pd.DataFrame(
    {
        "x": col - 0.5,
        "y": n - row + 0.5,
        "label": df[DIGIT].map(lambda v: str(v) if v != 0 else ""),
        "row": row,
        "col": col,
        "box": (row - 1) // box * box + (col - 1) // box + 1,
        "status": df[DIGIT].map(lambda v: "given" if v != 0 else "empty"),
    }
)

# Thin lines on cell boundaries, thick lines on box boundaries
thin = [i for i in range(n + 1) if i % box != 0]
thick = [i for i in range(n + 1) if i % box == 0]


def lines(positions):
    """Full-length vertical and horizontal segments at the given grid positions."""
    return pd.DataFrame(
        {
            "x": positions + [0] * len(positions),
            "y": [0] * len(positions) + positions,
            "xend": positions + [n] * len(positions),
            "yend": [n] * len(positions) + positions,
        }
    )


# Tooltips: show cell position and box number on hover (HTML interactivity)
cell_tooltips = layer_tooltips().line("Row @row, Col @col").line("Box @box").line("@status")

plot = (
    ggplot()
    + geom_tile(aes(x="x", y="y"), data=cells, fill=PAGE_BG, color=PAGE_BG, width=1, height=1, tooltips=cell_tooltips)
    + geom_segment(aes(x="x", y="y", xend="xend", yend="yend"), data=lines(thin), color=INK_SOFT, size=0.4)
    + geom_segment(aes(x="x", y="y", xend="xend", yend="yend"), data=lines(thick), color=INK, size=2.0)
    + geom_text(aes(x="x", y="y", label="label"), data=cells, size=9, color=INK, fontface="bold")
    + coord_fixed(ratio=1)
    + scale_x_continuous(limits=[-0.1, n + 0.1], expand=[0, 0])
    + scale_y_continuous(limits=[-0.1, n + 0.1], expand=[0, 0])
    + labs(title="sudoku-basic · python · letsplot · anyplot.ai")
    + theme_void()
    + theme(
        plot_title=element_text(size=16, color=INK, hjust=0.5, face="bold"),
        plot_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
        panel_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
        axis_title=element_blank(),
        axis_text=element_blank(),
        axis_ticks=element_blank(),
        plot_margin=[40, 40, 40, 40],
    )
)

# The one-panel grid paints the whole square canvas in the page color
plot = gggrid([plot]) + ggsize(600, 600) + theme(plot_background=element_rect(fill=PAGE_BG, color=PAGE_BG))

# Save — scale=4 yields 2400×2400 px (canonical square canvas)
ggsave(plot, f"plot-{THEME}.png", path=".", scale=4)
ggsave(plot, f"plot-{THEME}.html", path=".")
