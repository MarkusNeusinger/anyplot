""" anyplot.ai
line-timeseries-rolling: Time Series with Rolling Average Overlay
Library: matplotlib 3.11.2 | Python 3.14.10
Quality: 82/100 | Updated: 2026-11-21
"""

import os

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Imprint palette: all eight positions in canonical order
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

# Constants
WINDOW = 7  # rolling window length in observations (days)

# Columns: set these to your table's column names
DATE = "Date"  # role: date
TEMPERATURE = "Temperature (°C)"  # role: value

# Data: replace this block with your own table, for example df = pd.read_csv("readings.csv")
np.random.seed(42)
days = np.arange(180)
df = pd.DataFrame(
    {
        DATE: pd.date_range("2024-01-01", periods=180, freq="D"),
        TEMPERATURE: 5 + 15 * np.sin(2 * np.pi * (days - 30) / 365) + np.random.normal(0, 3, 180),
    }
)

# Plot: reads only df and the constants above
rolling = df[TEMPERATURE].rolling(window=WINDOW, center=True).mean()
raw_label = "Raw Data"
rolling_label = f"Rolling Average ({WINDOW}-day)"

fig, ax = plt.subplots(figsize=(8, 4.5), dpi=400, facecolor=PAGE_BG)
ax.set_facecolor(PAGE_BG)

# Raw data: thin, semi-transparent line that recedes behind the average
ax.plot(df[DATE], df[TEMPERATURE], linewidth=0.8, alpha=0.5, color=IMPRINT_PALETTE[1], label=raw_label)

# Rolling average: prominent line, shorter than the raw series (window must fill first)
ax.plot(df[DATE], rolling, linewidth=2.5, color=IMPRINT_PALETTE[0], label=rolling_label)

# Style
ax.set_title("line-timeseries-rolling · python · matplotlib · anyplot.ai", fontsize=12, fontweight="medium", color=INK)
ax.set_xlabel(DATE, fontsize=10, color=INK)
ax.set_ylabel(TEMPERATURE, fontsize=10, color=INK)
ax.tick_params(axis="both", labelsize=8, colors=INK_SOFT)
for label in ax.get_xticklabels():
    label.set_rotation(30)
    label.set_ha("right")

ax.spines["top"].set_visible(False)
ax.spines["right"].set_visible(False)
for s in ("left", "bottom"):
    ax.spines[s].set_color(INK_SOFT)

ax.grid(True, axis="both", alpha=0.15, linewidth=0.8, color=INK)

leg = ax.legend(fontsize=8, loc="upper left")
leg.get_frame().set_facecolor(ELEVATED_BG)
leg.get_frame().set_edgecolor(INK_SOFT)
plt.setp(leg.get_texts(), color=INK_SOFT)

fig.tight_layout()
plt.savefig(f"plot-{THEME}.png", dpi=400, facecolor=PAGE_BG)
