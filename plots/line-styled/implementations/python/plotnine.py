"""anyplot.ai
line-styled: Styled Line Plot
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
    geom_line,
    ggplot,
    labs,
    scale_color_manual,
    scale_linetype_manual,
    scale_x_continuous,
    theme,
    theme_minimal,
)


THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Imprint palette
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]
LINE_STYLES = ["solid", "dashed", "dotted", "dashdot"]

# Constants
LINE_WIDTH = 1.3

# Columns
QUARTER = "Quarter"  # role: x
SERIES = ["Product A", "Product B", "Product C", "Product D"]  # role: y_
SALES = "Sales (thousands USD)"
PRODUCT_LINE = "Product Line"

# Data
np.random.seed(42)
n_quarters = 12
base = 100
steps = [(5, 3), (4, 1), (6, -0.5), (3, 2)]
series = {
    name: base + np.cumsum(np.random.randn(n_quarters) * spread + drift)
    for name, (spread, drift) in zip(SERIES, steps, strict=True)
}
df = pd.DataFrame({QUARTER: np.arange(1, n_quarters + 1), **series})

# Plot
long_df = df.melt(id_vars=QUARTER, value_vars=SERIES, var_name=PRODUCT_LINE, value_name=SALES)
quarters = sorted(df[QUARTER].dropna().unique())
quarter_labels = [f"Q{int(q - 1) % 4 + 1} {2022 + int(q - 1) // 4}" for q in quarters]

anyplot_theme = theme(
    plot_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
    panel_background=element_rect(fill=PAGE_BG),
    panel_grid_major=element_line(color=INK, size=0.3, alpha=0.15),
    panel_grid_minor=element_line(color=INK, size=0.2, alpha=0.05),
    axis_title=element_text(color=INK, size=10),
    axis_text=element_text(color=INK_SOFT, size=8),
    axis_text_x=element_text(color=INK_SOFT, size=8, angle=30, ha="right"),
    axis_line=element_line(color=INK_SOFT),
    plot_title=element_text(color=INK, size=12),
    legend_background=element_rect(fill=ELEVATED_BG, color="none"),
    legend_key=element_rect(fill=ELEVATED_BG, color="none"),
    legend_key_width=45,
    legend_text=element_text(color=INK_SOFT, size=8),
    legend_title=element_text(color=INK, size=9),
    figure_size=(8, 4.5),
)

plot = (
    ggplot(long_df, aes(x=QUARTER, y=SALES, color=PRODUCT_LINE, linetype=PRODUCT_LINE))
    + geom_line(size=LINE_WIDTH)
    + scale_x_continuous(breaks=quarters, labels=quarter_labels)
    + scale_linetype_manual(values=[LINE_STYLES[i % len(LINE_STYLES)] for i in range(len(SERIES))], limits=SERIES)
    + scale_color_manual(values=IMPRINT_PALETTE, limits=SERIES)
    + labs(title="line-styled · python · plotnine · anyplot.ai", x=QUARTER)
    + theme_minimal()
    + anyplot_theme
)

# Save
plot.save(f"plot-{THEME}.png", dpi=400, width=8, height=4.5, units="in")
