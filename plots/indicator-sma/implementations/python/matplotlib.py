""" anyplot.ai
indicator-sma: Simple Moving Average (SMA) Indicator Chart
Library: matplotlib 3.10.9 | Python 3.13.13
Quality: 90/100 | Updated: 2026-05-19
"""

import os

import matplotlib.dates as mdates
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Okabe-Ito palette — canonical order
PRICE_COLOR = "#009E73"  # position 1 — price line (first series)
SMA20_COLOR = "#C475FD"  # position 2
SMA50_COLOR = "#4467A3"  # position 3
SMA200_COLOR = "#BD8233"  # position 4

# Data - realistic stock price data with trend and volatility
np.random.seed(42)
n_days = 300
dates = pd.date_range("2024-01-01", periods=n_days, freq="B")  # Business days

base_price = 150
returns = np.random.normal(0.0003, 0.015, n_days)
trend = np.sin(np.linspace(0, 3 * np.pi, n_days)) * 0.001
returns = returns + trend
close = base_price * np.cumprod(1 + returns)

df = pd.DataFrame({"date": dates, "close": close})
df["sma_20"] = df["close"].rolling(window=20).mean()
df["sma_50"] = df["close"].rolling(window=50).mean()
df["sma_200"] = df["close"].rolling(window=200).mean()

# Plot
fig, ax = plt.subplots(figsize=(16, 9), facecolor=PAGE_BG)
ax.set_facecolor(PAGE_BG)

ax.plot(df["date"], df["close"], color=PRICE_COLOR, linewidth=2.5, label="Price", alpha=0.85, zorder=4)
ax.plot(df["date"], df["sma_20"], color=SMA20_COLOR, linewidth=2.0, label="SMA 20", zorder=3)
ax.plot(df["date"], df["sma_50"], color=SMA50_COLOR, linewidth=2.0, label="SMA 50", zorder=2)
ax.plot(df["date"], df["sma_200"], color=SMA200_COLOR, linewidth=2.0, label="SMA 200", zorder=1)

# Style
ax.set_xlabel("Date", fontsize=20, color=INK)
ax.set_ylabel("Price ($)", fontsize=20, color=INK)
ax.set_title("indicator-sma · python · matplotlib · anyplot.ai", fontsize=24, fontweight="medium", color=INK)
ax.tick_params(axis="both", labelsize=16, colors=INK_SOFT)

# Date formatting with month locator
ax.xaxis.set_major_locator(mdates.MonthLocator())
ax.xaxis.set_major_formatter(mdates.DateFormatter("%b %Y"))
fig.autofmt_xdate(rotation=30)

# Grid — y-axis only for line chart
ax.yaxis.grid(True, alpha=0.10, linewidth=0.8, color=INK)
ax.set_axisbelow(True)

# Spines
ax.spines["top"].set_visible(False)
ax.spines["right"].set_visible(False)
for s in ("left", "bottom"):
    ax.spines[s].set_color(INK_SOFT)

# Legend — upper right avoids overlap with early price data
leg = ax.legend(fontsize=16, loc="upper right")
leg.get_frame().set_facecolor(ELEVATED_BG)
leg.get_frame().set_edgecolor(INK_SOFT)
plt.setp(leg.get_texts(), color=INK_SOFT)

plt.tight_layout()
plt.savefig(f"plot-{THEME}.png", dpi=300, bbox_inches="tight", facecolor=PAGE_BG)
