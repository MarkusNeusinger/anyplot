"""anyplot.ai
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

# Imprint palette: close price first (brand green), then the SMAs in canonical order
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

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

# Columns: set these to your table's column names
DATE = "Date"  # role: date
CLOSE = "Close Price"  # role: close
SMA_SHORT = "SMA 20"  # role: sma_short
SMA_MEDIUM = "SMA 50"  # role: sma_medium
SMA_LONG = "SMA 200"  # role: sma_long
PRICE_LABEL = "Price ($)"

# Data: replace this block with your own table, for example df = pd.read_csv("prices.csv")
np.random.seed(42)
n_days = 300
dates = pd.date_range(start="2025-01-01", periods=n_days, freq="B")
returns = np.random.normal(0.0005, 0.015, n_days)
prices = 100 * np.cumprod(1 + returns) + np.linspace(0, 20, n_days) * 0.3
df = pd.DataFrame({DATE: dates, CLOSE: prices})
df[SMA_SHORT] = df[CLOSE].rolling(window=20).mean()
df[SMA_MEDIUM] = df[CLOSE].rolling(window=50).mean()
df[SMA_LONG] = df[CLOSE].rolling(window=200).mean()

# Plot: reads only df and the constants above
series = [CLOSE, SMA_SHORT, SMA_MEDIUM, SMA_LONG]
df_long = df.melt(id_vars=[DATE], value_vars=series, var_name="Series", value_name=PRICE_LABEL)

fig, ax = plt.subplots(figsize=(8, 4.5), dpi=400, facecolor=PAGE_BG)
ax.set_facecolor(PAGE_BG)

sns.lineplot(
    data=df_long,
    x=DATE,
    y=PRICE_LABEL,
    hue="Series",
    hue_order=series,
    palette=IMPRINT_PALETTE[: len(series)],
    linewidth=1.6,
    ax=ax,
)

# Style
ax.set_title("indicator-sma · python · seaborn · anyplot.ai", fontsize=12, fontweight="medium", color=INK, pad=10)
ax.set_xlabel(DATE, fontsize=10, color=INK)
ax.set_ylabel(PRICE_LABEL, fontsize=10, color=INK)
ax.tick_params(axis="both", labelsize=8, colors=INK_SOFT)
sns.despine(ax=ax)

ax.yaxis.grid(True, alpha=0.12, linewidth=0.8, color=INK)
ax.xaxis.grid(False)
ax.set_axisbelow(True)

legend = ax.get_legend()
legend.set_title(None)
legend.get_frame().set_facecolor(ELEVATED_BG)
legend.get_frame().set_edgecolor(INK_SOFT)
for text in legend.get_texts():
    text.set_color(INK)
    text.set_fontsize(8)

fig.autofmt_xdate(rotation=30)
fig.subplots_adjust(left=0.08, right=0.97, top=0.92, bottom=0.17)
plt.savefig(f"plot-{THEME}.png", dpi=400, facecolor=PAGE_BG)
