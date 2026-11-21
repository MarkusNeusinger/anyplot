"""anyplot.ai
subplot-grid: Subplot Grid Layout
Library: seaborn 0.13.2 | Python 3.13.13
Quality: pending | Updated: 2026-05-13
"""

import os

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
from matplotlib.cm import ScalarMappable
from matplotlib.colors import LinearSegmentedColormap, Normalize


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Imprint palette: all eight positions, one per series in order
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

# Continuous scale for the hour of the scatter points (Imprint sequential)
imprint_seq = LinearSegmentedColormap.from_list("imprint_seq", ["#009E73", "#4467A3"])

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

# Columns: set these to your table's column names
HOUR = "Time (hours since start)"  # role: x
TEMPERATURE = "Temperature (°C)"  # role: y
HUMIDITY = "Humidity (%)"  # role: extra
AQI = "Air quality index (AQI)"  # role: extra
PRESSURE = "Pressure (hPa)"  # role: extra

# Data: replace this block with your own table, for example df = pd.read_csv("readings.csv")
# Environmental monitoring station: 48 hourly readings
np.random.seed(42)
hours = np.arange(48)
base_temp = 15 + 8 * np.sin(np.pi * hours / 24)
base_humidity = 60 + 15 * np.sin(np.pi * (hours - 6) / 24)
df = pd.DataFrame(
    {
        HOUR: hours,
        TEMPERATURE: base_temp + np.random.normal(0, 0.8, 48),
        HUMIDITY: base_humidity + np.random.normal(0, 3, 48),
        AQI: 40 + 20 * np.abs(np.sin(np.pi * hours / 48)) + np.random.normal(0, 2, 48),
        PRESSURE: 1013 + np.cumsum(np.random.normal(0, 0.1, 48)),
    }
)

# Plot: reads only df and the constants above
fig, axes = plt.subplots(2, 2, figsize=(8, 4.5), dpi=400, facecolor=PAGE_BG)
ax1, ax2, ax3, ax4 = axes.ravel()

# Top-left: temperature time series
sns.lineplot(data=df, x=HOUR, y=TEMPERATURE, ax=ax1, color=IMPRINT_PALETTE[0], linewidth=2)
ax1.set_title("Temperature over time")

# Top-right: humidity distribution
sns.histplot(data=df, x=HUMIDITY, bins=15, ax=ax2, color=IMPRINT_PALETTE[1], alpha=0.8, edgecolor=PAGE_BG)
ax2.set_ylabel("Frequency")
ax2.set_title("Humidity distribution")

# Bottom-left: temperature vs humidity, colored by hour with a color bar beside the cell
sns.scatterplot(
    data=df,
    x=TEMPERATURE,
    y=HUMIDITY,
    hue=HOUR,
    palette=imprint_seq,
    s=28,
    alpha=0.9,
    edgecolor=PAGE_BG,
    linewidth=0.4,
    legend=False,
    ax=ax3,
)
ax3.set_title("Temperature vs humidity")
cbar = fig.colorbar(
    ScalarMappable(norm=Normalize(df[HOUR].min(), df[HOUR].max()), cmap=imprint_seq), ax=ax3, pad=0.02, aspect=18
)
cbar.set_label("Hour", fontsize=8, color=INK)
cbar.ax.tick_params(labelsize=8, colors=INK_SOFT)
cbar.outline.set_edgecolor(INK_SOFT)

# Bottom-right: AQI bars with pressure line on a twin axis
ax4_twin = ax4.twinx()
ax4.bar(
    df[HOUR], df[AQI], width=0.8, alpha=0.7, color=IMPRINT_PALETTE[2], edgecolor=PAGE_BG, linewidth=0.3, label="AQI"
)
ax4_twin.plot(
    df[HOUR], df[PRESSURE], color=IMPRINT_PALETTE[3], linewidth=1.8, marker="o", markersize=2.5, label="Pressure"
)
ax4.set_xlabel(HOUR)
ax4.set_ylabel(AQI)
ax4_twin.set_ylabel(PRESSURE)
ax4.set_title("Air quality & pressure")
ax4.set_ylim(0, df[AQI].max() * 1.45)
handles = ax4.get_legend_handles_labels()[0] + ax4_twin.get_legend_handles_labels()[0]
labels = ax4.get_legend_handles_labels()[1] + ax4_twin.get_legend_handles_labels()[1]
ax4.legend(handles, labels, fontsize=8, loc="upper left", ncol=2)

# Style: shared chrome for every cell
for ax in (ax1, ax2, ax3, ax4, ax4_twin):
    ax.tick_params(axis="both", labelsize=8, colors=INK_SOFT)
    ax.xaxis.label.set_size(10)
    ax.yaxis.label.set_size(10)
    ax.spines["top"].set_visible(False)
    if ax is not ax4_twin:
        ax.yaxis.grid(True, alpha=0.10, linewidth=0.6, color=INK)
for ax in (ax1, ax2, ax3, ax4):
    ax.title.set_fontsize(11)
    ax.title.set_fontweight("medium")
    if ax is not ax4:
        ax.spines["right"].set_visible(False)
ax4_twin.ticklabel_format(axis="y", useOffset=False)
ax4_twin.spines["right"].set_color(INK_SOFT)
ax4_twin.spines["left"].set_visible(False)

fig.suptitle("subplot-grid · python · seaborn · anyplot.ai", fontsize=12, fontweight="medium", color=INK)
fig.tight_layout(rect=(0, 0, 1, 0.97), h_pad=1.2)
plt.savefig(f"plot-{THEME}.png", dpi=400, facecolor=PAGE_BG)
