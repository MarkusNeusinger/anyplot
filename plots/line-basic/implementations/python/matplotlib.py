""" anyplot.ai
line-basic: Basic Line Plot
Library: matplotlib 3.11.2 | Python 3.14.9
Quality: 83/100 | Updated: 2026-11-01
"""

import os

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Imprint palette: single series uses the brand green
BRAND = "#009E73"

# Columns: set these to your table's column names
MONTH = "Month"  # role: x
TEMPERATURE = "Temperature (°C)"  # role: y

# Data: replace this block with your own table, for example df = pd.read_csv("temperature.csv")
np.random.seed(42)
month_numbers = np.arange(1, 13)
base_temp = 15 + 12 * np.sin((month_numbers - 4) * np.pi / 6)
all_years = base_temp + np.random.randn(5, 12) * 2.5
df = pd.DataFrame(
    {
        MONTH: ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"],
        TEMPERATURE: all_years.mean(axis=0),
    }
)

# Plot
fig, ax = plt.subplots(figsize=(8, 4.5), dpi=400, facecolor=PAGE_BG)
ax.set_facecolor(PAGE_BG)

ax.plot(
    df[MONTH],
    df[TEMPERATURE],
    linewidth=2.5,
    color=BRAND,
    marker="o",
    markersize=6,
    markerfacecolor=PAGE_BG,
    markeredgecolor=BRAND,
    markeredgewidth=1.5,
)

# Style
ax.tick_params(axis="both", labelsize=8, labelcolor=INK_SOFT, length=0)
ax.set_xlabel(MONTH, fontsize=10, color=INK)
ax.set_ylabel(TEMPERATURE, fontsize=10, color=INK)
ax.set_title(
    "Monthly Temperature Trend · line-basic · matplotlib · anyplot.ai", fontsize=12, fontweight="medium", color=INK
)

ax.spines["top"].set_visible(False)
ax.spines["right"].set_visible(False)
for s in ("left", "bottom"):
    ax.spines[s].set_color(INK_SOFT)

ax.yaxis.grid(True, alpha=0.18, linewidth=0.8, color=INK)

fig.subplots_adjust(left=0.08, right=0.97, top=0.9, bottom=0.12)
plt.savefig(f"plot-{THEME}.png", dpi=400, facecolor=PAGE_BG)
