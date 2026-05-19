""" anyplot.ai
indicator-sma: Simple Moving Average (SMA) Indicator Chart
Library: seaborn 0.13.2 | Python 3.13.13
Quality: 88/100 | Updated: 2026-05-19
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

# Okabe-Ito palette — close price first (brand green), then SMAs in canonical order
PALETTE = {"Close Price": "#009E73", "SMA 20": "#D55E00", "SMA 50": "#0072B2", "SMA 200": "#CC79A7"}

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

# Data — realistic stock price with geometric random walk and mild upward drift
np.random.seed(42)
n_days = 300
dates = pd.date_range(start="2025-01-01", periods=n_days, freq="B")
returns = np.random.normal(0.0005, 0.015, n_days)
prices = 100 * np.cumprod(1 + returns)
trend = np.linspace(0, 20, n_days)
prices = prices + trend * 0.3

df = pd.DataFrame({"date": dates, "close": prices})
df["sma_20"] = df["close"].rolling(window=20).mean()
df["sma_50"] = df["close"].rolling(window=50).mean()
df["sma_200"] = df["close"].rolling(window=200).mean()

# Reshape to long format for seaborn native hue parameter
df_long = pd.melt(
    df, id_vars=["date"], value_vars=["close", "sma_20", "sma_50", "sma_200"], var_name="series", value_name="price"
)
label_map = {"close": "Close Price", "sma_20": "SMA 20", "sma_50": "SMA 50", "sma_200": "SMA 200"}
df_long["series"] = df_long["series"].map(label_map)

# Plot
fig, ax = plt.subplots(figsize=(16, 9), facecolor=PAGE_BG)
ax.set_facecolor(PAGE_BG)

sns.lineplot(
    data=df_long,
    x="date",
    y="price",
    hue="series",
    palette=PALETTE,
    hue_order=list(PALETTE.keys()),
    linewidth=2.2,
    ax=ax,
)

# Style
ax.set_title("indicator-sma · python · seaborn · anyplot.ai", fontsize=24, fontweight="medium", color=INK, pad=20)
ax.set_xlabel("Date", fontsize=20, color=INK)
ax.set_ylabel("Price ($)", fontsize=20, color=INK)
ax.tick_params(axis="both", labelsize=16, colors=INK_SOFT)

ax.spines["top"].set_visible(False)
ax.spines["right"].set_visible(False)
ax.spines["left"].set_color(INK_SOFT)
ax.spines["bottom"].set_color(INK_SOFT)

ax.yaxis.grid(True, alpha=0.12, linewidth=0.8, color=INK)
ax.xaxis.grid(False)
ax.set_axisbelow(True)

legend = ax.get_legend()
if legend:
    legend.set_title(None)
    legend.get_frame().set_facecolor(ELEVATED_BG)
    legend.get_frame().set_edgecolor(INK_SOFT)
    for text in legend.get_texts():
        text.set_color(INK)
        text.set_fontsize(16)

fig.autofmt_xdate(rotation=30)

plt.tight_layout()
plt.savefig(f"plot-{THEME}.png", dpi=300, bbox_inches="tight", facecolor=PAGE_BG)
