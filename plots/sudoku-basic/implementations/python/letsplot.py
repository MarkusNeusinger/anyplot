"""anyplot.ai
sudoku-basic: Basic Sudoku Grid
Library: letsplot 4.10.1 | Python 3.13.14
Quality: 86/100 | Updated: 2026-06-25
"""

import os

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
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Classic Sudoku puzzle (0 = empty cell)
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

# Build cell data with position metadata for tooltips
xs, ys, labels, row_nums, col_nums, box_nums, statuses = [], [], [], [], [], [], []
for row in range(9):
    for col in range(9):
        val = grid[row][col]
        xs.append(col + 0.5)
        ys.append(8 - row + 0.5)
        labels.append(str(val) if val != 0 else "")
        row_nums.append(row + 1)
        col_nums.append(col + 1)
        box_nums.append((row // 3) * 3 + (col // 3) + 1)
        statuses.append("given" if val != 0 else "empty")

cells = {"x": xs, "y": ys, "label": labels, "row": row_nums, "col": col_nums, "box": box_nums, "status": statuses}

# Thin grid lines (cell boundaries, skipping 3x3 box positions)
thin_x, thin_y, thin_xend, thin_yend = [], [], [], []
for i in range(10):
    if i % 3 != 0:
        thin_x.append(i)
        thin_y.append(0)
        thin_xend.append(i)
        thin_yend.append(9)
        thin_x.append(0)
        thin_y.append(i)
        thin_xend.append(9)
        thin_yend.append(i)
thin_lines = {"x": thin_x, "y": thin_y, "xend": thin_xend, "yend": thin_yend}

# Thick grid lines (3x3 box boundaries)
thick_x, thick_y, thick_xend, thick_yend = [], [], [], []
for i in (0, 3, 6, 9):
    thick_x.append(i)
    thick_y.append(0)
    thick_xend.append(i)
    thick_yend.append(9)
    thick_x.append(0)
    thick_y.append(i)
    thick_xend.append(9)
    thick_yend.append(i)
thick_lines = {"x": thick_x, "y": thick_y, "xend": thick_xend, "yend": thick_yend}

# Tooltips: show cell position and box number on hover (HTML interactivity)
cell_tooltips = layer_tooltips().line("Row @row, Col @col").line("Box @box").line("@status")

plot = (
    ggplot()
    + geom_tile(aes(x="x", y="y"), data=cells, fill=PAGE_BG, color=PAGE_BG, width=1, height=1, tooltips=cell_tooltips)
    + geom_segment(aes(x="x", y="y", xend="xend", yend="yend"), data=thin_lines, color=INK_SOFT, size=0.4)
    + geom_segment(aes(x="x", y="y", xend="xend", yend="yend"), data=thick_lines, color=INK, size=2.0)
    + geom_text(aes(x="x", y="y", label="label"), data=cells, size=9, color=INK, fontface="bold")
    + coord_fixed(ratio=1)
    + scale_x_continuous(limits=[-0.1, 9.1], expand=[0, 0])
    + scale_y_continuous(limits=[-0.1, 9.1], expand=[0, 0])
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
    + ggsize(600, 600)
)

# Save — scale=4 yields 2400×2400 px (canonical square canvas)
ggsave(plot, f"plot-{THEME}.png", path=".", scale=4)
ggsave(plot, f"plot-{THEME}.html", path=".")
