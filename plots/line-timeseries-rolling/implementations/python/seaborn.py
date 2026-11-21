"""anyplot.ai
line-timeseries-rolling: Time Series with Rolling Average Overlay
Library: seaborn 0.13.2 | Python 3.13.13
Quality: pending | Updated: 2026-05-13
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

# Imprint palette: canonical order, first series always #009E73
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

# Constants
WINDOW = 24  # rolling window in observations (hours)

# Columns: set these to your table's column names
TIME = "Time"  # role: date
LATENCY = "Response time (ms)"  # role: value

# Data: replace this block with your own table, for example df = pd.read_csv("latency.csv")
# Hourly API response time over two weeks, with a drop after a mid-period release
rng = np.random.default_rng(7)
hours = pd.date_range(start="2025-03-03", periods=336, freq="h")
hour_of_day = hours.hour.to_numpy()
daily_load = 25 * np.sin(2 * np.pi * (hour_of_day - 9) / 24)
level = np.where(np.arange(len(hours)) < 168, 190.0, 125.0)
spikes = rng.exponential(18, len(hours)) * (rng.random(len(hours)) < 0.12)
df = pd.DataFrame({TIME: hours, LATENCY: level + daily_load + rng.normal(0, 14, len(hours)) + spikes})

# Plot: reads only df and the constants above
# min_periods=WINDOW leaves the average empty until the window is full
rolling = df[LATENCY].rolling(window=WINDOW, min_periods=WINDOW).mean()

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
        "legend.facecolor": ELEVATED_BG,
        "legend.edgecolor": INK_SOFT,
    },
)

fig, ax = plt.subplots(figsize=(8, 4.5), dpi=400, facecolor=PAGE_BG)

sns.lineplot(
    data=df, x=TIME, y=LATENCY, ax=ax, color=IMPRINT_PALETTE[0], alpha=0.65, linewidth=0.9, label="Raw response time"
)
sns.lineplot(
    x=df[TIME], y=rolling, ax=ax, color=IMPRINT_PALETTE[1], linewidth=2.2, label=f"{WINDOW}-hour rolling average"
)

# Style
ax.set_title("line-timeseries-rolling · python · seaborn · anyplot.ai", fontsize=12, fontweight="medium", color=INK)
ax.set_xlabel(TIME, fontsize=10, color=INK)
ax.set_ylabel(LATENCY, fontsize=10, color=INK)
ax.tick_params(axis="both", labelsize=8, colors=INK_SOFT)
ax.xaxis.set_major_formatter(mdates.DateFormatter("%b %d"))
ax.grid(True, alpha=0.15, linewidth=0.6, axis="both")
ax.legend(fontsize=8, loc="upper right", framealpha=0.9, edgecolor=INK_SOFT)
sns.despine(ax=ax)
fig.tight_layout()

plt.savefig(f"plot-{THEME}.png", dpi=400, facecolor=PAGE_BG)
