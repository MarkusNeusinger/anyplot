""" anyplot.ai
datamatrix-basic: Basic Data Matrix 2D Barcode
Library: letsplot 4.9.0 | Python 3.13.13
Quality: 87/100 | Updated: 2026-05-20
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
    ggplot,
    ggsize,
    labs,
    scale_fill_manual,
    theme,
    theme_void,
)
from lets_plot.export import ggsave


LetsPlot.setup_html()

THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"

# Data Matrix encoding — 14×14 matrix (ISO/IEC 16022, ECC 200 structure)
size = 14
content = "MED-SN:A7B2C9D1"

matrix = np.zeros((size, size), dtype=int)

# L-shaped finder pattern: solid black on left column and bottom row
matrix[:, 0] = 1
matrix[-1, :] = 1

# Alternating clock pattern on top row and right column
matrix[0, :] = [1 if i % 2 == 0 else 0 for i in range(size)]
matrix[:, -1] = [1 if i % 2 == 0 else 0 for i in range(size)]

# Data region: pseudo-random fill seeded from content (simulating ECC 200 encoding)
data_hash = sum(ord(c) for c in content)
np.random.seed(data_hash)
for i in range(1, size - 1):
    for j in range(1, size - 1):
        matrix[i, j] = np.random.randint(0, 2)

# Quiet zone (1-module border per ISO/IEC 16022 spec)
quiet_zone = 1
full_size = size + 2 * quiet_zone
full_matrix = np.zeros((full_size, full_size), dtype=int)
full_matrix[quiet_zone : quiet_zone + size, quiet_zone : quiet_zone + size] = matrix

# Convert to long-form DataFrame for lets-plot tile mapping
rows = [
    {"x": j, "y": full_size - 1 - i, "value": int(full_matrix[i, j])}
    for i in range(full_size)
    for j in range(full_size)
]
df = pd.DataFrame(rows)

# Plot
plot = (
    ggplot(df, aes(x="x", y="y", fill="value"))
    + geom_tile()
    + scale_fill_manual(values=["#FFFFFF", "#000000"])
    + coord_fixed()
    + labs(title="datamatrix-basic · python · letsplot · anyplot.ai")
    + theme_void()
    + theme(
        plot_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
        panel_background=element_rect(fill=PAGE_BG),
        plot_title=element_text(size=16, face="bold", hjust=0.5, color=INK),
        legend_position="none",
    )
    + ggsize(600, 600)
)

# Save
ggsave(plot, f"plot-{THEME}.png", path=".", scale=4)
ggsave(plot, f"plot-{THEME}.html", path=".")
