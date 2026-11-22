"""anyplot.ai
density-rug: Density Plot with Rug Marks
Library: plotnine 0.15.4 | Python 3.13.13
Quality: 93/100 | Updated: 2026-05-18
"""

import os

import numpy as np
import pandas as pd
from plotnine import (
    aes,
    element_line,
    element_rect,
    element_text,
    geom_density,
    geom_rug,
    ggplot,
    labs,
    theme,
    theme_minimal,
)


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Imprint palette: all eight positions in canonical order
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

# Columns: set these to your table's column names
VALUES = "Daily river flow (m³/s)"  # role: values

# Data: replace this block with your own table, for example df = pd.read_csv("flow.csv")
# Daily river flow at a gauge: right-skewed base flow plus a few flood days
rng = np.random.default_rng(7)
base_flow = rng.lognormal(mean=3.0, sigma=0.45, size=190)
flood_flow = rng.uniform(70, 130, size=10)
df = pd.DataFrame({VALUES: np.concatenate([base_flow, flood_flow])})

# Plot
plot = (
    ggplot(df, aes(x=VALUES))
    + geom_density(fill=IMPRINT_PALETTE[0], alpha=0.5, color=IMPRINT_PALETTE[0], size=1.2)
    + geom_rug(alpha=0.5, sides="b", size=0.8, color=IMPRINT_PALETTE[0], length=0.04)
    + labs(y="Density", title="density-rug · python · plotnine · anyplot.ai")
    + theme_minimal()
    + theme(
        figure_size=(8, 4.5),
        plot_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
        panel_background=element_rect(fill=PAGE_BG),
        panel_grid_major=element_line(color=INK, size=0.3, alpha=0.12),
        panel_grid_minor=element_line(color=INK, size=0.2, alpha=0.06),
        panel_border=element_rect(color=INK_SOFT, fill=None, size=0.3),
        axis_title=element_text(size=10, color=INK),
        axis_text=element_text(size=8, color=INK_SOFT),
        axis_line=element_line(color=INK_SOFT, size=0.5),
        plot_title=element_text(size=12, color=INK),
    )
)

# Save
plot.save(f"plot-{THEME}.png", dpi=400, width=8, height=4.5, units="in", verbose=False)
