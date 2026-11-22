"""anyplot.ai
waffle-basic: Basic Waffle Chart
Library: plotnine 0.15.4 | Python 3.13.13
Quality: 79/100 | Created: 2026-05-05
"""

import os

import numpy as np
import pandas as pd
from plotnine import (
    aes,
    coord_equal,
    element_blank,
    element_rect,
    element_text,
    geom_tile,
    ggplot,
    guide_legend,
    guides,
    labs,
    scale_fill_manual,
    theme,
    theme_minimal,
)


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Imprint palette: all eight positions, one per category in order
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

# Constants
GRID_SIZE = 10  # standard 10x10 grid, one square per percent

# Columns: set these to your table's column names
CATEGORY = "Category"  # role: category
VALUE = "Share of budget (%)"  # role: value

# Data: replace this block with your own table, for example df = pd.read_csv("budget.csv")
df = pd.DataFrame({CATEGORY: ["Housing", "Food", "Transport", "Entertainment"], VALUE: [38, 27, 20, 15]})

# Plot: reads only df and the constants above
totals = df.groupby(CATEGORY, sort=False)[VALUE].sum(min_count=1).dropna()
categories = totals.index.tolist()
n_squares = GRID_SIZE * GRID_SIZE

# Whole squares per category: largest-remainder rounding so the grid is exactly filled
exact = totals.to_numpy(dtype=float) / totals.sum() * n_squares
counts = np.floor(exact).astype(int)
extra = n_squares - counts.sum()
counts[np.argsort(-(exact - counts), kind="stable")[:extra]] += 1

# Fill row by row from the top left, one contiguous block per category
labels = np.repeat(categories, counts)
position = np.arange(n_squares)
waffle = pd.DataFrame(
    {
        "x": position % GRID_SIZE,
        "y": GRID_SIZE - 1 - position // GRID_SIZE,
        CATEGORY: pd.Categorical(labels, categories),
    }
)

color_map = {cat: IMPRINT_PALETTE[i] for i, cat in enumerate(categories)}
legend_labels = {cat: f"{cat} ({share:g}%)" for cat, share in zip(categories, 100 * totals / totals.sum(), strict=True)}

anyplot_theme = theme(
    figure_size=(8, 4.5),
    plot_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
    panel_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
    plot_title=element_text(size=12, color=INK, ha="center"),
    legend_background=element_rect(fill=ELEVATED_BG, color=INK_SOFT),
    legend_title=element_text(size=10, color=INK),
    legend_text=element_text(size=9, color=INK_SOFT),
    legend_position="right",
    axis_text=element_blank(),
    axis_title=element_blank(),
    axis_ticks=element_blank(),
    panel_grid=element_blank(),
)

plot = (
    ggplot(waffle, aes(x="x", y="y", fill=CATEGORY))
    + geom_tile(color=PAGE_BG, size=0.8)
    + scale_fill_manual(values=color_map, limits=categories, labels=[legend_labels[c] for c in categories])
    + coord_equal()
    + labs(title="waffle-basic · python · plotnine · anyplot.ai", fill=CATEGORY)
    + guides(fill=guide_legend(ncol=1))
    + theme_minimal()
    + anyplot_theme
)

plot.save(f"plot-{THEME}.png", dpi=400, width=8, height=4.5, units="in", verbose=False)
