""" anyplot.ai
line-timeseries: Time Series Line Plot
Library: seaborn 0.13.2 | Python 3.13.13
Quality: 88/100 | Updated: 2026-05-09
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
BRAND = "#009E73"  # Okabe-Ito position 1

# Theme-adaptive seaborn configuration
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
        "legend.facecolor": ELEVATED_BG,
        "legend.edgecolor": INK_SOFT,
    },
)

# Data: Daily temperature readings over 3 months
np.random.seed(42)
dates = pd.date_range(start="2024-01-01", periods=90, freq="D")

day_of_year = np.arange(90)
base_temp = 5 + 10 * np.sin(2 * np.pi * (day_of_year + 10) / 365)
noise = np.random.randn(90) * 3
temperature = base_temp + noise

df = pd.DataFrame({"Date": dates, "Temperature (°C)": temperature})

# Plot
fig, ax = plt.subplots(figsize=(16, 9), facecolor=PAGE_BG)

sns.lineplot(data=df, x="Date", y="Temperature (°C)", color=BRAND, linewidth=3, ax=ax, errorbar=("ci", 95))

# Style
ax.set_xlabel("Date", fontsize=20, color=INK)
ax.set_ylabel("Temperature (°C)", fontsize=20, color=INK)
ax.set_title("line-timeseries · seaborn · anyplot.ai", fontsize=24, fontweight="medium", color=INK)
ax.tick_params(axis="both", labelsize=16, colors=INK_SOFT)

# Smart date formatting
ax.xaxis.set_major_locator(mdates.MonthLocator())
ax.xaxis.set_major_formatter(mdates.DateFormatter("%b %Y"))
ax.xaxis.set_minor_locator(mdates.WeekdayLocator(byweekday=mdates.MO))

# Rotate labels to prevent overlap
plt.setp(ax.get_xticklabels(), rotation=45, ha="right")

# Grid on both axes for readability
ax.grid(True, alpha=0.15, linewidth=0.8, color=INK)

# Remove top and right spines
ax.spines["top"].set_visible(False)
ax.spines["right"].set_visible(False)
for spine in ["left", "bottom"]:
    ax.spines[spine].set_color(INK_SOFT)

plt.tight_layout()
plt.savefig(f"plot-{THEME}.png", dpi=300, bbox_inches="tight", facecolor=PAGE_BG)
