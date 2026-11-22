"""anyplot.ai
renko-basic: Basic Renko Chart
Library: plotnine 0.15.4 | Python 3.13.13
Quality: 85/100 | Updated: 2026-05-17
"""

import os

import numpy as np
import pandas as pd
from plotnine import (
    aes,
    element_line,
    element_rect,
    element_text,
    geom_rect,
    ggplot,
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

# Imprint palette: bullish = position 1, bearish = red from the palette
BULLISH = "#009E73"
BEARISH = "#AE3030"

# Constants
BRICK_FRACTION = 0.02  # brick size as a share of the mean price, rounded to $0.5

# Columns
DATE = "date"  # role: date
CLOSE = "close"  # role: close

# Data
np.random.seed(42)
n_days = 250
returns = np.random.normal(0.0005, 0.018, n_days)
df = pd.DataFrame({DATE: pd.date_range("2024-01-01", periods=n_days, freq="D"), CLOSE: 100 * np.cumprod(1 + returns)})

# Plot
# Renko brick calculation (derived from df)
XMIN, XMAX, BOTTOM, TOP, DIRECTION = "xmin", "xmax", "bottom", "top", "direction"
brick_size = max(round(df[CLOSE].mean() * BRICK_FRACTION * 2) / 2, 0.5)
bricks = []
brick_start = (df[CLOSE].iloc[0] // brick_size) * brick_size
direction = None  # None initially, then 'up' or 'down'

for close_price in df[CLOSE].dropna():
    while True:
        if direction is None:
            # First brick - determine initial direction
            if close_price >= brick_start + brick_size:
                bricks.append({BOTTOM: brick_start, TOP: brick_start + brick_size, DIRECTION: "up"})
                brick_start += brick_size
                direction = "up"
            elif close_price <= brick_start - brick_size:
                bricks.append({BOTTOM: brick_start - brick_size, TOP: brick_start, DIRECTION: "down"})
                brick_start -= brick_size
                direction = "down"
            else:
                break
        elif direction == "up":
            if close_price >= brick_start + brick_size:
                bricks.append({BOTTOM: brick_start, TOP: brick_start + brick_size, DIRECTION: "up"})
                brick_start += brick_size
            elif close_price <= brick_start - 2 * brick_size:
                # Reversal requires 2x brick size
                brick_start -= brick_size
                bricks.append({BOTTOM: brick_start - brick_size, TOP: brick_start, DIRECTION: "down"})
                brick_start -= brick_size
                direction = "down"
            else:
                break
        else:  # direction == 'down'
            if close_price <= brick_start - brick_size:
                bricks.append({BOTTOM: brick_start - brick_size, TOP: brick_start, DIRECTION: "down"})
                brick_start -= brick_size
            elif close_price >= brick_start + 2 * brick_size:
                # Reversal requires 2x brick size
                brick_start += brick_size
                bricks.append({BOTTOM: brick_start, TOP: brick_start + brick_size, DIRECTION: "up"})
                brick_start += brick_size
                direction = "up"
            else:
                break

# One column per brick, with a small gap between neighbours
brick_df = pd.DataFrame(bricks)
brick_df[XMIN] = np.arange(len(brick_df)) + 0.1
brick_df[XMAX] = np.arange(len(brick_df)) + 0.9

plot = (
    ggplot(brick_df, aes(xmin=XMIN, xmax=XMAX, ymin=BOTTOM, ymax=TOP, fill=DIRECTION))
    + geom_rect(color=INK_SOFT, size=0.3)
    + scale_fill_manual(
        values={"up": BULLISH, "down": BEARISH},
        limits=brick_df[DIRECTION].unique().tolist(),
        labels={"up": "Bullish", "down": "Bearish"},
    )
    + labs(x="Brick Index", y="Price ($)", title="renko-basic · python · plotnine · anyplot.ai", fill="Direction")
    + theme_minimal()
    + theme(
        figure_size=(8, 4.5),
        text=element_text(size=7, color=INK),
        axis_title=element_text(size=10, color=INK),
        axis_text=element_text(size=8, color=INK_SOFT),
        plot_title=element_text(size=12, color=INK),
        legend_text=element_text(size=8, color=INK_SOFT),
        legend_title=element_text(size=9, color=INK),
        plot_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
        panel_background=element_rect(fill=PAGE_BG),
        panel_grid_major=element_line(color=INK, size=0.3, alpha=0.15),
        panel_grid_minor=element_line(color=INK, size=0.2, alpha=0.08),
        panel_border=element_rect(color=INK_SOFT, fill=None, size=0.3),
        legend_background=element_rect(fill=ELEVATED_BG, color=INK_SOFT),
        axis_line=element_line(color=INK_SOFT, size=0.3),
    )
)

plot.save(f"plot-{THEME}.png", dpi=400, width=8, height=4.5, units="in")
