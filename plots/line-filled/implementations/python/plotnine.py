"""anyplot.ai
line-filled: Filled Line Plot
Library: plotnine 0.15.4 | Python 3.13.13
Quality: pending | Updated: 2026-05-12
"""

import os

import numpy as np
import pandas as pd
from plotnine import (
    aes,
    element_line,
    element_rect,
    element_text,
    geom_area,
    geom_line,
    ggplot,
    labs,
    scale_x_continuous,
    scale_y_continuous,
    theme,
    theme_minimal,
)


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Imprint palette: single series uses the first position
BRAND = "#009E73"

# Columns: set these to your table's column names
MONTH = "Month"  # role: x
VISITORS = "Website Visitors"  # role: y

# Data: replace this block with your own table, for example df = pd.read_csv("traffic.csv")
np.random.seed(42)
months = np.arange(1, 13)
base_traffic = 50000 + np.cumsum(np.random.randn(12) * 5000)
seasonal = 10000 * np.sin(np.pi * months / 6)
visitors = base_traffic + seasonal + np.random.randn(12) * 3000
df = pd.DataFrame({MONTH: months, VISITORS: np.maximum(visitors, 20000)})

# Plot
table = df.copy()
table[MONTH] = table[MONTH].astype(float)
table[VISITORS] = table[VISITORS].astype(float)
table = table.dropna(subset=[VISITORS]).sort_values(MONTH)
plot = (
    ggplot(table, aes(x=MONTH, y=VISITORS))
    + geom_area(fill=BRAND, alpha=0.35)
    + geom_line(color=BRAND, size=1.3)
    + labs(title="line-filled · python · plotnine · anyplot.ai")
    + scale_x_continuous(breaks=table[MONTH].tolist())
    + scale_y_continuous(limits=(0, table[VISITORS].max() * 1.1), expand=(0, 0))
    + theme_minimal()
    + theme(
        figure_size=(8, 4.5),
        plot_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
        panel_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
        panel_grid_major=element_line(color=INK, size=0.3, alpha=0.12),
        panel_grid_minor=element_line(alpha=0),
        panel_border=element_rect(color=INK_SOFT, fill=None),
        axis_title=element_text(size=10, color=INK),
        axis_text=element_text(size=8, color=INK_SOFT),
        axis_line=element_line(color=INK_SOFT, size=0.5),
        plot_title=element_text(size=12, color=INK),
    )
)

# Save
plot.save(f"plot-{THEME}.png", dpi=400, width=8, height=4.5, units="in", verbose=False)
