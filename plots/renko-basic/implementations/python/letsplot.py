"""anyplot.ai
renko-basic: Basic Renko Chart
Library: letsplot 4.9.0 | Python 3.13.13
Quality: pending | Updated: 2026-05-17
"""

import os

import numpy as np
import pandas as pd
from lets_plot import (
    LetsPlot,
    aes,
    element_blank,
    element_line,
    element_rect,
    element_text,
    geom_tile,
    ggplot,
    ggsave,
    ggsize,
    labs,
    scale_fill_manual,
    theme,
    theme_minimal,
)


LetsPlot.setup_html()

# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Imprint palette: all eight positions in canonical order
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]
BULLISH = IMPRINT_PALETTE[0]  # green: price rose
BEARISH = IMPRINT_PALETTE[4]  # red: price fell

# Constants
BRICK_SHARE = 0.02  # a brick is about this share of the median close

# Columns: set these to your table's column names
DATE = "Date"  # role: date
CLOSE = "Close price ($)"  # role: close

# Data: replace this block with your own table, for example df = pd.read_csv("prices.csv")
np.random.seed(42)
n_days = 200
df = pd.DataFrame(
    {
        DATE: pd.date_range("2024-01-01", periods=n_days, freq="D"),
        CLOSE: 100 * np.exp(np.cumsum(np.random.normal(0.001, 0.02, n_days))),
    }
)

# Plot: reads only df and the constants above
BRICK = "Brick index"
DIRECTION = "Direction"

closes = df[CLOSE].dropna().to_numpy()
raw_size = np.median(closes) * BRICK_SHARE
magnitude = 10 ** np.floor(np.log10(raw_size))
BRICK_SIZE = round(raw_size / magnitude) * magnitude  # price move that completes one brick, a round number
base = (closes[0] // BRICK_SIZE) * BRICK_SIZE
rows = []
for price in closes:
    while price >= base + BRICK_SIZE:
        rows.append({BRICK: len(rows), "low": base, DIRECTION: "bullish"})
        base += BRICK_SIZE
    while price <= base - BRICK_SIZE:
        base -= BRICK_SIZE
        rows.append({BRICK: len(rows), "low": base, DIRECTION: "bearish"})

bricks = pd.DataFrame(rows)
bricks[CLOSE] = bricks["low"] + BRICK_SIZE / 2  # tile centre
bricks["height"] = BRICK_SIZE

plot = (
    ggplot(bricks, aes(x=BRICK, y=CLOSE, fill=DIRECTION))
    + geom_tile(aes(height="height"), width=0.88, color=PAGE_BG, size=0.6)
    + scale_fill_manual(values={"bullish": BULLISH, "bearish": BEARISH})
    + labs(x=BRICK, y=CLOSE, title="renko-basic · python · letsplot · anyplot.ai")
    + theme_minimal()
    + theme(
        plot_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
        panel_background=element_rect(fill=PAGE_BG),
        panel_grid_major=element_line(color=INK, size=0.15),
        panel_grid_minor=element_blank(),
        axis_title=element_text(size=12, color=INK),
        axis_text=element_text(size=10, color=INK_SOFT),
        axis_line=element_line(color=INK_SOFT),
        plot_title=element_text(size=16, color=INK),
        legend_background=element_rect(fill=PAGE_BG, color=INK_SOFT),
        legend_text=element_text(size=10, color=INK_SOFT),
        legend_title=element_text(size=12, color=INK),
        legend_position="right",
    )
    + ggsize(800, 450)
)

# Save
ggsave(plot, f"plot-{THEME}.png", path=".", scale=4)
ggsave(plot, f"plot-{THEME}.html", path=".")
