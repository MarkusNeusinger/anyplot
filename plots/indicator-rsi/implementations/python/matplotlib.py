"""anyplot.ai
indicator-rsi: RSI Technical Indicator Chart
Library: matplotlib 3.10.9 | Python 3.13.13
Quality: pending | Updated: 2026-05-16
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

# Imprint palette: position 1 is the single series, 5 and 3 mark the overbought and oversold zones
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

# Constants
OVERBOUGHT = 70  # RSI level above which a market counts as overbought
OVERSOLD = 30  # RSI level below which a market counts as oversold
CENTERLINE = 50  # bullish / bearish bias line
LOOKBACK = 14  # standard RSI lookback period

# Columns: set these to your table's column names
DATE = "Date"  # role: date
RSI = "RSI value"  # role: rsi

# Data: replace this block with your own table, for example df = pd.read_csv("rsi.csv")
# Synthetic daily closing prices (120 days, volatility regimes), turned into Wilder RSI
np.random.seed(42)
n_days = 120
dates = pd.date_range("2024-01-01", periods=n_days, freq="D")
trend = np.linspace(0, 0.15, n_days)
volatility = np.concatenate(
    [
        np.full(30, 0.015),  # low volatility
        np.full(30, 0.035),  # high volatility
        np.full(30, 0.025),  # medium
        np.full(30, 0.04),  # very high
    ]
)
returns = np.random.normal(0.0005, 1, n_days) * volatility + trend / n_days
prices = 100 * np.cumprod(1 + returns)

delta = np.diff(prices)
gains = np.where(delta > 0, delta, 0)
losses = np.where(delta < 0, -delta, 0)
avg_gain = np.zeros(len(delta))
avg_loss = np.zeros(len(delta))
avg_gain[LOOKBACK - 1] = np.mean(gains[:LOOKBACK])
avg_loss[LOOKBACK - 1] = np.mean(losses[:LOOKBACK])
for i in range(LOOKBACK, len(delta)):
    avg_gain[i] = (avg_gain[i - 1] * (LOOKBACK - 1) + gains[i]) / LOOKBACK
    avg_loss[i] = (avg_loss[i - 1] * (LOOKBACK - 1) + losses[i]) / LOOKBACK
rs = np.divide(avg_gain, avg_loss, out=np.ones_like(avg_gain), where=avg_loss != 0)
rsi = (100 - (100 / (1 + rs)))[LOOKBACK - 1 :]

df = pd.DataFrame({DATE: dates[LOOKBACK:], RSI: rsi})

# Plot: reads only df and the constants above
fig, ax = plt.subplots(figsize=(8, 4.5), dpi=400, facecolor=PAGE_BG)
ax.set_facecolor(PAGE_BG)

# Shaded zones: overbought in imprint red (semantic danger), oversold in imprint blue
ax.fill_between(df[DATE], OVERBOUGHT, 100, alpha=0.12, color=IMPRINT_PALETTE[4])
ax.fill_between(df[DATE], 0, OVERSOLD, alpha=0.12, color=IMPRINT_PALETTE[2])

# RSI line with the lookback noted in the legend
ax.plot(df[DATE], df[RSI], color=IMPRINT_PALETTE[0], linewidth=2.0, label=f"RSI ({LOOKBACK}-period)")

# Reference lines
ax.axhline(OVERBOUGHT, color=INK_SOFT, linestyle="--", linewidth=1.2, alpha=0.5)
ax.axhline(OVERSOLD, color=INK_SOFT, linestyle="--", linewidth=1.2, alpha=0.5)
ax.axhline(CENTERLINE, color=INK_SOFT, linestyle=":", linewidth=1.0, alpha=0.3)

# Fixed y-axis from 0 to 100
ax.set_ylim(0, 100)
ax.set_xlim(df[DATE].min(), df[DATE].max())

# Threshold labels, placed in offset points from the reference lines
last_date = df[DATE].iloc[-1]
ax.annotate(
    "Overbought",
    xy=(last_date, OVERBOUGHT),
    xytext=(0, 3),
    textcoords="offset points",
    fontsize=7,
    color=INK_SOFT,
    ha="right",
    va="bottom",
)
ax.annotate(
    "Oversold",
    xy=(last_date, OVERSOLD),
    xytext=(0, -3),
    textcoords="offset points",
    fontsize=7,
    color=INK_SOFT,
    ha="right",
    va="top",
)

# Style
ax.set_title("indicator-rsi · python · matplotlib · anyplot.ai", fontsize=12, fontweight="medium", color=INK)
ax.set_xlabel(DATE, fontsize=10, color=INK)
ax.set_ylabel(RSI, fontsize=10, color=INK)
ax.tick_params(axis="both", labelsize=8, colors=INK_SOFT, labelcolor=INK_SOFT)
ax.yaxis.grid(True, alpha=0.1, linewidth=0.8, color=INK)
ax.xaxis.grid(False)

leg = ax.legend(fontsize=8, loc="upper left")
leg.get_frame().set_facecolor(ELEVATED_BG)
leg.get_frame().set_edgecolor(INK_SOFT)
leg.get_frame().set_alpha(0.95)
plt.setp(leg.get_texts(), color=INK_SOFT)

for s in ("left", "bottom"):
    ax.spines[s].set_color(INK_SOFT)
ax.spines["top"].set_visible(False)
ax.spines["right"].set_visible(False)

fig.tight_layout()
plt.savefig(f"plot-{THEME}.png", dpi=400, facecolor=PAGE_BG)
