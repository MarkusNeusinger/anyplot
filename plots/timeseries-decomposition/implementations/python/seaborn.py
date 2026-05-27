""" anyplot.ai
timeseries-decomposition: Time Series Decomposition Plot
Library: seaborn 0.13.2 | Python 3.13.13
Quality: 97/100 | Updated: 2026-05-14
"""

import os

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
INK_MUTED = "#6B6A63" if THEME == "light" else "#A8A79F"
RULE = "rgba(26,26,23,0.10)" if THEME == "light" else "rgba(240,239,232,0.10)"

BRAND = "#009E73"
COLOR_TREND = "#C475FD"
COLOR_SEASONAL = "#4467A3"
COLOR_RESIDUAL = "#BD8233"

# Set seaborn theme with theme-adaptive colors
sns.set_theme(
    style="ticks",
    rc={
        "figure.facecolor": PAGE_BG,
        "axes.facecolor": PAGE_BG,
        "axes.edgecolor": INK_SOFT,
        "axes.labelcolor": INK,
        "text.color": INK,
        "xtick.color": INK_SOFT,
        "ytick.color": INK_SOFT,
        "grid.color": INK,
        "grid.alpha": 0.10,
        "legend.facecolor": ELEVATED_BG,
        "legend.edgecolor": INK_SOFT,
    },
)

# Data - Monthly electricity consumption (kWh)
np.random.seed(42)
n_years = 8
n_months = n_years * 12
period = 12

# Create date range
dates = pd.date_range(start="2016-01-01", periods=n_months, freq="MS")

# Generate realistic electricity consumption with trend, seasonality, and noise
# Trend: growing demand over years (5000 to 7500 kWh)
trend_component = np.linspace(5000, 7500, n_months)

# Seasonality: higher in summer/winter (AC/heating), lower in spring/fall
seasonal_pattern = np.array([1.25, 1.20, 1.05, 0.95, 0.85, 0.90, 1.10, 1.15, 1.05, 0.95, 1.10, 1.20])
seasonal_component = np.tile(seasonal_pattern, n_years)

# Noise
noise = np.random.normal(0, 100, n_months)

# Multiplicative model
values = trend_component * seasonal_component + noise

# Create DataFrame
df = pd.DataFrame({"date": dates, "consumption": values})
df = df.set_index("date")

# Manual seasonal decomposition (additive model)
trend = df["consumption"].rolling(window=period, center=True, min_periods=1).mean()
detrended = df["consumption"] - trend
seasonal = detrended.groupby(detrended.index.month).transform("mean")
residual = df["consumption"] - trend - seasonal

# Create figure with 4 subplots
fig, axes = plt.subplots(4, 1, figsize=(16, 9), sharex=True)
fig.patch.set_facecolor(PAGE_BG)
for ax in axes:
    ax.set_facecolor(PAGE_BG)

fig.subplots_adjust(hspace=0.25)

# Plot 1: Original
sns.lineplot(x=df.index, y=df["consumption"], ax=axes[0], color=BRAND, linewidth=2.5, legend=False)
axes[0].set_ylabel("Original (kWh)", fontsize=20, color=INK)
axes[0].set_title("Original", fontsize=22, fontweight="medium", loc="left", color=INK)
axes[0].tick_params(axis="both", labelsize=16, colors=INK_SOFT)
axes[0].grid(True, alpha=0.1, linewidth=0.8)
axes[0].spines["top"].set_visible(False)
axes[0].spines["right"].set_visible(False)
for spine in ("left", "bottom"):
    axes[0].spines[spine].set_color(INK_SOFT)

# Plot 2: Trend
sns.lineplot(x=trend.index, y=trend.values, ax=axes[1], color=COLOR_TREND, linewidth=2.5, legend=False)
axes[1].set_ylabel("Trend (kWh)", fontsize=20, color=INK)
axes[1].set_title("Trend", fontsize=22, fontweight="medium", loc="left", color=INK)
axes[1].tick_params(axis="both", labelsize=16, colors=INK_SOFT)
axes[1].grid(True, alpha=0.1, linewidth=0.8)
axes[1].spines["top"].set_visible(False)
axes[1].spines["right"].set_visible(False)
for spine in ("left", "bottom"):
    axes[1].spines[spine].set_color(INK_SOFT)

# Plot 3: Seasonal
sns.lineplot(x=seasonal.index, y=seasonal.values, ax=axes[2], color=COLOR_SEASONAL, linewidth=2.5, legend=False)
axes[2].axhline(y=0, color=INK_SOFT, linestyle="--", linewidth=1, alpha=0.5)
axes[2].set_ylabel("Seasonal (kWh)", fontsize=20, color=INK)
axes[2].set_title("Seasonal", fontsize=22, fontweight="medium", loc="left", color=INK)
axes[2].tick_params(axis="both", labelsize=16, colors=INK_SOFT)
axes[2].grid(True, alpha=0.1, linewidth=0.8)
axes[2].spines["top"].set_visible(False)
axes[2].spines["right"].set_visible(False)
for spine in ("left", "bottom"):
    axes[2].spines[spine].set_color(INK_SOFT)

# Plot 4: Residual
sns.lineplot(x=residual.index, y=residual.values, ax=axes[3], color=COLOR_RESIDUAL, linewidth=2.0, legend=False)
axes[3].axhline(y=0, color=INK_SOFT, linestyle="--", linewidth=1, alpha=0.5)
axes[3].set_ylabel("Residual (kWh)", fontsize=20, color=INK)
axes[3].set_xlabel("Date", fontsize=20, color=INK)
axes[3].set_title("Residual", fontsize=22, fontweight="medium", loc="left", color=INK)
axes[3].tick_params(axis="both", labelsize=16, colors=INK_SOFT)
axes[3].grid(True, alpha=0.1, linewidth=0.8)
axes[3].spines["top"].set_visible(False)
axes[3].spines["right"].set_visible(False)
for spine in ("left", "bottom"):
    axes[3].spines[spine].set_color(INK_SOFT)

# Main title
fig.suptitle("timeseries-decomposition · seaborn · anyplot.ai", fontsize=24, fontweight="medium", y=0.995, color=INK)

plt.tight_layout(rect=[0, 0, 1, 0.99])
plt.savefig(f"plot-{THEME}.png", dpi=300, bbox_inches="tight", facecolor=PAGE_BG)
