""" anyplot.ai
windbarb-basic: Wind Barb Plot for Meteorological Data
Library: seaborn 0.13.2 | Python 3.14.10
Quality: 79/100 | Updated: 2026-11-22
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
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
INK_MUTED = "#6B6A63" if THEME == "light" else "#A8A79F"

# Imprint palette: all eight positions in canonical order
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

# Imprint sequential colormap for the continuous wind speed
imprint_seq = LinearSegmentedColormap.from_list("imprint_seq", ["#009E73", "#4467A3"])

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
    },
)

# Constants
CALM_KNOTS = 2.5  # winds below this speed are drawn as an open circle without a staff
BARB_INCREMENTS = {"half": 5, "full": 10, "flag": 50}  # knots per half barb, full barb and pennant

# Columns: set these to your table's column names
LONGITUDE = "Longitude (°E)"  # role: x
LATITUDE = "Latitude (°N)"  # role: y
U_WIND = "Zonal wind u (knots)"  # role: u
V_WIND = "Meridional wind v (knots)"  # role: v

# Data: replace this block with your own table, for example df = pd.read_csv("winds.csv")
np.random.seed(42)
lon, lat = np.meshgrid(np.linspace(2, 12, 6), np.linspace(2, 8, 4))
lon = lon.flatten()
lat = lat.flatten()
n_stations = len(lon)

# Spatially coherent field plus noise
u = 20 * np.sin(lon * 0.4) + 15 + np.random.randn(n_stations) * 8
v = 15 * np.cos(lat * 0.5) + 10 + np.random.randn(n_stations) * 8

# Calm stations
for idx in [0, 11, 23]:
    u[idx] = 0.5 * (np.random.rand() - 0.5)
    v[idx] = 0.5 * (np.random.rand() - 0.5)

# Strong stations that need pennants
for idx in [5, 9, 18]:
    angle = np.random.rand() * 2 * np.pi
    speed_val = 55 + np.random.rand() * 15
    u[idx] = speed_val * np.cos(angle)
    v[idx] = speed_val * np.sin(angle)

df = pd.DataFrame({LONGITUDE: lon, LATITUDE: lat, U_WIND: u, V_WIND: v})

# Plot: reads only df and the constants above
speed = np.hypot(df[U_WIND], df[V_WIND])
is_calm = speed < CALM_KNOTS
winds = df[~is_calm]
calm = df[is_calm]

fig, ax = plt.subplots(figsize=(8, 4.5), dpi=400, facecolor=PAGE_BG)
ax.set_facecolor(PAGE_BG)
fig.subplots_adjust(left=0.08, right=0.93, top=0.92, bottom=0.2)

top_speed = speed.max()
barbs = ax.barbs(
    winds[LONGITUDE],
    winds[LATITUDE],
    winds[U_WIND],
    winds[V_WIND],
    speed[~is_calm],
    cmap=imprint_seq,
    clim=(0, top_speed),
    length=7,
    linewidth=1.5,
    barb_increments=BARB_INCREMENTS,
    pivot="middle",
)

# Calm stations: open circle alone, no staff, colored as the lowest speed
if len(calm) > 0:
    sns.scatterplot(
        data=calm,
        x=LONGITUDE,
        y=LATITUDE,
        s=110,
        marker="o",
        facecolor="none",
        edgecolor=imprint_seq(0.0),
        linewidth=1.6,
        legend=False,
        ax=ax,
    )

cbar = fig.colorbar(barbs, ax=ax, pad=0.015, fraction=0.04)
cbar.set_label("Wind speed (knots)", fontsize=10, color=INK)
cbar.ax.tick_params(labelsize=8, colors=INK_SOFT)
cbar.outline.set_edgecolor(INK_SOFT)

# Style
ax.set_title("windbarb-basic · python · seaborn · anyplot.ai", fontsize=12, fontweight="medium", color=INK)
ax.set_xlabel(LONGITUDE, fontsize=10)
ax.set_ylabel(LATITUDE, fontsize=10)
ax.tick_params(axis="both", labelsize=8)
x_lo, x_hi = df[LONGITUDE].min(), df[LONGITUDE].max()
y_lo, y_hi = df[LATITUDE].min(), df[LATITUDE].max()
ax.set_xlim(x_lo - 0.08 * (x_hi - x_lo), x_hi + 0.08 * (x_hi - x_lo))
ax.set_ylim(y_lo - 0.12 * (y_hi - y_lo), y_hi + 0.12 * (y_hi - y_lo))
sns.despine(ax=ax)

key = (
    f"Barb notation: ○ calm (<{CALM_KNOTS} kt)  |  half barb {BARB_INCREMENTS['half']} kt  |  "
    f"full barb {BARB_INCREMENTS['full']} kt  |  pennant ▲ {BARB_INCREMENTS['flag']} kt"
)
fig.text(0.5, 0.03, key, fontsize=8, ha="center", va="bottom", color=INK_MUTED)

plt.savefig(f"plot-{THEME}.png", dpi=400, facecolor=PAGE_BG)
