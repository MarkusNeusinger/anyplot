""" anyplot.ai
line-filled: Filled Line Plot
Library: matplotlib 3.11.2 | Python 3.14.10
Quality: 85/100 | Updated: 2026-11-09
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

# Imprint palette: single series in brand green
BRAND = "#009E73"

# Columns: set these to your table's column names
MONTH = "Month (2025)"  # role: x
VISITORS = "Website visitors (thousands)"  # role: y

# Data: replace this block with your own table, for example df = pd.read_csv("traffic.csv")
# Monthly website traffic with a summer peak
np.random.seed(42)
month_number = np.arange(1, 13)
traffic = 50000 + 15000 * np.sin((month_number - 3) * np.pi / 6) + np.random.normal(0, 3000, 12)
df = pd.DataFrame({MONTH: pd.date_range("2025-01-01", periods=12, freq="MS"), VISITORS: np.maximum(traffic, 0) / 1000})

# Plot: reads only df and the constants above
series = df[[MONTH, VISITORS]].dropna().sort_values(MONTH)

fig, ax = plt.subplots(figsize=(8, 4.5), dpi=400, facecolor=PAGE_BG, layout="constrained")
ax.set_facecolor(PAGE_BG)
ax.fill_between(series[MONTH], series[VISITORS], color=BRAND, alpha=0.3, linewidth=0)
ax.plot(series[MONTH], series[VISITORS], color=BRAND, linewidth=2.5, solid_joinstyle="round")

# Style
ax.set_title("line-filled · python · matplotlib · anyplot.ai", fontsize=12, fontweight="bold", color=INK)
ax.set_xlabel(MONTH, fontsize=10, color=INK)
ax.set_ylabel(VISITORS, fontsize=10, color=INK)
ax.set_xlim(series[MONTH].min(), series[MONTH].max())
ax.set_ylim(0, series[VISITORS].max() * 1.1)
if pd.api.types.is_datetime64_any_dtype(series[MONTH]):
    ax.xaxis.set_major_locator(mdates.MonthLocator())
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%b"))
ax.tick_params(axis="both", labelsize=8, colors=INK_SOFT)
ax.yaxis.grid(True, alpha=0.15, color=INK, linewidth=0.6)
ax.set_axisbelow("line")  # gridlines above the fill, below the line
for side in ("top", "right"):
    ax.spines[side].set_visible(False)
for side in ("left", "bottom"):
    ax.spines[side].set_color(INK_SOFT)

plt.savefig(f"plot-{THEME}.png", dpi=400, facecolor=PAGE_BG)
