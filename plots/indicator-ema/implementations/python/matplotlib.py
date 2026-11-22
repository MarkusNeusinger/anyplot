"""anyplot.ai
indicator-ema: Exponential Moving Average (EMA) Indicator Chart
Library: matplotlib 3.10.9 | Python 3.13.13
Quality: pending | Updated: 2026-05-19
"""

import os

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.dates import DateFormatter, MonthLocator


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
INK_MUTED = "#6B6A63" if THEME == "light" else "#A8A79F"

# Imprint palette: all eight positions in canonical order
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

# Constants
SHORT_SPAN = 12  # days in the fast EMA
LONG_SPAN = 26  # days in the slow EMA

# Columns: set these to your table's column names
DATE = "Date"  # role: date
CLOSE = "Close price (USD)"  # role: close

# Data: replace this block with your own table, for example df = pd.read_csv("prices.csv")
np.random.seed(42)
n_days = 120
df = pd.DataFrame(
    {
        DATE: pd.date_range("2024-01-02", periods=n_days, freq="B"),
        CLOSE: 150 * np.cumprod(1 + np.random.normal(0.0005, 0.02, n_days)),
    }
)

# Plot: reads only df and the constants above
ema_short = df[CLOSE].ewm(span=SHORT_SPAN, adjust=False).mean()
ema_long = df[CLOSE].ewm(span=LONG_SPAN, adjust=False).mean()
short_label = f"EMA {SHORT_SPAN}"
long_label = f"EMA {LONG_SPAN}"

# Crossover signals: index of the last bar before the sign of (short - long) flips
signal = np.sign(ema_short.to_numpy() - ema_long.to_numpy())
crossover_idx = np.where(np.diff(signal))[0]
golden_idx = [i for i in crossover_idx if signal[i] < 0]  # short EMA moves above long EMA
death_idx = [i for i in crossover_idx if signal[i] > 0]  # short EMA moves below long EMA

short_color, long_color, golden_color, death_color = IMPRINT_PALETTE[:4]

fig, ax = plt.subplots(figsize=(8, 4.5), dpi=400, facecolor=PAGE_BG)
ax.set_facecolor(PAGE_BG)

# Shaded regime between the two EMAs
for mask, color in ((ema_short >= ema_long, short_color), (ema_short < ema_long, long_color)):
    ax.fill_between(df[DATE], ema_short, ema_long, where=mask, alpha=0.12, color=color, interpolate=True, linewidth=0)

# Price line (most prominent), EMAs slightly thinner
ax.plot(df[DATE], df[CLOSE], linewidth=2.5, color=INK, label="Price", alpha=0.85, zorder=3)
ax.plot(df[DATE], ema_short, linewidth=2, color=short_color, label=short_label, zorder=4)
ax.plot(df[DATE], ema_long, linewidth=2, color=long_color, label=long_label, zorder=4)

# Crossover markers, placed on the short EMA at the bar where the lines cross
for idxs, color, marker, label in (
    (golden_idx, golden_color, "^", "Golden Cross"),
    (death_idx, death_color, "v", "Death Cross"),
):
    ax.scatter(
        df[DATE].iloc[idxs],
        ema_short.iloc[idxs],
        s=60,
        color=color,
        marker=marker,
        zorder=6,
        edgecolors=PAGE_BG,
        linewidths=0.8,
        label=label,
    )

# Callouts: the first golden and the first death cross, if the data has them
for idxs, color, text, offset in (
    (golden_idx, golden_color, "Golden\nCross", (8, -42)),
    (death_idx, death_color, "Death\nCross", (44, 14)),
):
    if idxs:
        ax.annotate(
            text,
            xy=(df[DATE].iloc[idxs[0]], ema_short.iloc[idxs[0]]),
            xytext=offset,
            textcoords="offset points",
            fontsize=8,
            color=color,
            fontweight="semibold",
            ha="center",
            arrowprops={"arrowstyle": "->", "color": color, "lw": 1.0},
            bbox={"facecolor": ELEVATED_BG, "edgecolor": color, "alpha": 0.9, "boxstyle": "round,pad=0.3"},
            zorder=8,
        )

# Style
ax.set_xlabel(DATE, fontsize=10, color=INK)
ax.set_ylabel(CLOSE, fontsize=10, color=INK)
ax.set_title("indicator-ema · python · matplotlib · anyplot.ai", fontsize=12, fontweight="medium", color=INK, pad=18)
ax.text(
    0.5,
    1.012,
    f"EMA crossover signals with regime shading  |  {len(df)} trading days  |  periods: {SHORT_SPAN} & {LONG_SPAN}",
    transform=ax.transAxes,
    fontsize=7,
    color=INK_MUTED,
    ha="center",
    va="bottom",
)
ax.tick_params(axis="both", labelsize=8, colors=INK_SOFT, labelcolor=INK_SOFT, length=0)
for side in ("top", "right"):
    ax.spines[side].set_visible(False)
for side in ("left", "bottom"):
    ax.spines[side].set_color(INK_SOFT)
ax.yaxis.grid(True, alpha=0.10, linewidth=0.8, color=INK)

ax.xaxis.set_major_locator(MonthLocator())
ax.xaxis.set_major_formatter(DateFormatter("%b %Y"))
plt.setp(ax.get_xticklabels(), rotation=30, ha="right")

leg = ax.legend(fontsize=8, loc="upper right", framealpha=0.9, ncol=2)
leg.get_frame().set_facecolor(ELEVATED_BG)
leg.get_frame().set_edgecolor(INK_SOFT)
plt.setp(leg.get_texts(), color=INK_SOFT)

fig.subplots_adjust(left=0.08, right=0.98, top=0.88, bottom=0.17)
plt.savefig(f"plot-{THEME}.png", dpi=400, facecolor=PAGE_BG)
