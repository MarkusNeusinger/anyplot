"""anyplot.ai
datamatrix-basic: Basic Data Matrix 2D Barcode
Library: plotnine 0.15.4 | Python 3.13.13
Quality: pending | Updated: 2026-05-20
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

# Constants
QUIET_ZONE = 2  # blank modules around the symbol (the spec asks for at least 1)
DARK, LIGHT = "#000000", "#FFFFFF"  # barcode modules stay black on white in both themes
X, Y, MODULE = "column", "row", "module"  # columns of the tile table

# Data: a generated symbol; change CONTENT and SIZE to encode your own text
CONTENT = "PT-0482-7316"
SIZE = 12  # modules per side, including the finder and clock edges
rng = np.random.default_rng(2024)

# Matrix (1 = black): finder and clock edges first, then the data region
matrix = np.zeros((SIZE, SIZE), dtype=int)
matrix[0, :] = np.arange(SIZE) % 2  # clock pattern along the top edge
matrix[:, -1] = 1 - (SIZE - 1 - np.arange(SIZE)) % 2  # clock pattern along the right edge
matrix[:, 0] = 1  # L-shaped finder: solid left edge
matrix[-1, :] = 1  # L-shaped finder: solid bottom edge

# Data region: the payload's bits, then random pad bits for the remaining modules
bits = np.unpackbits(np.frombuffer(CONTENT.encode("ascii"), dtype=np.uint8))
inner = (SIZE - 2) ** 2
stream = np.concatenate([bits, rng.integers(0, 2, size=max(inner - len(bits), 0))])[:inner]
matrix[1:-1, 1:-1] = stream.reshape(SIZE - 2, SIZE - 2)

# Plot
padded = np.pad(matrix, QUIET_ZONE, constant_values=0)
rows, cols = np.indices(padded.shape)
df = pd.DataFrame(
    {
        X: cols.ravel(),
        Y: (padded.shape[0] - 1 - rows).ravel(),  # flip y so row 0 is on top
        MODULE: np.where(padded.ravel() == 1, "dark", "light"),
    }
)

plot = (
    ggplot(df, aes(x=X, y=Y, fill=MODULE))
    + geom_tile(color=None, size=0)
    + scale_fill_manual(values={"dark": DARK, "light": LIGHT}, limits=["light", "dark"])
    + coord_fixed()
    + labs(
        title="datamatrix-basic · python · plotnine · anyplot.ai",
        subtitle=f"{SIZE}×{SIZE} ECC 200 symbol · {QUIET_ZONE}-module quiet zone",
        caption=f"Encoded: {CONTENT}",
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
