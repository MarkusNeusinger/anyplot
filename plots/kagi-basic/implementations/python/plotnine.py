""" anyplot.ai
kagi-basic: Basic Kagi Chart
Library: plotnine 0.15.4 | Python 3.13.13
Quality: 92/100 | Updated: 2026-05-17
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
    geom_segment,
    ggplot,
    labs,
    scale_color_manual,
    scale_size_manual,
    theme,
    theme_minimal,
)


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
RULE = "rgba(26,26,23,0.10)" if THEME == "light" else "rgba(240,239,232,0.10)"

# imprint semantic anchors (green for yang/bullish, red for yin/bearish)
YANG_COLOR = "#009E73"
YIN_COLOR = "#AE3030"

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
    is_yang = direction == 1

    for i in range(1, len(prices)):
        price = prices[i]

        if direction == 1:
            if price > high:
                high = price
                is_yang = True
            elif price < high * (1 - reversal_pct):
                kagi_segments.append(
                    {
                        "x": x_idx,
                        "x_end": x_idx,
                        "y": segment_start_price,
                        "y_end": high,
                        "trend": "yang" if is_yang else "yin",
                    }
                )
                kagi_segments.append(
                    {"x": x_idx, "x_end": x_idx + 1, "y": high, "y_end": high, "trend": "yang" if is_yang else "yin"}
                )
                x_idx += 1
                direction = -1
                segment_start_price = high
                low = price
                high = price

        else:
            if price < low:
                low = price
                is_yang = False
            elif price > low * (1 + reversal_pct):
                kagi_segments.append(
                    {
                        "x": x_idx,
                        "x_end": x_idx,
                        "y": segment_start_price,
                        "y_end": low,
                        "trend": "yin" if not is_yang else "yang",
                    }
                )
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

# Create plot with trend layers and legend
plot = (
    ggplot(kagi_df, aes(x="x", xend="x_end", y="y", yend="y_end", color="trend", size="trend"))
    + geom_segment(lineend="round")
    + scale_color_manual(
        values={"yang": YANG_COLOR, "yin": YIN_COLOR}, labels={"yang": "Yang (Bullish)", "yin": "Yin (Bearish)"}
    )
    + scale_size_manual(values={"yang": 2, "yin": 0.7})
    + labs(x="Kagi Line Index", y="Price ($)", title="kagi-basic · plotnine · anyplot.ai", color="Trend")
    + theme_minimal()
    + theme(
        figure_size=(16, 9),
        plot_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
        panel_background=element_rect(fill=PAGE_BG),
        panel_grid_major=element_line(color=INK, size=0.3, alpha=0.10),
        panel_grid_minor=element_blank(),
        panel_border=element_line(color=INK_SOFT),
        axis_title=element_text(size=20, color=INK),
        axis_text=element_text(size=16, color=INK_SOFT),
        axis_line=element_line(color=INK_SOFT),
        plot_title=element_text(size=24, color=INK),
        legend_background=element_rect(fill=ELEVATED_BG, color=INK_SOFT),
        legend_text=element_text(size=16, color=INK_SOFT),
        legend_title=element_text(size=18, color=INK),
        legend_position="right",
        text=element_text(size=14),
    )
)

# Save plot
plot.save(f"plot-{THEME}.png", dpi=300, verbose=False)
