""" anyplot.ai
subplot-grid: Subplot Grid Layout
Library: seaborn 0.13.2 | Python 3.13.13
Quality: 92/100 | Updated: 2026-05-13
"""

import os

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

# Okabe-Ito palette
IMPRINT = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477"]

# Apply theme to seaborn
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
        "legend.facecolor": ELEVATED_BG,
        "legend.edgecolor": INK_SOFT,
    },
)

# Data - Environmental monitoring scenario
np.random.seed(42)

# Time series: 48 hours of hourly readings
hours = np.arange(48)
dates = pd.date_range("2024-03-15", periods=48, freq="h")

# Temperature readings (Celsius) - realistic pattern with daily cycle
base_temp = 15 + 8 * np.sin(np.pi * hours / 24)
temperature = base_temp + np.random.normal(0, 0.8, 48)

# Humidity readings (%)
base_humidity = 60 + 15 * np.sin(np.pi * (hours - 6) / 24)
humidity = base_humidity + np.random.normal(0, 3, 48)

# Air quality index (AQI)
aqi = 40 + 20 * np.abs(np.sin(np.pi * hours / 48)) + np.random.normal(0, 2, 48)

# Pressure readings (hPa)
pressure = 1013 + np.cumsum(np.random.normal(0, 0.1, 48))

# Create DataFrame
df = pd.DataFrame(
    {
        "Hour": hours,
        "DateTime": dates,
        "Temperature": temperature,
        "Humidity": humidity,
        "AQI": aqi,
        "Pressure": pressure,
    }
)

# Create 2x2 subplot grid
fig, axes = plt.subplots(2, 2, figsize=(16, 9), facecolor=PAGE_BG)

# Subplot 1: Temperature Time Series (top-left)
ax1 = axes[0, 0]
sns.lineplot(data=df, x="Hour", y="Temperature", ax=ax1, color=IMPRINT[0], linewidth=3)
ax1.set_title("Temperature Over Time", fontsize=24, fontweight="medium", color=INK)
ax1.set_xlabel("Hours Since Start", fontsize=20, color=INK)
ax1.set_ylabel("Temperature (°C)", fontsize=20, color=INK)
ax1.tick_params(axis="both", labelsize=16, colors=INK_SOFT)
ax1.spines["top"].set_visible(False)
ax1.spines["right"].set_visible(False)
ax1.yaxis.grid(True, alpha=0.10, linewidth=0.8, color=INK)

# Subplot 2: Humidity Distribution (top-right)
ax2 = axes[0, 1]
sns.histplot(data=df, x="Humidity", bins=15, ax=ax2, color=IMPRINT[1], alpha=0.7, edgecolor=PAGE_BG)
ax2.set_title("Humidity Distribution", fontsize=24, fontweight="medium", color=INK)
ax2.set_xlabel("Humidity (%)", fontsize=20, color=INK)
ax2.set_ylabel("Frequency", fontsize=20, color=INK)
ax2.tick_params(axis="both", labelsize=16, colors=INK_SOFT)
ax2.spines["top"].set_visible(False)
ax2.spines["right"].set_visible(False)
ax2.yaxis.grid(True, alpha=0.10, linewidth=0.8, color=INK)

# Subplot 3: Temperature vs Humidity Scatter (bottom-left)
ax3 = axes[1, 0]
sns.scatterplot(
    data=df,
    x="Temperature",
    y="Humidity",
    hue="Hour",
    palette="viridis",
    s=150,
    alpha=0.8,
    ax=ax3,
    edgecolor=PAGE_BG,
    linewidth=0.5,
)
ax3.set_title("Temperature vs Humidity", fontsize=24, fontweight="medium", color=INK)
ax3.set_xlabel("Temperature (°C)", fontsize=20, color=INK)
ax3.set_ylabel("Humidity (%)", fontsize=20, color=INK)
ax3.tick_params(axis="both", labelsize=16, colors=INK_SOFT)
ax3.spines["top"].set_visible(False)
ax3.spines["right"].set_visible(False)
ax3.grid(True, alpha=0.10, linewidth=0.8, color=INK)
ax3.legend(title="Hour", fontsize=12, title_fontsize=13, loc="best")

# Subplot 4: Air Quality and Pressure (bottom-right)
ax4 = axes[1, 1]
ax4_twin = ax4.twinx()

# Plot AQI as bars
bars = ax4.bar(
    df["Hour"], df["AQI"], alpha=0.6, color=IMPRINT[2], label="AQI", width=0.8, edgecolor=PAGE_BG, linewidth=0.5
)

# Plot Pressure as line on twin axis
line = ax4_twin.plot(
    df["Hour"], df["Pressure"], color=IMPRINT[3], linewidth=3, marker="o", markersize=6, label="Pressure"
)

ax4.set_title("Air Quality & Pressure", fontsize=24, fontweight="medium", color=INK)
ax4.set_xlabel("Hours Since Start", fontsize=20, color=INK)
ax4.set_ylabel("AQI", fontsize=20, color=INK)
ax4_twin.set_ylabel("Pressure (hPa)", fontsize=20, color=INK)

ax4.tick_params(axis="both", labelsize=16, colors=INK_SOFT)
ax4_twin.tick_params(axis="y", labelsize=16, colors=INK_SOFT)
ax4.spines["top"].set_visible(False)
ax4_twin.spines["top"].set_visible(False)
ax4.yaxis.grid(True, alpha=0.10, linewidth=0.8, color=INK)

# Combined legend
lines1, labels1 = ax4.get_legend_handles_labels()
lines2, labels2 = ax4_twin.get_legend_handles_labels()
ax4.legend(lines1 + lines2, labels1 + labels2, fontsize=14, loc="upper left")

# Main title
fig.suptitle("subplot-grid · seaborn · anyplot.ai", fontsize=24, fontweight="medium", color=INK, y=0.98)

plt.tight_layout(rect=[0, 0, 1, 0.95])
plt.savefig(f"plot-{THEME}.png", dpi=300, bbox_inches="tight", facecolor=PAGE_BG)
