"""anyplot.ai
indicator-bollinger: Bollinger Bands Indicator Chart
Library: matplotlib 3.10.9 | Python 3.13.13
Quality: 90/100 | Updated: 2026-05-17
"""

import os

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Imprint palette: all eight positions, canonical order
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

# Constants
WINDOW = 20  # standard Bollinger period
NUM_STD = 2  # standard deviation multiple of the outer bands

# Columns: set these to your table's column names
DATE = "Date"  # role: date
CLOSE = "Close price ($)"  # role: close
SMA = "SMA (20-day)"  # role: sma
UPPER = "Upper band ($)"  # role: upper_band
LOWER = "Lower band ($)"  # role: lower_band

# Data: replace this block with your own table, for example df = pd.read_csv("prices.csv")
np.random.seed(42)
n_days = 120
price = 150 * np.cumprod(1 + np.random.normal(0.0005, 0.015, n_days))
rolling = pd.Series(price).rolling(window=WINDOW)
df = pd.DataFrame(
    {
        DATE: pd.date_range("2024-01-01", periods=n_days, freq="B"),
        CLOSE: price,
        SMA: rolling.mean(),
        UPPER: rolling.mean() + NUM_STD * rolling.std(),
        LOWER: rolling.mean() - NUM_STD * rolling.std(),
    }
)

# Plot: reads only df and the constants above
fig, ax = plt.subplots(figsize=(8, 4.5), dpi=400, facecolor=PAGE_BG)
ax.set_facecolor(PAGE_BG)

# Volatility envelope: one shared band color, semi-transparent fill between the outer bands
band_color = IMPRINT_PALETTE[2]
ax.fill_between(
    df[DATE], df[LOWER], df[UPPER], alpha=0.15, color=band_color, linewidth=0, label=f"Volatility band (±{NUM_STD}σ)"
)
ax.plot(df[DATE], df[UPPER], color=band_color, linewidth=1.5, alpha=0.7)
ax.plot(df[DATE], df[LOWER], color=band_color, linewidth=1.5, alpha=0.7)

# Middle band dashed, closing price prominent in brand green
ax.plot(df[DATE], df[SMA], color=IMPRINT_PALETTE[1], linewidth=1.5, linestyle="--", label=f"SMA ({WINDOW}-day)")
ax.plot(df[DATE], df[CLOSE], color=IMPRINT_PALETTE[0], linewidth=2, label="Close price")

# Style
ax.set_xlabel(DATE, fontsize=10, color=INK)
ax.set_ylabel("Price ($)", fontsize=10, color=INK)
ax.set_title("indicator-bollinger · python · matplotlib · anyplot.ai", fontsize=12, fontweight="medium", color=INK)
ax.tick_params(axis="both", labelsize=8, colors=INK_SOFT)
ax.xaxis.set_major_locator(plt.MaxNLocator(8))
fig.autofmt_xdate(rotation=30)

for s in ("top", "right"):
    ax.spines[s].set_visible(False)
for s in ("left", "bottom"):
    ax.spines[s].set_color(INK_SOFT)
ax.yaxis.grid(True, alpha=0.1, linewidth=0.8, color=INK_SOFT)

leg = ax.legend(fontsize=8, loc="lower left", framealpha=0.95)
leg.get_frame().set_facecolor(ELEVATED_BG)
leg.get_frame().set_edgecolor(INK_SOFT)
leg.get_frame().set_linewidth(0.8)
plt.setp(leg.get_texts(), color=INK_SOFT)

fig.subplots_adjust(left=0.08, right=0.97, top=0.92, bottom=0.17)
plt.savefig(f"plot-{THEME}.png", dpi=400, facecolor=PAGE_BG)
