""" anyplot.ai
renko-basic: Basic Renko Chart
Library: letsplot 4.9.0 | Python 3.13.13
Quality: 92/100 | Updated: 2026-05-17
"""

import os

import numpy as np
import pandas as pd
from lets_plot import *  # noqa: F403
from lets_plot import element_blank, element_line, element_rect, element_text, theme  # noqa: F401
from lets_plot.export import ggsave


LetsPlot.setup_html()  # noqa: F405

# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
RULE = "rgba(26,26,23,0.10)" if THEME == "light" else "rgba(240,239,232,0.10)"

# Okabe-Ito palette (bullish: position 1, bearish: position 2 for better accessibility)
BULLISH = "#009E73"  # Okabe-Ito position 1
BEARISH = "#AE3030"  # imprint red — bearish

# Generate synthetic stock price data
np.random.seed(42)
n_days = 200
dates = pd.date_range("2024-01-01", periods=n_days, freq="D")
returns = np.random.normal(0.001, 0.02, n_days)
prices = 100 * np.exp(np.cumsum(returns))

# Renko brick calculation
brick_size = 2.0  # $2 brick size
renko_bricks = []
current_price = prices[0]
brick_base = (current_price // brick_size) * brick_size
direction = None

for price in prices:
    while price >= brick_base + brick_size:
        new_base = brick_base + brick_size
        renko_bricks.append(
            {"brick_index": len(renko_bricks), "open": brick_base, "close": new_base, "direction": "bullish"}
        )
        brick_base = new_base
        direction = "bullish"

    while price <= brick_base - brick_size:
        new_base = brick_base - brick_size
        renko_bricks.append(
            {"brick_index": len(renko_bricks), "open": brick_base, "close": new_base, "direction": "bearish"}
        )
        brick_base = new_base
        direction = "bearish"

# Create DataFrame for plotting
df_renko = pd.DataFrame(renko_bricks)

# Calculate brick positions for visualization
df_renko["x"] = df_renko["brick_index"]
df_renko["y_min"] = df_renko[["open", "close"]].min(axis=1)
df_renko["y_max"] = df_renko[["open", "close"]].max(axis=1)
df_renko["y_center"] = (df_renko["y_min"] + df_renko["y_max"]) / 2
df_renko["height"] = brick_size

# Create Renko chart
plot = (
    ggplot(df_renko, aes(x="x", y="y_center", fill="direction"))  # noqa: F405
    + geom_tile(aes(height="height"), width=0.85, color="white", size=0.5)  # noqa: F405
    + scale_fill_manual(  # noqa: F405
        values={"bullish": BULLISH, "bearish": BEARISH}, name="Direction"
    )
    + labs(x="Brick Index", y="Price ($)", title="renko-basic · letsplot · anyplot.ai")  # noqa: F405
    + theme_minimal()  # noqa: F405
    + theme(  # noqa: F405
        plot_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
        panel_background=element_rect(fill=PAGE_BG),
        panel_grid_major=element_line(color=INK, size=0.2),
        panel_grid_minor=element_blank(),
        axis_title=element_text(size=20, color=INK),
        axis_text=element_text(size=16, color=INK_SOFT),
        axis_line=element_line(color=INK_SOFT),
        plot_title=element_text(size=24, color=INK),
        legend_background=element_rect(fill=PAGE_BG, color=INK_SOFT),
        legend_text=element_text(size=16, color=INK_SOFT),
        legend_title=element_text(size=18, color=INK),
        legend_position="right",
    )
    + ggsize(1600, 900)  # noqa: F405
)

# Save as PNG (scale 3x for 4800 × 2700 px)
ggsave(plot, f"plot-{THEME}.png", path=".", scale=3)

# Save as HTML for interactive viewing
ggsave(plot, f"plot-{THEME}.html", path=".")
