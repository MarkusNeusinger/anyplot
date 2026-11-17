""" anyplot.ai
scatter-color-mapped: Color-Mapped Scatter Plot
Library: seaborn 0.13.2 | Python 3.14.10
Quality: 82/100 | Updated: 2026-11-17
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
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Imprint palette: canonical order, first series always #009E73
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

# Imprint sequential colormap (single polarity, brand green to blue)
imprint_seq = LinearSegmentedColormap.from_list("imprint_seq", [IMPRINT_PALETTE[0], IMPRINT_PALETTE[2]])

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
LONGITUDE = "Longitude (°W)"  # role: x
LATITUDE = "Latitude (°N)"  # role: y
AQI = "Air Quality Index"  # role: color

# Data: replace this block with your own table, for example df = pd.read_csv("stations.csv")
rng = np.random.default_rng(42)
n_stations = 200
lat = rng.uniform(25, 50, n_stations)
lon = rng.uniform(-130, -65, n_stations)
urban_density = np.exp(-((lat - 40) ** 2 + (lon + 90) ** 2) / 400)
aqi = np.clip(30 + urban_density * 70 + rng.normal(0, 5, n_stations), 10, 150)
df = pd.DataFrame({LONGITUDE: lon, LATITUDE: lat, AQI: aqi})

# Plot: reads only df and the constants above
norm = Normalize(vmin=df[AQI].min(), vmax=df[AQI].max())

fig, ax = plt.subplots(figsize=(8, 4.5), dpi=400, facecolor=PAGE_BG)
sns.scatterplot(
    data=df,
    x=LONGITUDE,
    y=LATITUDE,
    hue=AQI,
    hue_norm=norm,
    palette=imprint_seq,
    s=60,
    alpha=0.85,
    edgecolor=INK_SOFT,
    linewidth=0.4,
    legend=False,
    ax=ax,
)

# Colorbar
cbar = fig.colorbar(ScalarMappable(norm=norm, cmap=imprint_seq), ax=ax, pad=0.02)
cbar.set_label(AQI, fontsize=10, color=INK)
cbar.ax.tick_params(labelsize=8, colors=INK_SOFT)
cbar.outline.set_edgecolor(INK_SOFT)

# Style
ax.set_title("scatter-color-mapped · python · seaborn · anyplot.ai", fontsize=12, fontweight="medium", color=INK)
ax.set_xlabel(LONGITUDE, fontsize=10)
ax.set_ylabel(LATITUDE, fontsize=10)
ax.tick_params(axis="both", labelsize=8)
ax.yaxis.grid(True, alpha=0.10, linewidth=0.8, color=INK)
sns.despine(ax=ax)

plt.savefig(f"plot-{THEME}.png", dpi=400, facecolor=PAGE_BG)
