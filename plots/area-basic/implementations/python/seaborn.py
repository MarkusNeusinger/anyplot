""" anyplot.ai
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
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
INK_MUTED = "#6B6A63" if THEME == "light" else "#A8A79F"
BRAND = "#009E73"

# Data - daily website visitors over a month
np.random.seed(42)
dates = pd.date_range(start="2024-03-01", periods=30, freq="D")
base_visitors = 8000
trend = np.linspace(0, 2000, 30)
weekly_pattern = np.array([1.0, 1.1, 1.15, 1.2, 1.1, 0.7, 0.65] * 5)[:30]
noise = np.random.randn(30) * 350
visitors = (base_visitors + trend) * weekly_pattern + noise
visitors[9:12] *= 0.22  # Planned maintenance window (days 10–12)
visitors = np.maximum(visitors, 100)

df = pd.DataFrame({"date": dates, "visitors": visitors})
avg_visitors = df["visitors"].mean()
y_max = df["visitors"].max() * 1.18

# Configure seaborn theme (theme-adaptive chrome)
sns.set_theme(
    style="white",
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

# Layered gradient fill using seaborn's light_palette — 3 layers at higher alpha
# for stronger area visual weight than the previous 5-layer faint approach
palette_colors = sns.light_palette(BRAND, n_colors=5)
for i in range(3):
    frac = (i + 1) / 3
    ax.fill_between(df["date"], 0, df["visitors"] * frac, color=palette_colors[i + 2], alpha=0.28, linewidth=0)

# Seaborn lineplot for the area boundary line
sns.lineplot(data=df, x="date", y="visitors", ax=ax, color=BRAND, linewidth=2.5)

# Annotate the scheduled maintenance dip (days 10–12)
maint_idx = 10
maint_val = df["visitors"].iloc[maint_idx]
ax.annotate(
    "Scheduled\nmaintenance",
    xy=(df["date"].iloc[maint_idx], maint_val + 80),
    xytext=(df["date"].iloc[maint_idx + 6], maint_val + 4200),
    fontsize=8,
    fontweight="semibold",
    color=INK,
    arrowprops={"arrowstyle": "->", "color": INK_SOFT, "lw": 1.2, "connectionstyle": "arc3,rad=0.2"},
    ha="center",
    va="bottom",
)

# Monthly average reference line
ax.axhline(y=avg_visitors, color=INK_SOFT, linestyle="--", linewidth=1.0, alpha=0.6, zorder=1)
ax.text(
    df["date"].iloc[-1],
    avg_visitors + y_max * 0.012,
    f"Avg: {avg_visitors:,.0f}",
    fontsize=8,
    color=INK_MUTED,
    ha="right",
    va="bottom",
    fontstyle="italic",
)

# Labels and title
title = "area-basic · python · seaborn · anyplot.ai"
n = len(title)
ratio = 67 / n if n > 67 else 1.0
title_fontsize = max(8, round(12 * ratio))

ax.set_xlabel("Date", fontsize=10, color=INK)
ax.set_ylabel("Visitors / day", fontsize=10, color=INK)
ax.set_title(title, fontsize=title_fontsize, fontweight="medium", color=INK, pad=8)
ax.tick_params(axis="both", labelsize=8, colors=INK_SOFT)

# Spine, grid, and axes styling
sns.despine(ax=ax)
ax.yaxis.grid(True, alpha=0.15, linewidth=0.8, color=INK)
ax.set_axisbelow(True)
ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f"{x:,.0f}"))
ax.xaxis.set_major_locator(mdates.WeekdayLocator(byweekday=mdates.MO))
ax.xaxis.set_minor_locator(mdates.DayLocator())
ax.xaxis.set_major_formatter(mdates.DateFormatter("%b %d"))
plt.setp(ax.get_xticklabels(), rotation=30, ha="right")
ax.set_ylim(bottom=0, top=y_max)

plt.tight_layout()
plt.savefig(f"plot-{THEME}.png", dpi=400, facecolor=PAGE_BG)
