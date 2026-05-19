""" anyplot.ai
indicator-ema: Exponential Moving Average (EMA) Indicator Chart
Library: matplotlib 3.10.9 | Python 3.13.13
Quality: 88/100 | Updated: 2026-05-19
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

# Okabe-Ito colors for EMAs
EMA_SHORT_COLOR = "#009E73"  # Okabe-Ito pos 1 — 12-day EMA
EMA_LONG_COLOR = "#D55E00"  # Okabe-Ito pos 2 — 26-day EMA
GOLDEN_COLOR = "#E69F00"  # Okabe-Ito pos 5 — bullish crossover
DEATH_COLOR = "#CC79A7"  # Okabe-Ito pos 4 — bearish crossover

# Data
np.random.seed(42)
n_days = 120

dates = pd.date_range("2024-01-02", periods=n_days, freq="B")
returns = np.random.normal(0.0005, 0.02, n_days)
price = 150 * np.cumprod(1 + returns)

df = pd.DataFrame({"date": dates, "close": price})
df["ema_12"] = df["close"].ewm(span=12, adjust=False).mean()
df["ema_26"] = df["close"].ewm(span=26, adjust=False).mean()

# Identify crossover signals
signal = np.sign(df["ema_12"].values - df["ema_26"].values)
crossover_idx = np.where(np.diff(signal))[0]

# Plot
fig, ax = plt.subplots(figsize=(16, 9), facecolor=PAGE_BG)
ax.set_facecolor(PAGE_BG)

# Shaded regime regions between EMA lines
ax.fill_between(
    df["date"],
    df["ema_12"],
    df["ema_26"],
    where=df["ema_12"] >= df["ema_26"],
    alpha=0.12,
    color=EMA_SHORT_COLOR,
    interpolate=True,
)
ax.fill_between(
    df["date"],
    df["ema_12"],
    df["ema_26"],
    where=df["ema_12"] < df["ema_26"],
    alpha=0.12,
    color=EMA_LONG_COLOR,
    interpolate=True,
)

# Price line (most prominent)
ax.plot(df["date"], df["close"], linewidth=2.5, color=INK, label="Price", alpha=0.85, zorder=3)

# EMA lines (slightly thinner per spec)
ax.plot(df["date"], df["ema_12"], linewidth=2, color=EMA_SHORT_COLOR, label="EMA 12", alpha=0.9, zorder=4)
ax.plot(df["date"], df["ema_26"], linewidth=2, color=EMA_LONG_COLOR, label="EMA 26", alpha=0.9, zorder=4)

# Crossover markers — golden cross (^) vs death cross (v)
for idx in crossover_idx:
    x_date = df["date"].iloc[idx]
    y_val = df["ema_12"].iloc[idx]
    is_golden = signal[idx] < 0  # EMA12 was below, now crossing above
    ax.scatter(
        x_date,
        y_val,
        s=280,
        color=GOLDEN_COLOR if is_golden else DEATH_COLOR,
        marker="^" if is_golden else "v",
        zorder=6,
        edgecolors=PAGE_BG,
        linewidths=2,
    )

# Proxy artists for crossover legend entries
ax.scatter([], [], s=200, color=GOLDEN_COLOR, marker="^", edgecolors=PAGE_BG, linewidths=2, label="Golden Cross")
ax.scatter([], [], s=200, color=DEATH_COLOR, marker="v", edgecolors=PAGE_BG, linewidths=2, label="Death Cross")

# Style
ax.set_xlabel("Date", fontsize=20, color=INK)
ax.set_ylabel("Price (USD)", fontsize=20, color=INK)
ax.set_title("indicator-ema · python · matplotlib · anyplot.ai", fontsize=24, fontweight="medium", color=INK)
ax.tick_params(axis="both", labelsize=16, colors=INK_SOFT, labelcolor=INK_SOFT)

ax.spines["top"].set_visible(False)
ax.spines["right"].set_visible(False)
for s in ("left", "bottom"):
    ax.spines[s].set_color(INK_SOFT)

ax.yaxis.grid(True, alpha=0.10, linewidth=0.8, color=INK)

leg = ax.legend(fontsize=16, loc="upper right", framealpha=0.9)
leg.get_frame().set_facecolor(ELEVATED_BG)
leg.get_frame().set_edgecolor(INK_SOFT)
plt.setp(leg.get_texts(), color=INK_SOFT)

fig.autofmt_xdate(rotation=30)

plt.tight_layout()
plt.savefig(f"plot-{THEME}.png", dpi=300, bbox_inches="tight", facecolor=PAGE_BG)
