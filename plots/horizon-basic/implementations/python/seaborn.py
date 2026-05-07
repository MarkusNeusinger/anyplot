""" anyplot.ai
horizon-basic: Horizon Chart
Library: seaborn 0.13.2 | Python 3.13.13
Quality: 78/100 | Updated: 2026-05-07
"""

import os

import matplotlib.patches as mpatches
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd


THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Data - Stock price deviations from 20-day moving average (5 stocks over 90 trading days)
np.random.seed(42)
trading_days = 90
stocks = ["TECH", "FINANCE", "ENERGY", "HEALTHCARE", "RETAIL"]

# Generate realistic stock deviation patterns with seasonality
data = []
for stock_idx, stock in enumerate(stocks):
    np.random.seed(42 + stock_idx)
    if stock == "TECH":
        base = 8 * np.sin(np.linspace(0, 4 * np.pi, trading_days)) + 3
        noise = np.random.randn(trading_days) * 5
        values = base + noise
    elif stock == "FINANCE":
        base = np.zeros(trading_days)
        noise = np.random.randn(trading_days) * 6
        volatility_spikes = np.random.choice([-8, 0, 8], trading_days, p=[0.15, 0.7, 0.15])
        values = base + noise + volatility_spikes
    elif stock == "ENERGY":
        base = -5 * np.ones(trading_days)
        trend = np.linspace(-5, 5, trading_days)
        noise = np.random.randn(trading_days) * 4
        values = base + trend + noise
    elif stock == "HEALTHCARE":
        base = 6 * np.cos(np.linspace(0, 3 * np.pi, trading_days))
        noise = np.random.randn(trading_days) * 4
        values = base + noise
    else:
        base = np.zeros(trading_days)
        drift = np.linspace(-8, 8, trading_days)
        noise = np.random.randn(trading_days) * 3
        values = base + drift + noise

    values = np.clip(values, -15, 15)
    for day, v in enumerate(values):
        data.append({"day": day, "stock": stock, "deviation": v})

df = pd.DataFrame(data)

# Horizon chart parameters
n_bands = 3
band_height = 15 / n_bands

# Create figure
fig, axes = plt.subplots(len(stocks), 1, figsize=(16, 9), sharex=True)
fig.patch.set_facecolor(PAGE_BG)
fig.subplots_adjust(hspace=0.06)

# Color palettes for positive (green) and negative (red)
positive_colors = ["#E8F5E9", "#66BB6A", "#2E7D32"]
negative_colors = ["#FFEBEE", "#EF5350", "#C62828"]

for idx, stock in enumerate(stocks):
    ax = axes[idx]
    ax.set_facecolor(PAGE_BG)
    stock_data = df[df["stock"] == stock]
    x = np.arange(len(stock_data))
    values = stock_data["deviation"].values

    ax.set_xlim(0, len(x))
    ax.set_ylim(0, band_height)

    positive_vals = np.maximum(values, 0)
    negative_vals = np.abs(np.minimum(values, 0))

    # Draw negative bands (red)
    for band_idx in range(n_bands):
        band_min = band_idx * band_height
        neg_folded = np.clip(negative_vals - band_min, 0, band_height)
        neg_mask = (negative_vals > band_min) & (values < 0)
        neg_y = np.where(neg_mask, neg_folded, np.nan)
        ax.fill_between(x, 0, neg_y, color=negative_colors[band_idx], alpha=0.85, linewidth=0)

    # Draw positive bands (green)
    for band_idx in range(n_bands):
        band_min = band_idx * band_height
        pos_folded = np.clip(positive_vals - band_min, 0, band_height)
        pos_mask = (positive_vals > band_min) & (values > 0)
        pos_y = np.where(pos_mask, pos_folded, np.nan)
        ax.fill_between(x, 0, pos_y, color=positive_colors[band_idx], alpha=0.85, linewidth=0)

    ax.set_ylabel(stock, fontsize=16, rotation=0, ha="right", va="center", labelpad=15, color=INK)
    ax.set_yticks([])

    # Enhanced grid for better time tracking
    ax.grid(True, axis="x", alpha=0.2, linewidth=0.8, color=INK_SOFT)
    ax.set_axisbelow(True)

    # Style spines
    for spine in ["top", "right", "left"]:
        ax.spines[spine].set_visible(False)
    ax.spines["bottom"].set_color(INK_SOFT)
    ax.spines["bottom"].set_visible(idx == len(stocks) - 1)
    ax.tick_params(axis="x", colors=INK_SOFT, labelsize=16, bottom=(idx == len(stocks) - 1))

# X-axis formatting
tick_positions = np.arange(0, trading_days, 15)
tick_labels = [f"Day {i}" for i in tick_positions]
axes[-1].set_xticks(tick_positions)
axes[-1].set_xticklabels(tick_labels, fontsize=16, color=INK_SOFT)
axes[-1].set_xlabel("Trading Days (90-day period)", fontsize=20, color=INK)

# Title
fig.suptitle("horizon-basic · seaborn · anyplot.ai", fontsize=24, y=0.98, fontweight="medium", color=INK)

# Legend
legend_patches = [
    mpatches.Patch(color=positive_colors[0], label="Low positive (0–5 pp)"),
    mpatches.Patch(color=positive_colors[1], label="Medium positive (5–10 pp)"),
    mpatches.Patch(color=positive_colors[2], label="High positive (10–15 pp)"),
    mpatches.Patch(color=negative_colors[0], label="Low negative (0–5 pp)"),
    mpatches.Patch(color=negative_colors[1], label="Medium negative (5–10 pp)"),
    mpatches.Patch(color=negative_colors[2], label="High negative (10–15 pp)"),
]
fig.legend(
    handles=legend_patches,
    loc="upper right",
    bbox_to_anchor=(0.98, 0.92),
    fontsize=14,
    title="Deviation from 20-day MA (percentage points)",
    title_fontsize=14,
    framealpha=0.95,
    facecolor=ELEVATED_BG,
    edgecolor=INK_SOFT,
    ncol=2,
)

plt.tight_layout(rect=[0, 0, 1, 0.95])
plt.savefig(f"plot-{THEME}.png", dpi=300, bbox_inches="tight", facecolor=PAGE_BG)
