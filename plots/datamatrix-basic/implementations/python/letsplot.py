"""anyplot.ai
datamatrix-basic: Basic Data Matrix 2D Barcode
Library: letsplot 4.9.0 | Python 3.13.13
Quality: pending | Updated: 2026-05-20
"""

import os

import numpy as np
import pandas as pd
from lets_plot import (
    LetsPlot,
    aes,
    coord_fixed,
    element_rect,
    element_text,
    geom_tile,
    gggrid,
    ggplot,
    ggsize,
    labs,
    layer_tooltips,
    scale_fill_manual,
    theme,
    theme_void,
)
from lets_plot.export import ggsave


LetsPlot.setup_html()

THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Constants
CONTENT = "MED-SN:A7B2C9D1"
SIZE = 14  # modules per side (ISO/IEC 16022, ECC 200)
QUIET_ZONE = 1  # modules of blank border

# role: x position of the module (column)
X = "x"
# role: y position of the module (row, counted from the bottom)
Y = "y"
# role: 1 for a black module, 0 for a white one
VALUE = "value"
# role: structural region of the symbol, shown in the tooltip
REGION = "region"

# Data
matrix = np.zeros((SIZE, SIZE), dtype=int)
matrix[:, 0] = 1  # L-shaped finder pattern: left column and bottom row
matrix[-1, :] = 1
clock = np.arange(SIZE) % 2 == 0  # alternating clock pattern: top row and right column
matrix[0, :] = clock
matrix[:, -1] = clock

# Data region: pseudo-random fill seeded from the content (simulating ECC 200 encoding)
rng = np.random.default_rng(sum(ord(c) for c in CONTENT))
matrix[1:-1, 1:-1] = rng.integers(0, 2, size=(SIZE - 2, SIZE - 2))

full = np.pad(matrix, QUIET_ZONE)
rows = []
for i in range(full.shape[0]):
    for j in range(full.shape[1]):
        qi, qj = i - QUIET_ZONE, j - QUIET_ZONE
        if not (0 <= qi < SIZE and 0 <= qj < SIZE):
            region = "Quiet Zone"
        elif qj == 0 or qi == SIZE - 1:
            region = "Finder Pattern (L-shape)"
        elif qi == 0 or qj == SIZE - 1:
            region = "Timing Pattern (alternating)"
        else:
            region = "Data Region (ECC 200)"
        rows.append({X: j, Y: full.shape[0] - 1 - i, VALUE: int(full[i, j]), REGION: region})

df = pd.DataFrame(rows)

# Plot
modules = df[X].max() + 1 - 2 * QUIET_ZONE
tooltips = layer_tooltips().line(f"@{REGION}").line(f"Encoded: {CONTENT}")

plot = (
    ggplot(df, aes(x=X, y=Y, fill=VALUE))
    + geom_tile(tooltips=tooltips)
    + scale_fill_manual(values=["#FFFFFF", "#000000"])
    + coord_fixed()
    + labs(
        title="datamatrix-basic · python · letsplot · anyplot.ai",
        subtitle=f"Encoded: {CONTENT}  ·  {modules}×{modules} ECC 200  ·  ISO/IEC 16022",
    )
    + theme_void()
    + theme(
        plot_title=element_text(size=16, face="bold", hjust=0.5, color=INK),
        plot_subtitle=element_text(size=12, hjust=0.5, color=INK_SOFT),
        legend_position="none",
    )
)

# The one-panel grid paints the whole square canvas in the page color
plot = gggrid([plot]) + ggsize(600, 600) + theme(plot_background=element_rect(fill=PAGE_BG, color=PAGE_BG))

# Save
ggsave(plot, f"plot-{THEME}.png", path=".", scale=4)
ggsave(plot, f"plot-{THEME}.html", path=".")
