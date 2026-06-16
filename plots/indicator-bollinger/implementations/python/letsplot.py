""" anyplot.ai
indicator-bollinger: Bollinger Bands Indicator Chart
Library: letsplot 4.9.0 | Python 3.13.13
Quality: 92/100 | Updated: 2026-05-17
"""
# ruff: noqa: F403, F405
"""anyplot.ai
indicator-bollinger: Bollinger Bands Indicator Chart
Library: letsplot | Python 3.13
Quality: pending | Updated: 2026-05-17
"""

import os

import numpy as np
import pandas as pd
from lets_plot import *
from lets_plot.export import ggsave


LetsPlot.setup_html()

# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

BRAND = "#009E73"  # Okabe-Ito position 1
BAND_COLOR = "#4467A3"  # Okabe-Ito position 3

# Data - Generate synthetic stock price data with Bollinger Bands
np.random.seed(42)
n_periods = 120

# Generate price data with trend and volatility
dates = pd.date_range(start="2024-01-01", periods=n_periods, freq="B")
returns = np.random.normal(0.0005, 0.018, n_periods)
# Add some volatility clustering
volatility_multiplier = np.where((np.arange(n_periods) > 40) & (np.arange(n_periods) < 70), 1.8, 1.0)
returns = returns * volatility_multiplier
close = 100 * np.exp(np.cumsum(returns))

# Calculate Bollinger Bands (20-period SMA with 2 standard deviations)
window = 20
sma = pd.Series(close).rolling(window=window).mean().values
std = pd.Series(close).rolling(window=window).std().values
upper_band = sma + 2 * std
lower_band = sma - 2 * std

df = pd.DataFrame({"date": dates, "close": close, "sma": sma, "upper_band": upper_band, "lower_band": lower_band})

# Remove NaN values from rolling calculations
df = df.dropna().reset_index(drop=True)

# Create plot with legend using color aesthetic
plot = (
    ggplot(df)
    # Bollinger Bands fill area (between upper and lower bands)
    + geom_ribbon(
        aes(x="date", ymin="lower_band", ymax="upper_band", fill="Bollinger Bands"), fill=BAND_COLOR, alpha=0.2
    )
    # Lower band line
    + geom_line(aes(x="date", y="lower_band", color="Bollinger Bands"), color=BAND_COLOR, size=1.0, alpha=0.7)
    # Upper band line
    + geom_line(aes(x="date", y="upper_band", color="Bollinger Bands"), color=BAND_COLOR, size=1.0, alpha=0.7)
    # Middle band (SMA) - dashed line
    + geom_line(aes(x="date", y="sma", color="20-SMA"), color=BAND_COLOR, size=1.2, linetype="dashed", alpha=0.9)
    # Close price line - prominent
    + geom_line(aes(x="date", y="close", color="Close Price"), color=BRAND, size=1.8)
    # Labels
    + labs(title="indicator-bollinger · letsplot · anyplot.ai", x="Date", y="Price (USD)", color="", fill="")
    # Theme and styling
    + theme_minimal()
    + theme(
        plot_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
        panel_background=element_rect(fill=PAGE_BG),
        panel_grid_major=element_line(color=INK, size=0.15),
        panel_grid_minor=element_line(color=INK, size=0.1),
        axis_title=element_text(size=20, color=INK),
        axis_text=element_text(size=16, color=INK_SOFT),
        axis_line=element_line(color=INK_SOFT, size=0.5),
        plot_title=element_text(size=24, color=INK),
    )
    + ggsize(1600, 900)
)

# Save PNG (scale=3 gives 4800x2700)
ggsave(plot, f"plot-{THEME}.png", path=".", scale=3)

# Save HTML for interactivity
ggsave(plot, f"plot-{THEME}.html", path=".")
