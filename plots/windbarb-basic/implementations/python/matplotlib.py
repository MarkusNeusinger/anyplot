"""anyplot.ai
windbarb-basic: Wind Barb Plot for Meteorological Data
Library: matplotlib 3.10.9 | Python 3.13.13
Quality: pending | Updated: 2026-05-19
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

# Imprint palette: position 1 is the single series
BRAND = "#009E73"

# Columns: set these to your table's column names
LONGITUDE = "Longitude (°E)"  # role: x
LATITUDE = "Latitude (°N)"  # role: y
U_WIND = "Zonal wind u (kt)"  # role: u
V_WIND = "Meridional wind v (kt)"  # role: v

# Data: replace this block with your own table, for example df = pd.read_csv("winds.csv")
# Surface wind observations from a western Pacific weather station network
np.random.seed(42)

# Grid of observation points: 10 longitude × 6 latitude (120–129°E, 25–30°N)
lon, lat = np.meshgrid(np.arange(120, 130, 1), np.arange(25, 31, 1))
lon = lon.flatten()
lat = lat.flatten()

# Wind components (u: east-west, v: north-south) in knots,
# a mid-latitude westerly pattern with spatial coherence
base_u = 15 + 10 * np.sin((lon - 120) * 0.5)
base_v = 5 + 8 * np.cos((lat - 25) * 0.8)
u = base_u + np.random.uniform(-5, 5, size=lon.shape)
v = base_v + np.random.uniform(-5, 5, size=lat.shape)

# Calm winds (< 2.5 knots)
calm_indices = [0, 25, 45]
u[calm_indices] = np.random.uniform(-1, 1, size=len(calm_indices))
v[calm_indices] = np.random.uniform(-1, 1, size=len(calm_indices))

# Strong winds with pennants (50+ knots)
strong_indices = [12, 38, 55]
u[strong_indices] = 40 + np.random.uniform(0, 15, size=len(strong_indices))
v[strong_indices] = 30 + np.random.uniform(0, 10, size=len(strong_indices))

df = pd.DataFrame({LONGITUDE: lon, LATITUDE: lat, U_WIND: u, V_WIND: v})

# Plot: reads only df and the constants above
fig, ax = plt.subplots(figsize=(8, 4.5), dpi=400, facecolor=PAGE_BG)
ax.set_facecolor(PAGE_BG)

ax.barbs(
    df[LONGITUDE],
    df[LATITUDE],
    df[U_WIND],
    df[V_WIND],
    length=6,
    barb_increments={"half": 5, "full": 10, "flag": 50},
    color=BRAND,
    linewidth=1.1,
    sizes={"emptybarb": 0.15, "spacing": 0.15, "height": 0.5},
)

# Style
ax.set_xlabel(LONGITUDE, fontsize=10, color=INK)
ax.set_ylabel(LATITUDE, fontsize=10, color=INK)
ax.set_title("windbarb-basic · python · matplotlib · anyplot.ai", fontsize=12, fontweight="medium", color=INK)
ax.tick_params(axis="both", labelsize=8, colors=INK_SOFT)
for spine in ("left", "bottom"):
    ax.spines[spine].set_color(INK_SOFT)
ax.spines["top"].set_visible(False)
ax.spines["right"].set_visible(False)
ax.grid(True, alpha=0.10, linewidth=0.8, color=INK)

ax.set_xlim(df[LONGITUDE].min() - 0.5, df[LONGITUDE].max() + 0.5)
ax.set_ylim(df[LATITUDE].min() - 2.6, df[LATITUDE].max() + 0.5)  # empty band below the barbs holds the key

# Barb notation key, placed bottom-right clear of the barbs
legend_text = (
    "Wind Barb Legend:\n○ = Calm (< 2.5 kt)\n╲ = 5 kt (half barb)\n╲╲ = 10 kt (full barb)\n▲ = 50 kt (pennant)"
)
ax.text(
    0.98,
    0.02,
    legend_text,
    transform=ax.transAxes,
    fontsize=8,
    verticalalignment="bottom",
    horizontalalignment="right",
    fontfamily="monospace",
    color=INK_SOFT,
    bbox={"boxstyle": "round", "facecolor": ELEVATED_BG, "alpha": 0.9, "edgecolor": INK_SOFT},
)

fig.subplots_adjust(left=0.08, right=0.97, top=0.92, bottom=0.12)
plt.savefig(f"plot-{THEME}.png", dpi=400, facecolor=PAGE_BG)
