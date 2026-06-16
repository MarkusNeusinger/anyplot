""" anyplot.ai
renko-basic: Basic Renko Chart
Library: plotnine 0.15.4 | Python 3.13.13
Quality: 85/100 | Updated: 2026-05-17
"""

import os
import sys

import numpy as np
import pandas as pd


# Work around naming collision with plotnine.py
sys.path.pop(0)

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

# imprint semantic anchors for direction
BULLISH = "#009E73"  # green - up bricks
BEARISH = "#AE3030"  # red - down bricks

# Data - Generate stock price data
np.random.seed(42)
n_days = 250
dates = pd.date_range("2024-01-01", periods=n_days, freq="D")
returns = np.random.normal(0.0005, 0.018, n_days)
prices = 100 * np.cumprod(1 + returns)
price_data = pd.DataFrame({"date": dates, "close": prices})

# Renko brick calculation
brick_size = 2.0  # $2 brick size
bricks = []
current_price = price_data["close"].iloc[0]
brick_start = (current_price // brick_size) * brick_size
direction = None  # None initially, then 'up' or 'down'

for close_price in price_data["close"]:
    while True:
        if direction is None:
            # First brick - determine initial direction
            if close_price >= brick_start + brick_size:
                bricks.append(
                    {
                        "brick_num": len(bricks),
                        "bottom": brick_start,
                        "top": brick_start + brick_size,
                        "direction": "up",
                    }
                )
                brick_start += brick_size
                direction = "up"
            elif close_price <= brick_start - brick_size:
                bricks.append(
                    {
                        "brick_num": len(bricks),
                        "bottom": brick_start - brick_size,
                        "top": brick_start,
                        "direction": "down",
                    }
                )
                brick_start -= brick_size
                direction = "down"
            else:
                break
        elif direction == "up":
            if close_price >= brick_start + brick_size:
                bricks.append(
                    {
                        "brick_num": len(bricks),
                        "bottom": brick_start,
                        "top": brick_start + brick_size,
                        "direction": "up",
                    }
                )
                brick_start += brick_size
            elif close_price <= brick_start - 2 * brick_size:
                # Reversal requires 2x brick size
                brick_start -= brick_size
                bricks.append(
                    {
                        "brick_num": len(bricks),
                        "bottom": brick_start - brick_size,
                        "top": brick_start,
                        "direction": "down",
                    }
                )
                brick_start -= brick_size
                direction = "down"
            else:
                break
        else:  # direction == 'down'
            if close_price <= brick_start - brick_size:
                bricks.append(
                    {
                        "brick_num": len(bricks),
                        "bottom": brick_start - brick_size,
                        "top": brick_start,
                        "direction": "down",
                    }
                )
                brick_start -= brick_size
            elif close_price >= brick_start + 2 * brick_size:
                # Reversal requires 2x brick size
                brick_start += brick_size
                bricks.append(
                    {
                        "brick_num": len(bricks),
                        "bottom": brick_start,
                        "top": brick_start + brick_size,
                        "direction": "up",
                    }
                )
                brick_start += brick_size
                direction = "up"
            else:
                break

brick_df = pd.DataFrame(bricks)

# Create rectangle coordinates for geom_rect
brick_df["xmin"] = brick_df["brick_num"] + 0.1
brick_df["xmax"] = brick_df["brick_num"] + 0.9
brick_df["ymin"] = brick_df["bottom"]
brick_df["ymax"] = brick_df["top"]

# Plot
plot = (
    ggplot(brick_df, aes(xmin="xmin", xmax="xmax", ymin="ymin", ymax="ymax", fill="direction"))
    + geom_rect(color=INK_SOFT, size=0.3)
    + scale_fill_manual(values={"up": BULLISH, "down": BEARISH}, labels={"up": "Bullish", "down": "Bearish"})
    + labs(x="Brick Index", y="Price ($)", title="renko-basic · plotnine · anyplot.ai", fill="Direction")
    + theme_minimal()
    + theme(
        figure_size=(16, 9),
        text=element_text(size=14, color=INK),
        axis_title=element_text(size=20, color=INK),
        axis_text=element_text(size=16, color=INK_SOFT),
        plot_title=element_text(size=24, color=INK),
        legend_text=element_text(size=16, color=INK_SOFT),
        legend_title=element_text(size=18, color=INK),
        plot_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
        panel_background=element_rect(fill=PAGE_BG),
        panel_grid_major=element_line(color=INK, size=0.5, alpha=0.15),
        panel_grid_minor=element_line(color=INK, size=0.3, alpha=0.08),
        panel_border=element_rect(color=INK_SOFT, fill=None, size=0.3),
        legend_background=element_rect(fill=ELEVATED_BG, color=INK_SOFT),
        axis_line=element_line(color=INK_SOFT, size=0.3),
    )
)

plot.save(f"plot-{THEME}.png", dpi=300, width=16, height=9)
