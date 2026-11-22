"""anyplot.ai
indicator-macd: MACD Technical Indicator Chart
Library: matplotlib 3.10.9 | Python 3.13.13
Quality: 90/100 | Updated: 2026-05-16
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

# Imprint palette: all eight positions in canonical order
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]
POSITIVE_COLOR = IMPRINT_PALETTE[0]  # green: histogram above zero
NEGATIVE_COLOR = IMPRINT_PALETTE[4]  # red: histogram below zero
MACD_COLOR = IMPRINT_PALETTE[2]  # blue: MACD line
SIGNAL_COLOR = IMPRINT_PALETTE[3]  # ochre: signal line

# Constants
FAST, SLOW, SIGNAL_SPAN = 12, 26, 9  # standard MACD parameters
WARMUP = 30  # leading rows dropped while the averages fill

# Columns: set these to your table's column names
DATE = "Date"  # role: date
MACD = "MACD"  # role: macd
SIGNAL = "Signal"  # role: signal
HISTOGRAM = "Histogram"  # role: histogram

# Data: replace this block with your own table, for example df = pd.read_csv("macd.csv", parse_dates=[DATE])
np.random.seed(42)
n_days = 150
returns = np.random.normal(0.0005, 0.015, n_days)
price = pd.Series(100 * np.cumprod(1 + returns))
macd_values = price.ewm(span=FAST, adjust=False).mean() - price.ewm(span=SLOW, adjust=False).mean()
signal_values = macd_values.ewm(span=SIGNAL_SPAN, adjust=False).mean()
df = pd.DataFrame(
    {
        DATE: pd.date_range("2024-06-01", periods=n_days, freq="B"),
        MACD: macd_values,
        SIGNAL: signal_values,
        HISTOGRAM: macd_values - signal_values,
    }
).iloc[WARMUP:]

# Plot: reads only df and the constants above
fig, (ax1, ax2) = plt.subplots(
    2, 1, figsize=(8, 4.5), dpi=400, facecolor=PAGE_BG, sharex=True, gridspec_kw={"height_ratios": [2, 1]}
)

for ax in (ax1, ax2):
    ax.set_facecolor(PAGE_BG)
    ax.tick_params(axis="both", labelsize=8, colors=INK_SOFT)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    for s in ("left", "bottom"):
        ax.spines[s].set_color(INK_SOFT)
    ax.yaxis.grid(True, alpha=0.10, linewidth=0.8, color=INK_SOFT)

# Upper panel: MACD and signal lines
ax1.plot(df[DATE], df[MACD], color=MACD_COLOR, linewidth=2.5, label=f"{MACD} ({FAST}, {SLOW})")
ax1.plot(df[DATE], df[SIGNAL], color=SIGNAL_COLOR, linewidth=2.5, label=f"{SIGNAL} ({SIGNAL_SPAN})")
ax1.axhline(0, color=INK_SOFT, linestyle="--", linewidth=1.0, alpha=0.6)
ax1.set_ylabel(f"{MACD} value", fontsize=10, color=INK)
leg = ax1.legend(fontsize=8, loc="upper left")
leg.get_frame().set_facecolor(ELEVATED_BG)
leg.get_frame().set_edgecolor(INK_SOFT)
leg.get_frame().set_alpha(0.95)
plt.setp(leg.get_texts(), color=INK_SOFT)

# Lower panel: histogram, green above zero and red below
bar_colors = np.where(df[HISTOGRAM] >= 0, POSITIVE_COLOR, NEGATIVE_COLOR)
ax2.bar(df[DATE], df[HISTOGRAM], color=bar_colors, alpha=0.85, width=0.8)
ax2.axhline(0, color=INK_SOFT, linestyle="-", linewidth=1.0, alpha=0.7)
ax2.set_xlabel(DATE, fontsize=10, color=INK)
ax2.set_ylabel(HISTOGRAM, fontsize=10, color=INK)

fig.autofmt_xdate(rotation=45, ha="right")
fig.suptitle("indicator-macd · python · matplotlib · anyplot.ai", fontsize=12, fontweight="medium", color=INK)
fig.tight_layout(rect=(0, 0, 1, 0.97))

plt.savefig(f"plot-{THEME}.png", dpi=400, facecolor=PAGE_BG)
