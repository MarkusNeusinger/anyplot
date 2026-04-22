""" pyplots.ai
renko-basic: Basic Renko Chart
Library: letsplot 4.8.2 | Python 3.13.11
Quality: 92/100 | Created: 2026-01-09
"""

import numpy as np
import pandas as pd
from lets_plot import *  # noqa: F403
from lets_plot.export import ggsave as export_ggsave


LetsPlot.setup_html()  # noqa: F405

# Generate synthetic stock price data
np.random.seed(42)
n_days = 200
dates = pd.date_range("2024-01-01", periods=n_days, freq="D")
# Create realistic price movement with trend and volatility
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
        # Bullish brick
        new_base = brick_base + brick_size
        renko_bricks.append(
            {"brick_index": len(renko_bricks), "open": brick_base, "close": new_base, "direction": "bullish"}
        )
        brick_base = new_base
        direction = "bullish"

    while price <= brick_base - brick_size:
        # Bearish brick
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

# Create Renko chart using geom_tile for bricks
plot = (
    ggplot(df_renko, aes(x="x", y="y_center", fill="direction"))  # noqa: F405
    + geom_tile(aes(height="height"), width=0.85, color="white", size=0.5)  # noqa: F405
    + scale_fill_manual(values={"bullish": "#22C55E", "bearish": "#DC2626"}, name="Direction")  # noqa: F405
    + labs(x="Brick Index", y="Price ($)", title="renko-basic · letsplot · pyplots.ai")  # noqa: F405
    + theme_minimal()  # noqa: F405
    + theme(  # noqa: F405
        plot_title=element_text(size=24, face="bold"),  # noqa: F405
        axis_title=element_text(size=20),  # noqa: F405
        axis_text=element_text(size=16),  # noqa: F405
        legend_title=element_text(size=18),  # noqa: F405
        legend_text=element_text(size=16),  # noqa: F405
        legend_position="right",
        panel_grid_major=element_line(color="#E5E5E5", size=0.5),  # noqa: F405
        panel_grid_minor=element_blank(),  # noqa: F405
    )
    + ggsize(1600, 900)  # noqa: F405
)

# Save as PNG (scale 3x for 4800 × 2700 px)
export_ggsave(plot, "plot.png", path=".", scale=3)

# Save as HTML for interactive viewing
export_ggsave(plot, "plot.html", path=".")
