"""anyplot.ai
line-stock-comparison: Stock Price Comparison Chart
Library: matplotlib 3.10.9 | Python 3.13.13
Quality: 89/100 | Updated: 2026-05-23
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
INK_MUTED = "#6B6A63" if THEME == "light" else "#A8A79F"

# Imprint palette: all eight positions in canonical order
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

# Constants
BASE = 100  # every series is rebased to this value on its first date
BENCHMARK = "SPY"  # the index the stocks are compared against

# Columns: set these to your table's column names
DATE = "Date"  # role: date
SYMBOL = "Symbol"  # role: symbol
PRICE = "Adjusted close (USD)"  # role: price

# Data: replace this block with your own table, for example df = pd.read_csv("prices.csv")
np.random.seed(42)
n_days = 252
dates = pd.date_range("2024-01-02", periods=n_days, freq="B")
stocks = {
    "AAPL": {"start": 185, "drift": 0.0008, "vol": 0.018},
    "GOOGL": {"start": 140, "drift": 0.0006, "vol": 0.020},
    "MSFT": {"start": 375, "drift": 0.0007, "vol": 0.016},
    "SPY": {"start": 475, "drift": 0.0004, "vol": 0.010},
}
frames = []
for name, params in stocks.items():
    returns = np.random.normal(params["drift"], params["vol"], n_days)
    frames.append(pd.DataFrame({DATE: dates, SYMBOL: name, PRICE: params["start"] * np.cumprod(1 + returns)}))
df = pd.concat(frames, ignore_index=True)

# Plot: reads only df and the constants above
table = df.pivot_table(index=DATE, columns=SYMBOL, values=PRICE, sort=False)
rebased = table / table.bfill().iloc[0] * BASE

fig, ax = plt.subplots(figsize=(8, 4.5), dpi=400, facecolor=PAGE_BG)
ax.set_facecolor(PAGE_BG)
ax.set_prop_cycle(color=IMPRINT_PALETTE)

for symbol in rebased.columns:
    # The benchmark gets a thicker line for visual hierarchy
    lw = 3.0 if symbol == BENCHMARK else 2.0
    ax.plot(rebased.index, rebased[symbol], label=symbol, linewidth=lw)

# Reference line at the common starting value
ax.axhline(y=BASE, color=INK_MUTED, linestyle="--", linewidth=1.0, alpha=0.7, zorder=1)

# Label the benchmark at its last value
if BENCHMARK in rebased.columns:
    bench = rebased[BENCHMARK].dropna()
    bench_color = ax.get_lines()[list(rebased.columns).index(BENCHMARK)].get_color()
    ax.annotate(
        "Benchmark",
        xy=(bench.index[-1], bench.iloc[-1]),
        xytext=(10, 0),
        textcoords="offset points",
        color=bench_color,
        fontsize=9,
        fontweight="bold",
        va="center",
    )

# Date formatting with major monthly ticks and minor biweekly ticks
ax.xaxis.set_major_locator(mdates.MonthLocator())
ax.xaxis.set_major_formatter(mdates.DateFormatter("%b '%y"))
ax.xaxis.set_minor_locator(mdates.WeekdayLocator(byweekday=0, interval=2))
fig.autofmt_xdate(rotation=30, ha="right")

# Style
ax.yaxis.grid(True, alpha=0.15, color=INK, linewidth=0.8)
ax.set_axisbelow(True)
ax.spines["top"].set_visible(False)
ax.spines["right"].set_visible(False)
ax.spines["left"].set_color(INK_SOFT)
ax.spines["bottom"].set_color(INK_SOFT)

ax.set_title(
    "line-stock-comparison · python · matplotlib · anyplot.ai", fontsize=12, fontweight="medium", color=INK, pad=10
)
ax.set_xlabel(DATE, fontsize=10, color=INK)
ax.set_ylabel(f"Rebased value (start = {BASE})", fontsize=10, color=INK)
ax.tick_params(axis="both", labelsize=8, colors=INK_SOFT)

leg = ax.legend(title=SYMBOL, fontsize=8, title_fontsize=8, loc="upper left", frameon=True)
leg.get_frame().set_facecolor(ELEVATED_BG)
leg.get_frame().set_edgecolor(INK_SOFT)
leg.get_frame().set_linewidth(0.5)
plt.setp(leg.get_texts(), color=INK_SOFT)
leg.get_title().set_color(INK_SOFT)

fig.subplots_adjust(left=0.09, right=0.87, top=0.92, bottom=0.14)
plt.savefig(f"plot-{THEME}.png", dpi=400, facecolor=PAGE_BG)
plt.close()
