""" anyplot.ai
line-timeseries: Time Series Line Plot
Library: matplotlib 3.11.2 | Python 3.14.10
Quality: 82/100 | Updated: 2026-11-20
"""

import os

import matplotlib.dates as mdates
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Imprint palette: position 1 is the single series
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

# Columns: set these to your table's column names
DATE = "Date"  # role: date
TEMPERATURE = "Temperature (°C)"  # role: value

# Data: replace this block with your own table, for example df = pd.read_csv("temperature.csv", parse_dates=[DATE])
np.random.seed(42)
dates = pd.date_range(start="2024-01-01", end="2024-12-31", freq="D")
day_of_year = np.arange(len(dates))
seasonal = 15 * np.sin(2 * np.pi * (day_of_year - 80) / 365)
noise = np.random.randn(len(dates)) * 3
df = pd.DataFrame({DATE: dates, TEMPERATURE: 12 + seasonal + noise})

# Plot: reads only df and the constants above
fig, ax = plt.subplots(figsize=(8, 4.5), dpi=400, facecolor=PAGE_BG)
ax.set_facecolor(PAGE_BG)

ax.plot(df[DATE], df[TEMPERATURE], linewidth=1.8, color=IMPRINT_PALETTE[0], alpha=0.9)

# Calendar-aware ticks: one label per month, minor ticks mid-month
ax.xaxis.set_major_locator(mdates.MonthLocator())
ax.xaxis.set_major_formatter(mdates.DateFormatter("%b %Y"))
ax.xaxis.set_minor_locator(mdates.MonthLocator(bymonthday=15))
plt.setp(ax.xaxis.get_majorticklabels(), rotation=45, ha="right")

# Style
title = "Daily Temperature 2024 · line-timeseries · python · matplotlib · anyplot.ai"
ax.set_title(
    title, fontsize=max(8, round(12 * 67 / len(title))) if len(title) > 67 else 12, fontweight="medium", color=INK
)
ax.set_xlabel(DATE, fontsize=10, color=INK)
ax.set_ylabel(TEMPERATURE, fontsize=10, color=INK)
ax.tick_params(axis="both", labelsize=8, colors=INK_SOFT)

for spine in ("top", "right"):
    ax.spines[spine].set_visible(False)
for spine in ("left", "bottom"):
    ax.spines[spine].set_color(INK_SOFT)

ax.grid(True, alpha=0.10, which="major", color=INK)
ax.grid(True, alpha=0.05, which="minor", color=INK)

ax.set_xlim(df[DATE].min(), df[DATE].max())
ax.margins(y=0.05)

fig.subplots_adjust(left=0.08, right=0.97, top=0.92, bottom=0.2)
plt.savefig(f"plot-{THEME}.png", dpi=400, facecolor=PAGE_BG)
