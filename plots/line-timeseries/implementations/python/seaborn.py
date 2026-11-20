"""anyplot.ai
line-timeseries: Time Series Line Plot
Library: seaborn 0.13.2 | Python 3.13.13
Quality: pending | Updated: 2026-05-09
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

# Imprint palette: single series uses position 1
BRAND = "#009E73"

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
    },
)

# Columns: set these to your table's column names
DATE = "Date"  # role: date
TEMPERATURE = "Temperature (°C)"  # role: value

# Data: replace this block with your own table, for example df = pd.read_csv("temperature.csv", parse_dates=[DATE])
np.random.seed(42)
n_days = 90
day_of_year = np.arange(n_days)
base_temp = 5 + 10 * np.sin(2 * np.pi * (day_of_year + 10) / 365)
df = pd.DataFrame(
    {
        DATE: pd.date_range(start="2024-01-01", periods=n_days, freq="D"),
        TEMPERATURE: base_temp + np.random.randn(n_days) * 3,
    }
)

# Plot
fig, ax = plt.subplots(figsize=(8, 4.5), dpi=400, facecolor=PAGE_BG)

sns.lineplot(data=df, x=DATE, y=TEMPERATURE, color=BRAND, linewidth=2.5, errorbar=None, ax=ax)

# Style
ax.set_xlabel(DATE, fontsize=10)
ax.set_ylabel(TEMPERATURE, fontsize=10)
ax.set_title("line-timeseries · python · seaborn · anyplot.ai", fontsize=12, fontweight="medium")
ax.tick_params(axis="both", labelsize=8)

# Calendar-aligned ticks: months labelled, Mondays as minor ticks
ax.xaxis.set_major_locator(mdates.MonthLocator())
ax.xaxis.set_major_formatter(mdates.DateFormatter("%b %Y"))
ax.xaxis.set_minor_locator(mdates.WeekdayLocator(byweekday=mdates.MO))

# Grid on both axes, subordinate to the line
ax.grid(True, alpha=0.15, linewidth=0.8, color=INK)

sns.despine(ax=ax)
fig.tight_layout()
fig.savefig(f"plot-{THEME}.png", dpi=400, facecolor=PAGE_BG)
