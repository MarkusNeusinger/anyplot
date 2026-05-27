""" anyplot.ai
candlestick-volume: Stock Candlestick Chart with Volume
Library: matplotlib 3.10.9 | Python 3.13.13
Quality: 93/100 | Updated: 2026-05-16
"""

import os

import matplotlib.dates as mdates
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.patches import Patch


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# imprint semantic anchors
UP_COLOR = "#009E73"  # green — up days
DOWN_COLOR = "#AE3030"  # red — down days

# Data - Generate realistic 60 trading days of OHLC data with volume
np.random.seed(42)
n_days = 60
dates = pd.date_range("2024-01-02", periods=n_days, freq="B")  # Business days

# Generate price path with realistic movement
base_price = 150.0
returns = np.random.normal(0.001, 0.02, n_days)
prices = base_price * np.cumprod(1 + returns)

# Create OHLC data
opens = np.zeros(n_days)
highs = np.zeros(n_days)
lows = np.zeros(n_days)
closes = np.zeros(n_days)

opens[0] = base_price
closes[0] = prices[0]
for i in range(1, n_days):
    opens[i] = closes[i - 1] * (1 + np.random.normal(0, 0.005))
    closes[i] = prices[i]

# High/low based on open/close with some variation
for i in range(n_days):
    oc_max = max(opens[i], closes[i])
    oc_min = min(opens[i], closes[i])
    highs[i] = oc_max + np.random.uniform(0.5, 2.0)
    lows[i] = oc_min - np.random.uniform(0.5, 2.0)

# Volume with higher volume on big moves
base_volume = 5_000_000
volume_multiplier = 1 + np.abs(closes - opens) / opens * 20
volumes = base_volume * volume_multiplier * np.random.uniform(0.7, 1.3, n_days)
volumes = volumes.astype(int)

# Colors for up/down days
is_up = closes >= opens

# Create figure with two subplots sharing x-axis (75% price, 25% volume)
fig, (ax_price, ax_volume) = plt.subplots(
    2, 1, figsize=(16, 9), gridspec_kw={"height_ratios": [3, 1]}, sharex=True, facecolor=PAGE_BG
)
ax_price.set_facecolor(PAGE_BG)
ax_volume.set_facecolor(PAGE_BG)

# Candlestick chart - Price pane
candle_width = 0.6
for i in range(n_days):
    color = UP_COLOR if is_up[i] else DOWN_COLOR
    # Draw wick (high-low line)
    ax_price.plot([dates[i], dates[i]], [lows[i], highs[i]], color=color, linewidth=2.5, solid_capstyle="round")
    # Draw body (open-close rectangle)
    body_bottom = min(opens[i], closes[i])
    body_height = abs(closes[i] - opens[i])
    ax_price.bar(
        dates[i], body_height, width=candle_width, bottom=body_bottom, color=color, edgecolor=color, linewidth=0.5
    )

# Volume bars with matching colors
for i in range(n_days):
    color = UP_COLOR if is_up[i] else DOWN_COLOR
    ax_volume.bar(dates[i], volumes[i], width=candle_width, color=color, alpha=0.8)

# Price pane styling
ax_price.set_ylabel("Price ($)", fontsize=20, color=INK)
ax_price.tick_params(axis="both", labelsize=16, colors=INK_SOFT, labelcolor=INK_SOFT)
ax_price.grid(True, alpha=0.15, linewidth=0.8, color=INK)
ax_price.set_title("candlestick-volume · matplotlib · anyplot.ai", fontsize=24, fontweight="medium", color=INK, pad=15)

# Add legend
legend_elements = [
    Patch(facecolor=UP_COLOR, label="Up (Close ≥ Open)"),
    Patch(facecolor=DOWN_COLOR, label="Down (Close < Open)"),
]
leg = ax_price.legend(handles=legend_elements, loc="upper left", fontsize=16)
leg.get_frame().set_facecolor(ELEVATED_BG)
leg.get_frame().set_edgecolor(INK_SOFT)
leg.get_frame().set_linewidth(0.8)
for text in leg.get_texts():
    text.set_color(INK_SOFT)

# Volume pane styling
ax_volume.set_xlabel("Date", fontsize=20, color=INK)
ax_volume.set_ylabel("Volume (shares)", fontsize=20, color=INK)
ax_volume.tick_params(axis="both", labelsize=16, colors=INK_SOFT, labelcolor=INK_SOFT)
ax_volume.grid(True, alpha=0.15, linewidth=0.8, color=INK)

# Format y-axis for volume (in millions)
ax_volume.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f"{x / 1e6:.1f}M"))

# Format x-axis dates
ax_volume.xaxis.set_major_locator(mdates.WeekdayLocator(byweekday=mdates.MO, interval=2))
ax_volume.xaxis.set_major_formatter(mdates.DateFormatter("%b %d"))
plt.setp(ax_volume.xaxis.get_majorticklabels(), rotation=45, ha="right", color=INK_SOFT)

# Ensure y-axis starts at 0 for volume
ax_volume.set_ylim(bottom=0)

# Crosshair cursor: vertical line at mouse position spanning both panes
# Static crosshair at the midpoint for visual alignment
midpoint_date = dates[n_days // 2]
for ax in [ax_price, ax_volume]:
    ax.axvline(x=midpoint_date, color=INK_SOFT, linestyle="--", linewidth=1, alpha=0.4)

# Spine styling for both panes
for ax in [ax_price, ax_volume]:
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    for s in ("left", "bottom"):
        ax.spines[s].set_color(INK_SOFT)
        ax.spines[s].set_linewidth(0.8)

plt.tight_layout()
plt.savefig(f"plot-{THEME}.png", dpi=300, bbox_inches="tight", facecolor=PAGE_BG)
