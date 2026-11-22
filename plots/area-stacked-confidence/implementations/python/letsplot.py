""" anyplot.ai
area-stacked-confidence: Stacked Area Chart with Confidence Bands
Library: letsplot 4.11.0 | Python 3.14.10
Quality: 81/100 | Updated: 2026-11-22
"""

import os

import numpy as np
import pandas as pd
from lets_plot import *  # noqa: F403, F405


LetsPlot.setup_html()

# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
GRID = "rgba(26,26,23,0.15)" if THEME == "light" else "rgba(240,239,232,0.15)"

# Imprint palette: all eight positions, one per series in order
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

# Constants
Y_LABEL = "Energy Consumption (TWh)"  # axis title shared by all series

# Columns: set these to your table's column names
QUARTER = "Quarter"  # role: x
# Series are stacked in VALUE order, the first at the bottom
VALUE = ["Solar", "Wind", "Hydro"]  # role: y
LOWER = ["Solar lower", "Wind lower", "Hydro lower"]  # role: y_lower
UPPER = ["Solar upper", "Wind upper", "Hydro upper"]  # role: y_upper

# Data: replace this block with your own table, for example df = pd.read_csv("energy.csv")
# One row per quarter: each series' own (unstacked) value and its own 90% interval bounds.
np.random.seed(42)
n_quarters = 24
growth = np.linspace(1, 2.5, n_quarters)  # forecast uncertainty widens over time
solar = np.linspace(50, 120, n_quarters) + np.random.normal(0, 5, n_quarters)
wind = np.linspace(80, 150, n_quarters) + np.random.normal(0, 8, n_quarters)
hydro = np.linspace(100, 110, n_quarters) + np.random.normal(0, 3, n_quarters)
columns = {QUARTER: [f"{2023 + i // 4}-Q{i % 4 + 1}" for i in range(n_quarters)]}
for col, lo, hi, base, spread in zip(VALUE, LOWER, UPPER, (solar, wind, hydro), (8, 12, 5), strict=True):
    columns |= {col: base, lo: base - spread * growth, hi: base + spread * growth}
df = pd.DataFrame(columns)

# Plot
quarter_order = list(df[QUARTER])
tick_step = max(1, len(quarter_order) // 6)

# Stack in column order: each layer starts where the one below ends
edge = df[VALUE].cumsum(axis=1)
layers = []
for i, col in enumerate(VALUE):
    layers.append(
        pd.DataFrame(
            {
                "x": np.arange(len(df)),
                "source": col,
                "edge": edge[col],
                "base": edge[col] - df[col],
                "band_lo": edge[col] - (df[col] - df[LOWER[i]]),
                "band_hi": edge[col] + (df[UPPER[i]] - df[col]),
            }
        )
    )
plot_df = pd.concat(layers, ignore_index=True)
sources = list(VALUE)
fills = dict(zip(sources, IMPRINT_PALETTE, strict=False))

anyplot_theme = theme(
    plot_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
    panel_background=element_rect(fill=PAGE_BG),
    panel_grid_major_y=element_line(color=GRID, size=0.3),
    panel_grid_major_x=element_blank(),
    panel_grid_minor=element_blank(),
    axis_title=element_text(color=INK, size=12),
    axis_text=element_text(color=INK_SOFT, size=10),
    axis_line=element_line(color=INK_SOFT, size=0.4),
    plot_title=element_text(color=INK, size=16),
    plot_caption=element_text(color=INK_SOFT, size=10),
    legend_background=element_rect(fill=ELEVATED_BG, color=INK_SOFT),
    legend_text=element_text(color=INK_SOFT, size=10),
    legend_title=element_text(color=INK, size=12),
    legend_position="right",
)

plot = (
    ggplot(plot_df)
    + geom_ribbon(aes(x="x", ymin="band_lo", ymax="band_hi", fill="source"), alpha=0.25, size=0)
    + geom_ribbon(aes(x="x", ymin="base", ymax="edge", fill="source"), alpha=0.7, size=0)
    + geom_line(aes(x="x", y="edge", color="source"), size=1.0)
    + scale_fill_manual(values=[fills[s] for s in sources], breaks=sources, name="Energy Source")
    + scale_color_manual(values=[fills[s] for s in sources], breaks=sources, guide="none")
    + scale_x_continuous(
        breaks=list(range(0, len(quarter_order), tick_step)),
        labels=[quarter_order[i] for i in range(0, len(quarter_order), tick_step)],
    )
    + labs(
        title="area-stacked-confidence · python · letsplot · anyplot.ai",
        x=QUARTER,
        y=Y_LABEL,
        caption="Lighter shaded bands around each stacked edge show the 90% prediction interval of that series",
    )
    + theme_minimal()
    + anyplot_theme
    + ggsize(800, 450)
)

# Save PNG (scale 4x for 3200 x 1800 px) and HTML
ggsave(plot, f"plot-{THEME}.png", path=".", scale=4)
ggsave(plot, f"plot-{THEME}.html", path=".")
