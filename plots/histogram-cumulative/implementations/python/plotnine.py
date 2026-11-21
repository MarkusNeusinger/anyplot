""" anyplot.ai
histogram-cumulative: Cumulative Histogram
Library: plotnine 0.15.9 | Python 3.14.10
Quality: 84/100 | Updated: 2026-11-21
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
    geom_bar,
    geom_vline,
    ggplot,
    ggsave,
    labs,
    scale_y_continuous,
    theme,
    theme_minimal,
)


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Imprint palette: first series is always #009E73
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

# Constants
N_BINS = 25  # number of histogram bins
QUARTILES = (0.25, 0.50, 0.75)  # cumulative shares marked with reference lines

# Columns: set these to your table's column names
SHELF_LIFE = "Shelf Life (days)"  # role: numeric

# Data: replace this block with your own table, for example df = pd.read_csv("shelf_life.csv")
np.random.seed(42)
df = pd.DataFrame({SHELF_LIFE: np.concatenate([np.random.normal(45, 8, 300), np.random.normal(65, 5, 150)])})

# Plot: reads only df and the constants above
CUMULATIVE = "Cumulative Count"
BIN_CENTER = "bin_center"

counts, bin_edges = np.histogram(df[SHELF_LIFE].dropna(), bins=N_BINS)
cumulative_counts = np.cumsum(counts)
bin_centers = (bin_edges[:-1] + bin_edges[1:]) / 2
bin_width = bin_edges[1] - bin_edges[0]
total = int(cumulative_counts[-1])

df_hist = pd.DataFrame({BIN_CENTER: bin_centers, CUMULATIVE: cumulative_counts})

# Quartile positions: first bin whose running total reaches each share
quartile_x = [bin_centers[min(np.searchsorted(cumulative_counts, total * q), len(bin_centers) - 1)] for q in QUARTILES]

# Y ticks: round steps up to the total, which marks the full sample size
step = 10 ** int(np.floor(np.log10(total)))
y_breaks = [*np.arange(0, total, step), total]

anyplot_theme = theme(
    plot_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
    panel_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
    panel_grid_major=element_line(color=INK, size=0.25, alpha=0.08),
    panel_grid_minor=element_blank(),
    panel_border=element_blank(),
    axis_title=element_text(color=INK, size=10),
    axis_text=element_text(color=INK_SOFT, size=8),
    axis_line=element_line(color=INK_SOFT, size=0.3),
    axis_ticks=element_line(color=INK_SOFT, size=0.3),
    plot_title=element_text(color=INK, size=12),
    plot_subtitle=element_text(color=INK_SOFT, size=9),
    figure_size=(8, 4.5),
)

plot = (
    ggplot(df_hist, aes(x=BIN_CENTER, y=CUMULATIVE))
    + geom_bar(stat="identity", width=bin_width * 0.95, fill=IMPRINT_PALETTE[0], color=INK_SOFT, alpha=0.85, size=0.2)
    + geom_vline(xintercept=quartile_x[0], linetype="dashed", color=INK_SOFT, size=0.3, alpha=0.5)
    + geom_vline(xintercept=quartile_x[1], linetype="dashed", color=INK_SOFT, size=0.4, alpha=0.7)
    + geom_vline(xintercept=quartile_x[2], linetype="dashed", color=INK_SOFT, size=0.3, alpha=0.5)
    + labs(
        x=SHELF_LIFE,
        y=CUMULATIVE,
        title="histogram-cumulative · python · plotnine · anyplot.ai",
        subtitle="Dashed lines mark the quartile positions",
    )
    + scale_y_continuous(breaks=y_breaks, limits=(0, total * 1.04))
    + theme_minimal()
    + anyplot_theme
)

# Save
script_dir = os.path.dirname(os.path.abspath(__file__))
ggsave(plot, filename=os.path.join(script_dir, f"plot-{THEME}.png"), dpi=400, width=8, height=4.5, verbose=False)
