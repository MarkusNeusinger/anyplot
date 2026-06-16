""" anyplot.ai
line-timeseries-rolling: Time Series with Rolling Average Overlay
Library: matplotlib 3.10.9 | Python 3.13.13
Quality: 92/100 | Updated: 2026-05-13
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

# Data - Daily temperature readings with 7-day rolling average
np.random.seed(42)

# Generate 180 days of temperature data (6 months)
dates = pd.date_range("2024-01-01", periods=180, freq="D")

# Create seasonal temperature pattern with noise
# Base seasonal pattern: winter -> spring -> summer
day_of_year = np.arange(180)
seasonal = 5 + 15 * np.sin(2 * np.pi * (day_of_year - 30) / 365)
noise = np.random.normal(0, 3, 180)
temperature = seasonal + noise

# Create DataFrame and calculate rolling average
df = pd.DataFrame({"date": dates, "temperature": temperature})
df["rolling_avg"] = df["temperature"].rolling(window=7, center=True).mean()

# Plot
fig, ax = plt.subplots(figsize=(16, 9), facecolor=PAGE_BG)
ax.set_facecolor(PAGE_BG)

# Raw data - thin, semi-transparent line (secondary Okabe-Ito color)
ax.plot(df["date"], df["temperature"], linewidth=1, alpha=0.4, color="#C475FD", label="Daily Temperature")

# Rolling average - prominent smooth line (brand green)
ax.plot(df["date"], df["rolling_avg"], linewidth=3.5, color="#009E73", label="7-Day Rolling Average")

# Labels and styling
ax.set_xlabel("Date", fontsize=20, color=INK)
ax.set_ylabel("Temperature (°C)", fontsize=20, color=INK)
ax.set_title("line-timeseries-rolling · matplotlib · anyplot.ai", fontsize=24, fontweight="medium", color=INK)
ax.tick_params(axis="both", labelsize=16, colors=INK_SOFT)

# Spine styling
ax.spines["top"].set_visible(False)
ax.spines["right"].set_visible(False)
for s in ("left", "bottom"):
    ax.spines[s].set_color(INK_SOFT)

# Grid styling
ax.grid(True, alpha=0.1, linewidth=0.8, color=INK, axis="both")

# Legend styling
leg = ax.legend(fontsize=16, loc="upper left")
if leg:
    leg.get_frame().set_facecolor(ELEVATED_BG)
    leg.get_frame().set_edgecolor(INK_SOFT)
    plt.setp(leg.get_texts(), color=INK_SOFT)

# Format x-axis dates
fig.autofmt_xdate(rotation=30)

plt.tight_layout()
plt.savefig(f"plot-{THEME}.png", dpi=300, bbox_inches="tight", facecolor=PAGE_BG)
