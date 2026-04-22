""" pyplots.ai
kagi-basic: Basic Kagi Chart
Library: plotnine 0.15.2 | Python 3.13.11
Quality: 91/100 | Created: 2026-01-08
"""

import numpy as np
import pandas as pd
from plotnine import (
    aes,
    element_blank,
    element_text,
    geom_segment,
    ggplot,
    labs,
    scale_color_manual,
    scale_size_manual,
    theme,
    theme_minimal,
)


# Generate synthetic stock price data
np.random.seed(42)
n_days = 250

# Create random walk with trend
returns = np.random.normal(0.0005, 0.02, n_days)
prices = 100 * np.exp(np.cumsum(returns))
dates = pd.date_range("2024-01-01", periods=n_days, freq="B")

df_prices = pd.DataFrame({"date": dates, "close": prices})


# Kagi chart algorithm with reversal threshold
def build_kagi_data(prices, reversal_pct=0.04):
    """Build Kagi chart segments from price series."""
    kagi_segments = []

    if len(prices) < 2:
        return pd.DataFrame()

    # Initialize
    direction = 1 if prices[1] > prices[0] else -1
    high = prices[0]
    low = prices[0]
    x_idx = 0
    segment_start_price = prices[0]

    # Track yang/yin state (thick/thin)
    is_yang = direction == 1  # Start based on initial direction

    for i in range(1, len(prices)):
        price = prices[i]

        if direction == 1:  # Currently trending up
            if price > high:
                high = price
                # Check if we exceeded previous high (switch to yang)
                is_yang = True
            elif price < high * (1 - reversal_pct):
                # Reversal down - add vertical segment
                kagi_segments.append(
                    {
                        "x": x_idx,
                        "x_end": x_idx,
                        "y": segment_start_price,
                        "y_end": high,
                        "trend": "yang" if is_yang else "yin",
                    }
                )
                # Add horizontal shoulder
                kagi_segments.append(
                    {"x": x_idx, "x_end": x_idx + 1, "y": high, "y_end": high, "trend": "yang" if is_yang else "yin"}
                )
                x_idx += 1
                direction = -1
                segment_start_price = high
                low = price
                high = price

        else:  # Currently trending down
            if price < low:
                low = price
                # Check if we fell below previous low (switch to yin)
                is_yang = False
            elif price > low * (1 + reversal_pct):
                # Reversal up - add vertical segment
                kagi_segments.append(
                    {
                        "x": x_idx,
                        "x_end": x_idx,
                        "y": segment_start_price,
                        "y_end": low,
                        "trend": "yin" if not is_yang else "yang",
                    }
                )
                # Add horizontal waist
                kagi_segments.append(
                    {"x": x_idx, "x_end": x_idx + 1, "y": low, "y_end": low, "trend": "yin" if not is_yang else "yang"}
                )
                x_idx += 1
                direction = 1
                segment_start_price = low
                high = price
                low = price

    # Add final segment
    final_price = prices[-1]
    final_trend = "yang" if is_yang else "yin"
    if direction == 1:
        kagi_segments.append(
            {
                "x": x_idx,
                "x_end": x_idx,
                "y": segment_start_price,
                "y_end": max(high, final_price),
                "trend": final_trend,
            }
        )
    else:
        kagi_segments.append(
            {"x": x_idx, "x_end": x_idx, "y": segment_start_price, "y_end": min(low, final_price), "trend": final_trend}
        )

    return pd.DataFrame(kagi_segments)


# Build Kagi data with 4% reversal threshold
kagi_df = build_kagi_data(df_prices["close"].values, reversal_pct=0.04)

# Create the plot
plot = (
    ggplot(kagi_df, aes(x="x", xend="x_end", y="y", yend="y_end", color="trend", size="trend"))
    + geom_segment()
    + scale_color_manual(
        values={"yang": "#2E7D32", "yin": "#C62828"}, labels={"yang": "Yang (Bullish)", "yin": "Yin (Bearish)"}
    )
    + scale_size_manual(values={"yang": 3.5, "yin": 1.0}, labels={"yang": "Yang (Bullish)", "yin": "Yin (Bearish)"})
    + labs(x="Kagi Line Index", y="Price ($)", title="kagi-basic · plotnine · pyplots.ai", color="Trend", size="Trend")
    + theme_minimal()
    + theme(
        figure_size=(16, 9),
        text=element_text(size=14),
        axis_title=element_text(size=20),
        axis_text=element_text(size=16),
        plot_title=element_text(size=24),
        legend_text=element_text(size=16),
        legend_title=element_text(size=18),
        legend_position="right",
        panel_grid_minor=element_blank(),
    )
)

# Save the plot
plot.save("plot.png", dpi=300, verbose=False)
