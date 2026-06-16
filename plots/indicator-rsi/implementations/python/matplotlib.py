""" anyplot.ai
indicator-rsi: RSI Technical Indicator Chart
Library: matplotlib 3.10.9 | Python 3.13.13
Quality: 94/100 | Updated: 2026-05-16
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
INK_MUTED = "#6B6A63" if THEME == "light" else "#A8A79F"

BRAND = "#009E73"  # Okabe-Ito position 1

# Data - Generate synthetic stock price data and calculate RSI
np.random.seed(42)
n_periods = 120

# Create trending market with volatility spikes to showcase full RSI range
dates = pd.date_range("2024-01-01", periods=n_periods, freq="D")
trend = np.linspace(0, 0.15, n_periods)
volatility = np.concatenate(
    [
        np.full(30, 0.015),  # Low volatility
        np.full(30, 0.035),  # High volatility
        np.full(30, 0.025),  # Medium
        np.full(30, 0.04),  # Very high
    ]
)
returns = np.random.normal(0.0005, 1, n_periods) * volatility + trend / n_periods
prices = 100 * np.cumprod(1 + returns)

# Calculate RSI using 14-period lookback
period = 14
delta = np.diff(prices)
gains = np.where(delta > 0, delta, 0)
losses = np.where(delta < 0, -delta, 0)

avg_gain = np.zeros(len(delta))
avg_loss = np.zeros(len(delta))
avg_gain[period - 1] = np.mean(gains[:period])
avg_loss[period - 1] = np.mean(losses[:period])

for i in range(period, len(delta)):
    avg_gain[i] = (avg_gain[i - 1] * (period - 1) + gains[i]) / period
    avg_loss[i] = (avg_loss[i - 1] * (period - 1) + losses[i]) / period

rs = np.divide(avg_gain, avg_loss, out=np.ones_like(avg_gain), where=avg_loss != 0)
rsi = 100 - (100 / (1 + rs))
rsi = rsi[period - 1 :]
rsi_dates = dates[period:]

df = pd.DataFrame({"date": rsi_dates, "rsi": rsi})

# Plot
fig, ax = plt.subplots(figsize=(16, 9), facecolor=PAGE_BG)
ax.set_facecolor(PAGE_BG)

# Shade overbought zone (70-100) — imprint red, semantic danger
ax.fill_between(df["date"], 70, 100, alpha=0.12, color="#AE3030")

# Shade oversold zone (0-30)
ax.fill_between(df["date"], 0, 30, alpha=0.12, color="#4467A3")

# Plot RSI line using brand color
ax.plot(df["date"], df["rsi"], color=BRAND, linewidth=3, label="RSI (14-period)")

# Add horizontal reference lines
ax.axhline(y=70, color=INK_SOFT, linestyle="--", linewidth=2, alpha=0.5)
ax.axhline(y=30, color=INK_SOFT, linestyle="--", linewidth=2, alpha=0.5)
ax.axhline(y=50, color=INK_SOFT, linestyle=":", linewidth=1.5, alpha=0.3)

# Set fixed y-axis from 0 to 100
ax.set_ylim(0, 100)
ax.set_xlim(df["date"].min(), df["date"].max())

# Labels and styling
ax.set_xlabel("Date", fontsize=20, color=INK)
ax.set_ylabel("RSI Value", fontsize=20, color=INK)
ax.set_title("indicator-rsi · matplotlib · anyplot.ai", fontsize=24, fontweight="medium", color=INK)
ax.tick_params(axis="both", labelsize=16, colors=INK_SOFT, labelcolor=INK_SOFT)

# Add text annotations for threshold levels
ax.text(df["date"].iloc[-1], 72, "Overbought", fontsize=13, color=INK_SOFT, ha="right", va="bottom")
ax.text(df["date"].iloc[-1], 28, "Oversold", fontsize=13, color=INK_SOFT, ha="right", va="top")

# Grid and legend
ax.grid(True, alpha=0.1, linewidth=0.8, color=INK)
ax.yaxis.grid(True, alpha=0.1, linewidth=0.8, color=INK)
ax.xaxis.grid(False)

leg = ax.legend(fontsize=16, loc="upper left")
if leg:
    leg.get_frame().set_facecolor(ELEVATED_BG)
    leg.get_frame().set_edgecolor(INK_SOFT)
    leg.get_frame().set_alpha(0.95)
    plt.setp(leg.get_texts(), color=INK_SOFT)

# Spine styling
for s in ("left", "bottom"):
    ax.spines[s].set_color(INK_SOFT)
ax.spines["top"].set_visible(False)
ax.spines["right"].set_visible(False)

plt.tight_layout()
plt.savefig(f"plot-{THEME}.png", dpi=300, bbox_inches="tight", facecolor=PAGE_BG)
