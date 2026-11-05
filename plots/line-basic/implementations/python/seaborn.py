"""anyplot.ai
line-basic: Basic Line Plot
Library: seaborn 0.13.2 | Python 3.13.13
Quality: 91/100 | Updated: 2026-04-29
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
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Imprint palette: single series uses the first position
BRAND = "#009E73"

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
    },
)

# Columns: set these to your table's column names
DATE = "Date"  # role: x
VISITORS = "Daily visitors (thousands)"  # role: y

# Data: replace this block with your own table, for example df = pd.read_csv("visitors.csv")
rng = np.random.default_rng(7)
days = pd.date_range("2025-01-01", periods=120, freq="D")
trend = 12 + 0.09 * np.arange(len(days))
weekend_dip = np.where(days.day_of_week >= 5, -2.2, 0.0)
noise = rng.normal(0, 0.9, len(days))
df = pd.DataFrame({DATE: days, VISITORS: trend + weekend_dip + noise})

# Plot
fig, ax = plt.subplots(figsize=(8, 4.5), dpi=400, facecolor=PAGE_BG)
ax.set_facecolor(PAGE_BG)

sns.lineplot(data=df, x=DATE, y=VISITORS, ax=ax, color=BRAND, linewidth=2, marker="o", markersize=3.5)

# Style
ax.set_title("Daily Website Visitors · line-basic · python · seaborn · anyplot.ai", fontsize=12, fontweight="medium")
ax.set_xlabel(DATE, fontsize=10)
ax.set_ylabel(VISITORS, fontsize=10)
ax.tick_params(axis="both", labelsize=8)
ax.xaxis.set_major_locator(mdates.MonthLocator())
ax.xaxis.set_major_formatter(mdates.DateFormatter("%b %Y"))
ax.yaxis.grid(True, alpha=0.10, linewidth=0.8)
sns.despine(ax=ax)

plt.savefig(f"plot-{THEME}.png", dpi=400, facecolor=PAGE_BG)
