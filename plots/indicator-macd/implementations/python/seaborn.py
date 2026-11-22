"""anyplot.ai
indicator-macd: MACD Technical Indicator Chart
Library: seaborn 0.13.2 | Python 3.13.13
Quality: 91/100 | Updated: 2026-05-16
"""

import os

import matplotlib.dates as mdates
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

# Imprint palette: canonical order, first position is #009E73
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]
HIST_POSITIVE = IMPRINT_PALETTE[0]  # green: the spec asks for green above zero
HIST_NEGATIVE = IMPRINT_PALETTE[4]  # red: the spec asks for red below zero
MACD_COLOR = IMPRINT_PALETTE[2]  # blue
SIGNAL_COLOR = IMPRINT_PALETTE[3]  # ochre

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

# Constants
FAST_SPAN = 12  # standard MACD parameters
SLOW_SPAN = 26
SIGNAL_SPAN = 9

# Columns: set these to your table's column names
DATE = "Date"  # role: date
MACD = "MACD value"  # role: macd
SIGNAL = "Signal"  # role: signal
HISTOGRAM = "Histogram"  # role: histogram

# Data: replace this block with your own table, for example df = pd.read_csv("macd.csv")
np.random.seed(42)
n_days = 120
returns = np.random.normal(0.001, 0.015, n_days)
close = pd.Series(100 * np.exp(np.cumsum(returns)))
macd_line = close.ewm(span=FAST_SPAN, adjust=False).mean() - close.ewm(span=SLOW_SPAN, adjust=False).mean()
signal_line = macd_line.ewm(span=SIGNAL_SPAN, adjust=False).mean()
df = pd.DataFrame(
    {
        DATE: pd.date_range("2024-01-01", periods=n_days, freq="B"),
        MACD: macd_line,
        SIGNAL: signal_line,
        HISTOGRAM: macd_line - signal_line,
    }
).iloc[SLOW_SPAN + SIGNAL_SPAN - 2 :]

# Plot: reads only df and the constants above
positive = df[HISTOGRAM] >= 0
fig, ax = plt.subplots(figsize=(8, 4.5), dpi=400, facecolor=PAGE_BG)

ax.bar(
    df[DATE][positive],
    df[HISTOGRAM][positive],
    width=0.8,
    color=HIST_POSITIVE,
    alpha=0.55,
    linewidth=0,
    label="Histogram (+)",
)
ax.bar(
    df[DATE][~positive],
    df[HISTOGRAM][~positive],
    width=0.8,
    color=HIST_NEGATIVE,
    alpha=0.55,
    linewidth=0,
    label="Histogram (−)",
)
sns.lineplot(data=df, x=DATE, y=MACD, ax=ax, color=MACD_COLOR, linewidth=2, label=f"MACD ({FAST_SPAN}, {SLOW_SPAN})")
sns.lineplot(data=df, x=DATE, y=SIGNAL, ax=ax, color=SIGNAL_COLOR, linewidth=2, label=f"Signal ({SIGNAL_SPAN})")
ax.axhline(0, color=INK_SOFT, linestyle="--", linewidth=1.0)

# Style
ax.set_title("indicator-macd · python · seaborn · anyplot.ai", fontsize=12, fontweight="medium", color=INK)
ax.set_xlabel(DATE, fontsize=10)
ax.set_ylabel(MACD, fontsize=10)
ax.tick_params(axis="both", labelsize=8)
ax.xaxis.set_major_formatter(mdates.ConciseDateFormatter(ax.xaxis.get_major_locator()))
sns.despine(ax=ax)
ax.yaxis.grid(True, linewidth=0.8)
ax.legend(fontsize=8, loc="upper left", ncol=2, framealpha=0.95)

plt.tight_layout()
plt.savefig(f"plot-{THEME}.png", dpi=400, facecolor=PAGE_BG)
