"""anyplot.ai
contour-map-geographic: Contour Lines on Geographic Map
Library: seaborn 0.13.2 | Python 3.13.13
Quality: 83/100 | Updated: 2026-05-20
"""

import os

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
from matplotlib.colors import LinearSegmentedColormap, TwoSlopeNorm


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
OCEAN = "#C4D8EC" if THEME == "light" else "#182633"
LAND = "#D8CEA8" if THEME == "light" else "#5A5040"
COAST = "#7A7264" if THEME == "light" else "#8A8070"

# Imprint palette: first position is the single-series color
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

# Imprint diverging ramp for filled fields: page color at the midpoint; reversed so warm anomalies are red
DIV_FIELDS = [(0.0, "#AE3030"), (0.5, PAGE_BG), (1.0, "#4467A3")]
imprint_div = LinearSegmentedColormap.from_list("imprint_div", DIV_FIELDS).reversed()

# Constants
CONTOUR_STEP = 0.5  # contour interval in °C; every second level is drawn as a labeled line
ARCTIC_LAT = 60  # boundary of the Arctic amplification zone (°N)

# Columns: set these to your table's column names
LONGITUDE = "Longitude (°)"  # role: lon
LATITUDE = "Latitude (°)"  # role: lat
ANOMALY = "Temperature anomaly (°C)"  # role: value

# Simplified world coastline polygons (major continents)
WORLD_COASTLINES = [
    # North America
    [
        (-168, 66),
        (-141, 70),
        (-130, 70),
        (-120, 60),
        (-125, 50),
        (-125, 40),
        (-117, 33),
        (-105, 25),
        (-97, 26),
        (-82, 25),
        (-81, 30),
        (-75, 35),
        (-70, 42),
        (-67, 45),
        (-60, 47),
        (-55, 52),
        (-60, 60),
        (-65, 68),
        (-80, 70),
        (-100, 73),
        (-120, 75),
        (-145, 72),
        (-168, 66),
    ],
    # South America
    [
        (-82, 10),
        (-77, 0),
        (-80, -5),
        (-70, -15),
        (-60, -5),
        (-50, 0),
        (-35, -5),
        (-40, -23),
        (-55, -35),
        (-68, -55),
        (-75, -50),
        (-75, -40),
        (-70, -20),
        (-80, -5),
        (-82, 10),
    ],
    # Europe
    [
        (-10, 36),
        (-10, 45),
        (-5, 48),
        (0, 52),
        (5, 55),
        (10, 58),
        (20, 60),
        (28, 70),
        (35, 70),
        (30, 60),
        (25, 55),
        (20, 50),
        (15, 45),
        (20, 40),
        (25, 35),
        (35, 35),
        (28, 42),
        (20, 38),
        (10, 38),
        (-10, 36),
    ],
    # Africa
    [
        (-17, 15),
        (-17, 28),
        (-5, 36),
        (10, 38),
        (20, 33),
        (35, 30),
        (45, 12),
        (52, 12),
        (45, 0),
        (42, -10),
        (35, -25),
        (25, -34),
        (18, -35),
        (12, -20),
        (15, -5),
        (5, 5),
        (-10, 5),
        (-17, 15),
    ],
    # Asia
    [
        (35, 30),
        (45, 42),
        (52, 45),
        (70, 42),
        (80, 30),
        (75, 15),
        (90, 22),
        (100, 15),
        (105, 22),
        (110, 5),
        (120, 25),
        (130, 35),
        (140, 45),
        (145, 55),
        (135, 70),
        (100, 78),
        (70, 75),
        (50, 70),
        (30, 70),
        (35, 50),
        (45, 45),
        (35, 30),
    ],
    # Australia
    [
        (113, -22),
        (120, -18),
        (135, -12),
        (145, -15),
        (152, -25),
        (150, -38),
        (140, -38),
        (130, -33),
        (115, -35),
        (113, -22),
    ],
]


# Data: replace this block with your own table, for example df = pd.read_csv("anomaly.csv")
np.random.seed(42)
lon = np.linspace(-180, 180, 72)
lat = np.linspace(-70, 85, 32)
LON, LAT = np.meshgrid(lon, lat)
# Arctic amplification: larger anomalies toward the poles, plus regional waves and noise
anomaly_base = 0.5 + 1.5 * (np.abs(LAT) / 90) ** 1.5
anomaly_regional = 0.8 * np.sin(np.radians(LON * 2)) * np.cos(np.radians(LAT * 1.5)) + 0.6 * np.cos(
    np.radians(LON + 60)
) * np.sin(np.radians(LAT * 2))
noise = np.random.randn(32, 72) * 0.1
Z = np.clip(anomaly_base + anomaly_regional + noise, -2.0, 4.5)
df = pd.DataFrame({LONGITUDE: LON.ravel(), LATITUDE: LAT.ravel(), ANOMALY: Z.ravel()})

# Apply seaborn theme with full theme-adaptive chrome
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

# Plot: reads only df and the constants above
grid = df.pivot_table(index=LATITUDE, columns=LONGITUDE, values=ANOMALY)
grid_lon = grid.columns.to_numpy()
grid_lat = grid.index.to_numpy()
values = grid.to_numpy()

low = np.floor(np.nanmin(values) / CONTOUR_STEP) * CONTOUR_STEP
high = np.ceil(np.nanmax(values) / CONTOUR_STEP) * CONTOUR_STEP
levels = np.arange(low, high + CONTOUR_STEP / 2, CONTOUR_STEP)
norm = TwoSlopeNorm(vcenter=0, vmin=min(low, -CONTOUR_STEP), vmax=max(high, CONTOUR_STEP))

# Canvas: landscape 3200x1800 px, main geographic map + zonal mean side panel
fig, (ax_map, ax_zone) = plt.subplots(
    1, 2, figsize=(8, 4.5), dpi=400, gridspec_kw={"width_ratios": [4, 1], "wspace": 0.06}
)
fig.patch.set_facecolor(PAGE_BG)

# Geographic contour map
ax_map.set_facecolor(OCEAN)
ax_map.set_xlim(grid_lon.min(), grid_lon.max())
ax_map.set_ylim(grid_lat.min(), grid_lat.max())

# Filled bands, diverging around 0: blue = cooler than baseline, red = warmer
contourf_plot = ax_map.contourf(grid_lon, grid_lat, values, levels=levels, cmap=imprint_div, norm=norm, zorder=1)

# Translucent land and coastlines over the fill, contour lines and labels above them
for coastline in WORLD_COASTLINES:
    lons, lats = zip(*coastline, strict=True)
    ax_map.fill(lons, lats, facecolor=LAND, alpha=0.35, edgecolor=COAST, linewidth=1.2, zorder=3)

contour_lines = ax_map.contour(
    grid_lon, grid_lat, values, levels=levels[::2], colors=INK, linewidths=0.9, alpha=0.8, zorder=4
)
ax_map.clabel(contour_lines, inline=True, fontsize=9, fmt="%.1f°C", colors=INK)

# Colorbar
cbar = fig.colorbar(contourf_plot, ax=ax_map, ticks=levels[::2], shrink=0.80, pad=0.02, aspect=30)
cbar.set_label(ANOMALY, fontsize=11, color=INK)
cbar.ax.tick_params(labelsize=9, colors=INK_SOFT)
cbar.outline.set_edgecolor(INK_SOFT)

ax_map.set_xlabel(LONGITUDE, fontsize=11, color=INK)
ax_map.set_ylabel(LATITUDE, fontsize=11, color=INK)
ax_map.tick_params(axis="both", labelsize=9, colors=INK_SOFT)
ax_map.grid(True, alpha=0.10, linewidth=0.5, color=INK_SOFT, zorder=0)
ax_map.set_axisbelow(True)
sns.despine(ax=ax_map)

# Zonal mean profile: seaborn averages the anomaly over longitude for each latitude
sns.lineplot(
    data=df,
    x=ANOMALY,
    y=LATITUDE,
    orient="y",
    estimator="mean",
    errorbar=None,
    color=IMPRINT_PALETTE[0],
    linewidth=2.2,
    ax=ax_zone,
)
zonal_mean = df.groupby(LATITUDE)[ANOMALY].mean()
ax_zone.fill_betweenx(
    zonal_mean.index, 0, zonal_mean.to_numpy(), where=zonal_mean.to_numpy() > 0, color=IMPRINT_PALETTE[0], alpha=0.18
)
ax_zone.axvline(0, color=INK_SOFT, linewidth=0.8, linestyle="--", alpha=0.6)
ax_zone.axhline(ARCTIC_LAT, color=IMPRINT_PALETTE[0], linewidth=0.8, linestyle=":", alpha=0.8)
ax_zone.text(
    0.5, 0.97, "Arctic\namplification", transform=ax_zone.transAxes, fontsize=8, color=INK, ha="center", va="top"
)

ax_zone.set_ylim(grid_lat.min(), grid_lat.max())
ax_zone.set_title("Zonal mean", fontsize=10, color=INK, pad=4)
ax_zone.set_xlabel("Anomaly (°C)", fontsize=10, color=INK)
ax_zone.set_ylabel("")
ax_zone.tick_params(axis="x", labelsize=9, colors=INK_SOFT)
ax_zone.set_yticks([])
ax_zone.grid(True, alpha=0.10, linewidth=0.5, color=INK_SOFT)
ax_zone.set_facecolor(PAGE_BG)
sns.despine(ax=ax_zone, left=True)

fig.suptitle(
    "Global Temperature Anomaly · contour-map-geographic · python · seaborn · anyplot.ai",
    fontsize=11,
    fontweight="bold",
    x=0.5,
    y=0.98,
    color=INK,
)

plt.tight_layout()
plt.savefig(f"plot-{THEME}.png", dpi=400, facecolor=PAGE_BG)
