"""anyplot.ai
area-basic: Basic Area Chart
Library: seaborn 0.13.2 | Python 3.13.13
Quality: 90/100 | Updated: 2026-05-28
"""

import os

import matplotlib.dates as mdates
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import numpy as np
import pandas as pd
import seaborn as sns


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Imprint palette: the first position is the single series
BRAND = "#009E73"

# Columns: set these to your table's column names
DATE = "Date"  # role: x
VISITORS = "Visitors / day"  # role: y

# Data: replace this block with your own table, for example df = pd.read_csv("traffic.csv")
np.random.seed(42)
dates = pd.date_range(start="2024-03-01", periods=30, freq="D")
base_visitors = 8000
trend = np.linspace(0, 2000, 30)
weekly_pattern = np.array([1.0, 1.1, 1.15, 1.2, 1.1, 0.7, 0.65] * 5)[:30]
noise = np.random.randn(30) * 350
visitors = (base_visitors + trend) * weekly_pattern + noise
visitors[9:12] *= 0.22  # Planned maintenance window (days 10-12)
visitors = np.maximum(visitors, 100)
df = pd.DataFrame({DATE: dates, VISITORS: visitors})

# Plot: reads only df and the constants above
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
        "grid.alpha": 0.15,
        "axes.spines.top": False,
        "axes.spines.right": False,
    },
)

fig, ax = plt.subplots(figsize=(8, 4.5), dpi=400, facecolor=PAGE_BG)
ax.set_facecolor(PAGE_BG)

# Layered gradient fill from seaborn's light_palette: three tints fading toward the baseline
palette_colors = sns.light_palette(BRAND, n_colors=5)
for i in range(3):
    frac = (i + 1) / 3
    ax.fill_between(df[DATE], 0, df[VISITORS] * frac, color=palette_colors[i + 2], alpha=0.28, linewidth=0)

# Solid top edge
sns.lineplot(data=df, x=DATE, y=VISITORS, ax=ax, color=BRAND, linewidth=2.5)

# Title: mandated format, font size shrinks for long titles
title = "area-basic · python · seaborn · anyplot.ai"
n = len(title)
ratio = 67 / n if n > 67 else 1.0
title_fontsize = max(8, round(12 * ratio))

ax.set_xlabel(DATE, fontsize=10, color=INK)
ax.set_ylabel(VISITORS, fontsize=10, color=INK)
ax.set_title(title, fontsize=title_fontsize, fontweight="medium", color=INK, pad=8)
ax.tick_params(axis="both", labelsize=8, colors=INK_SOFT)

sns.despine(ax=ax)
ax.yaxis.grid(True, alpha=0.15, linewidth=0.8, color=INK)
ax.set_axisbelow(True)
ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f"{x:,.0f}"))
ax.xaxis.set_major_locator(mdates.WeekdayLocator(byweekday=mdates.MO))
ax.xaxis.set_minor_locator(mdates.DayLocator())
ax.xaxis.set_major_formatter(mdates.DateFormatter("%b %d"))
plt.setp(ax.get_xticklabels(), rotation=30, ha="right")
ax.set_ylim(bottom=0, top=df[VISITORS].max() * 1.08)

plt.tight_layout()
plt.savefig(f"plot-{THEME}.png", dpi=400, facecolor=PAGE_BG)
