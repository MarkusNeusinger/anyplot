""" anyplot.ai
line-styled: Styled Line Plot
Library: plotnine 0.15.4 | Python 3.13.13
Quality: 90/100 | Updated: 2026-05-12
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

IMPRINT = ["#009E73", "#C475FD", "#4467A3", "#BD8233"]

# Data - quarterly product performance over 3 years
np.random.seed(42)
quarters = np.arange(1, 13)
quarter_labels = [f"Q{(i - 1) % 4 + 1} {2022 + (i - 1) // 4}" for i in quarters]

# Generate realistic sales trends for different product lines
base = 100
product_a = base + np.cumsum(np.random.randn(12) * 5 + 3)
product_b = base + np.cumsum(np.random.randn(12) * 4 + 1)
product_c = base + np.cumsum(np.random.randn(12) * 6 - 0.5)
product_d = base + np.cumsum(np.random.randn(12) * 3 + 2)

# Create long-format DataFrame for plotnine
df = pd.DataFrame(
    {
        "Quarter": np.tile(quarters, 4),
        "Sales": np.concatenate([product_a, product_b, product_c, product_d]),
        "Product": ["Product A"] * 12 + ["Product B"] * 12 + ["Product C"] * 12 + ["Product D"] * 12,
    }
)

# Define line styles and colors using Okabe-Ito palette
linetype_values = {"Product A": "solid", "Product B": "dashed", "Product C": "dotted", "Product D": "dashdot"}
color_values = {
    "Product A": IMPRINT[0],
    "Product B": IMPRINT[1],
    "Product C": IMPRINT[2],
    "Product D": IMPRINT[3],
}

# Theme-adaptive styling
anyplot_theme = theme(
    plot_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
    panel_background=element_rect(fill=PAGE_BG),
    panel_grid_major=element_line(color=INK, size=0.3, alpha=0.15),
    panel_grid_minor=element_line(color=INK, size=0.2, alpha=0.08),
    panel_border=element_rect(color=INK_SOFT, fill=None, size=0.5),
    axis_title=element_text(color=INK, size=20),
    axis_text=element_text(color=INK_SOFT, size=16),
    axis_line=element_line(color=INK_SOFT, size=0.4),
    plot_title=element_text(color=INK, size=24, weight="medium"),
    legend_background=element_rect(fill=ELEVATED_BG, color=INK_SOFT, size=0.4),
    legend_text=element_text(color=INK_SOFT, size=16),
    legend_title=element_text(color=INK, size=18),
    figure_size=(16, 9),
)

# Create plot
plot = (
    ggplot(df, aes(x="Quarter", y="Sales", color="Product", linetype="Product"))
    + geom_line(size=1.8)
    + scale_x_continuous(breaks=quarters, labels=quarter_labels, limits=(0.5, 12.5))
    + scale_linetype_manual(values=linetype_values)
    + scale_color_manual(values=color_values)
    + labs(
        title="line-styled · plotnine · anyplot.ai",
        x="Quarter",
        y="Sales (thousands USD)",
        color="Product Line",
        linetype="Product Line",
    )
    + theme_minimal()
    + anyplot_theme
)

# Save
plot.save(f"plot-{THEME}.png", dpi=300)
