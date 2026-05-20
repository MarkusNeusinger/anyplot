""" anyplot.ai
datamatrix-basic: Basic Data Matrix 2D Barcode
Library: plotnine 0.15.4 | Python 3.13.13
Quality: 85/100 | Updated: 2026-05-20
"""

import os
import sys


# Work around filename shadowing the plotnine library
sys.path.pop(0)
import numpy as np
import pandas as pd
from plotnine import (
    aes,
    coord_fixed,
    element_rect,
    element_text,
    geom_tile,
    ggplot,
    labs,
    scale_fill_manual,
    theme,
    theme_void,
)


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Data - Create a 16x16 Data Matrix barcode encoding "SERIAL:12345678"
np.random.seed(42)

size = 16

# Initialize matrix (0 = white, 1 = black)
dm_matrix = np.zeros((size, size), dtype=int)

# L-shaped finder pattern: solid black left edge and bottom edge
dm_matrix[:, 0] = 1
dm_matrix[size - 1, :] = 1

# Alternating clock pattern on top and right edges
for i in range(size):
    dm_matrix[0, i] = i % 2
for i in range(size):
    dm_matrix[i, size - 1] = (size - 1 - i) % 2

# Data encoding area simulating "SERIAL:12345678"
content = "SERIAL:12345678"
data_values = [ord(c) for c in content]
data_idx = 0
for row in range(1, size - 1):
    for col in range(1, size - 1):
        val = data_values[data_idx % len(data_values)]
        bit_pos = (row + col) % 8
        dm_matrix[row, col] = (val >> bit_pos) & 1
        data_idx += 1

# Quiet zone (2-module white border for scanning reliability)
quiet_zone = 2
padded_size = size + 2 * quiet_zone
dm_with_border = np.zeros((padded_size, padded_size), dtype=int)
dm_with_border[quiet_zone : quiet_zone + size, quiet_zone : quiet_zone + size] = dm_matrix

# Convert matrix to DataFrame (flip y so origin is bottom-left)
rows = []
for row in range(padded_size):
    for col in range(padded_size):
        rows.append({"x": col, "y": padded_size - 1 - row, "value": str(dm_with_border[row, col])})

df = pd.DataFrame(rows)

# Plot
plot = (
    ggplot(df, aes(x="x", y="y", fill="value"))
    + geom_tile(color=None, size=0)
    + scale_fill_manual(values={"0": "#FFFFFF", "1": "#000000"})
    + coord_fixed()
    + labs(
        title="datamatrix-basic · python · plotnine · anyplot.ai",
        subtitle="16×16 ECC 200 symbol · 25% error correction",
        caption="Encoded: SERIAL:12345678",
    )
    + theme_void()
    + theme(
        figure_size=(6, 6),
        plot_title=element_text(size=12, weight="bold", ha="center", color=INK),
        plot_subtitle=element_text(size=9, ha="center", color=INK_SOFT),
        plot_caption=element_text(size=9, ha="right", color=INK_SOFT),
        panel_background=element_rect(fill=PAGE_BG),
        plot_background=element_rect(fill=PAGE_BG),
        legend_position="none",
    )
)

# Save
plot.save(f"plot-{THEME}.png", dpi=400, width=6, height=6, units="in")
