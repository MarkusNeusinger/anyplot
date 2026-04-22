""" pyplots.ai
kagi-basic: Basic Kagi Chart
Library: letsplot 4.8.2 | Python 3.13.11
Quality: 91/100 | Created: 2026-01-08
"""

import numpy as np
import pandas as pd
from lets_plot import (
    LetsPlot,
    aes,
    element_blank,
    element_text,
    geom_segment,
    ggplot,
    ggsize,
    labs,
    theme,
    theme_minimal,
)
from lets_plot.export import ggsave


LetsPlot.setup_html()

# Generate synthetic stock price data
np.random.seed(42)
n_days = 200
returns = np.random.normal(0.001, 0.02, n_days)
prices = 100 * np.cumprod(1 + returns)

# Kagi chart parameters
reversal_threshold = 0.04  # 4% reversal threshold

# Build Kagi chart segments from price data
segments = []
direction = 1  # 1 = up, -1 = down
last_high = prices[0]
last_low = prices[0]
current_price = prices[0]
x_idx = 0

for price in prices[1:]:
    if direction == 1:  # Currently in uptrend
        if price > last_high:
            last_high = price
            current_price = price
        elif price <= current_price * (1 - reversal_threshold):
            # Add vertical yang (thick) line
            segments.append({"x1": x_idx, "y1": last_low, "x2": x_idx, "y2": last_high, "line_type": "yang"})
            x_idx += 1
            # Add horizontal shoulder
            segments.append({"x1": x_idx - 1, "y1": last_high, "x2": x_idx, "y2": last_high, "line_type": "yang"})
            # Change direction
            direction = -1
            last_low = price
            current_price = price
    else:  # Currently in downtrend
        if price < last_low:
            last_low = price
            current_price = price
        elif price >= current_price * (1 + reversal_threshold):
            # Add vertical yin (thin) line
            segments.append({"x1": x_idx, "y1": last_high, "x2": x_idx, "y2": last_low, "line_type": "yin"})
            x_idx += 1
            # Add horizontal waist
            segments.append({"x1": x_idx - 1, "y1": last_low, "x2": x_idx, "y2": last_low, "line_type": "yin"})
            # Change direction
            direction = 1
            last_high = price
            current_price = price

# Add final segment
if direction == 1:
    segments.append({"x1": x_idx, "y1": last_low, "x2": x_idx, "y2": current_price, "line_type": "yang"})
else:
    segments.append({"x1": x_idx, "y1": last_high, "x2": x_idx, "y2": current_price, "line_type": "yin"})

# Create dataframe and separate by line type
kagi_df = pd.DataFrame(segments)
yang_df = kagi_df[kagi_df["line_type"] == "yang"].copy()
yin_df = kagi_df[kagi_df["line_type"] == "yin"].copy()

# Create the plot
plot = (
    ggplot()
    + geom_segment(
        aes(x="x1", y="y1", xend="x2", yend="y2"),
        data=yang_df,
        color="#16A34A",  # Green for yang (bullish)
        size=4,  # Thick line for yang
    )
    + geom_segment(
        aes(x="x1", y="y1", xend="x2", yend="y2"),
        data=yin_df,
        color="#DC2626",  # Red for yin (bearish)
        size=1.5,  # Thin line for yin
    )
    + labs(title="kagi-basic · letsplot · pyplots.ai", x="Line Index", y="Price ($)")
    + theme_minimal()
    + theme(
        plot_title=element_text(size=24),
        axis_title=element_text(size=20),
        axis_text=element_text(size=16),
        panel_grid_minor=element_blank(),
    )
    + ggsize(1600, 900)
)

# Save as PNG (scaled 3x for 4800x2700 px)
ggsave(plot, "plot.png", path=".", scale=3)

# Save as HTML for interactive viewing
ggsave(plot, "plot.html", path=".")
