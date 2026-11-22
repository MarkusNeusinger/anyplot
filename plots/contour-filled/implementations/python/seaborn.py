"""anyplot.ai
contour-filled: Filled Contour Plot
Library: seaborn 0.13.2 | Python 3.13.13
Quality: pending | Updated: 2026-05-15
"""

import os

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
from matplotlib.colors import LinearSegmentedColormap


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Imprint palette: all eight positions in canonical order
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

# Imprint sequential colormap for a single-signed field
imprint_seq = LinearSegmentedColormap.from_list("imprint_seq", ["#009E73", "#4467A3"])

# Configure seaborn theme
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

# Constants
N_LEVELS = 15  # number of contour levels (spec: typically 10-20)

# Columns: set these to your table's column names
LONGITUDE = "Longitude (°E)"  # role: x
LATITUDE = "Latitude (°N)"  # role: y
TEMPERATURE = "Temperature (°C)"  # role: z

# Data: replace this block with your own table, for example df = pd.read_csv("field.csv")
lon, lat = np.meshgrid(np.linspace(-180, 180, 80), np.linspace(-90, 90, 80))
warm_east = 25 * np.exp(-((lon - 60) ** 2 + (lat - 30) ** 2) / 1200)
warm_west = 20 * np.exp(-((lon + 80) ** 2 + (lat + 40) ** 2) / 1500)
cold_trough = -15 * np.exp(-((lon - 40) ** 2 + (lat - 60) ** 2) / 800)
df = pd.DataFrame(
    {LONGITUDE: lon.ravel(), LATITUDE: lat.ravel(), TEMPERATURE: (warm_east + warm_west + cold_trough + 10).ravel()}
)

# Plot: reads only df and the constants above
grid = df.pivot_table(index=LATITUDE, columns=LONGITUDE, values=TEMPERATURE)
levels = np.linspace(np.nanmin(grid.to_numpy()), np.nanmax(grid.to_numpy()), N_LEVELS)

fig, ax = plt.subplots(figsize=(8, 4.5), dpi=400, facecolor=PAGE_BG)
ax.set_facecolor(PAGE_BG)

contourf = ax.contourf(grid.columns, grid.index, grid.to_numpy(), levels=levels, cmap=imprint_seq)
ax.contour(grid.columns, grid.index, grid.to_numpy(), levels=levels, colors=INK_SOFT, linewidths=0.4, alpha=0.5)

cbar = fig.colorbar(contourf, ax=ax, shrink=0.85, pad=0.02)
cbar.set_label(TEMPERATURE, fontsize=10, color=INK)
cbar.ax.tick_params(labelsize=8, colors=INK_SOFT)
cbar.outline.set_edgecolor(INK_SOFT)

# Style
ax.set_xlabel(LONGITUDE, fontsize=10, color=INK)
ax.set_ylabel(LATITUDE, fontsize=10, color=INK)
ax.set_title("contour-filled · python · seaborn · anyplot.ai", fontsize=12, fontweight="medium", color=INK)
ax.tick_params(axis="both", labelsize=8, colors=INK_SOFT)
ax.set_aspect("equal")
ax.grid(False)

plt.savefig(f"plot-{THEME}.png", dpi=400, facecolor=PAGE_BG)
