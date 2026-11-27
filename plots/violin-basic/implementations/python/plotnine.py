"""anyplot.ai
violin-basic: Basic Violin Plot
Library: plotnine 0.15.4 | Python 3.13.13
Quality: pending | Updated: 2026-05-29
"""

import os

import numpy as np
import pandas as pd
from plotnine import (
    aes,
    element_blank,
    element_line,
    element_rect,
    element_text,
    geom_violin,
    ggplot,
    labs,
    scale_fill_manual,
    scale_x_discrete,
    theme,
    theme_minimal,
)


# Theme tokens (Imprint palette — theme-adaptive chrome)
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Imprint palette, canonical order
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

# Columns: set these to your table's column names
TIER = "Server tier"  # role: category
LATENCY = "Response latency (ms)"  # role: value

# Data: replace this block with your own table, for example df = pd.read_csv("latency.csv")
rng = np.random.default_rng(42)
df = pd.concat(
    [
        # Edge cache: fast, right-skewed with a long tail of slow misses
        pd.DataFrame({TIER: "Edge cache", LATENCY: rng.lognormal(np.log(18), 0.45, 300)}),
        # API gateway: bimodal, cache hits versus full computations
        pd.DataFrame(
            {TIER: "API gateway", LATENCY: np.concatenate([rng.normal(60, 8, 160), rng.normal(130, 14, 140)])}
        ),
        # Database: tight, near-normal query times
        pd.DataFrame({TIER: "Database", LATENCY: rng.normal(95, 9, 300)}),
        # Batch worker: wide spread from variable job sizes
        pd.DataFrame({TIER: "Batch worker", LATENCY: rng.normal(150, 38, 300).clip(40)}),
    ],
    ignore_index=True,
)

# Plot: reads only df and the constants above
tiers = df[TIER].unique().tolist()
title = "violin-basic · python · plotnine · anyplot.ai"

plot = (
    ggplot(df, aes(x=TIER, y=LATENCY, fill=TIER))
    + geom_violin(draw_quantiles=[0.25, 0.5, 0.75], alpha=0.85, color=INK, size=0.6)
    + scale_x_discrete(limits=tiers)
    + scale_fill_manual(values=IMPRINT_PALETTE, limits=tiers)
    + labs(title=title)
    + theme_minimal()
    + theme(
        figure_size=(8, 4.5),
        text=element_text(size=9, color=INK),
        axis_title=element_text(size=10, color=INK),
        axis_text=element_text(size=8, color=INK_SOFT),
        plot_title=element_text(size=12, color=INK),
        legend_position="none",
        panel_grid_major_x=element_blank(),
        panel_grid_minor=element_blank(),
        panel_grid_major_y=element_line(color=INK, size=0.3, alpha=0.15),
        axis_line=element_line(color=INK_SOFT),
        panel_border=element_blank(),
        plot_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
        panel_background=element_rect(fill=PAGE_BG),
    )
)

# Save
plot.save(f"plot-{THEME}.png", dpi=400, width=8, height=4.5, units="in", verbose=False)
