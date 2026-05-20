""" anyplot.ai
contour-map-geographic: Contour Lines on Geographic Map
Library: seaborn 0.13.2 | Python 3.13.13
Quality: 82/100 | Updated: 2026-05-20
"""

import os

import matplotlib.pyplot as plt
import numpy as np
import seaborn as sns


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
OCEAN = "#C4D8EC" if THEME == "light" else "#182633"
LAND = "#D8CEA8" if THEME == "light" else "#5A5040"
COAST = "#7A7264" if THEME == "light" else "#8A8070"

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

# Data: Global temperature anomaly grid (simulated climate data)
np.random.seed(42)

lon = np.linspace(-180, 180, 72)
lat = np.linspace(-70, 85, 32)
LON, LAT = np.meshgrid(lon, lat)

# Realistic temperature anomaly: higher anomalies at poles (Arctic amplification)
anomaly_base = 0.5 + 1.5 * (np.abs(LAT) / 90) ** 1.5
anomaly_regional = 0.8 * np.sin(np.radians(LON * 2)) * np.cos(np.radians(LAT * 1.5)) + 0.6 * np.cos(
    np.radians(LON + 60)
) * np.sin(np.radians(LAT * 2))
noise = np.random.randn(32, 72) * 0.3
Z = np.clip(anomaly_base + anomaly_regional + noise, -2.0, 4.5)

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

# Canvas — landscape 3200×1800 px (no bbox_inches='tight' per seaborn library rule)
fig, ax = plt.subplots(figsize=(8, 4.5), dpi=400)
fig.patch.set_facecolor(PAGE_BG)

# Ocean background and map extent
ax.set_facecolor(OCEAN)
ax.set_xlim(-180, 180)
ax.set_ylim(-70, 85)

# Filled contours for temperature anomalies
levels = np.linspace(-2, 4.5, 14)
contourf_plot = ax.contourf(LON, LAT, Z, levels=levels, cmap="RdYlBu_r", alpha=0.85, extend="both", zorder=1)

# Contour lines at every other level
contour_lines = ax.contour(LON, LAT, Z, levels=levels[::2], colors=INK, linewidths=0.8, alpha=0.55, zorder=2)
ax.clabel(contour_lines, inline=True, fontsize=8, fmt="%.1f°C", colors=INK)

# Coastlines with subtle land fill for geographic context
for coastline in WORLD_COASTLINES:
    if len(coastline) > 2:
        lons = [p[0] for p in coastline]
        lats = [p[1] for p in coastline]
        ax.fill(lons, lats, color=LAND, edgecolor=COAST, linewidth=1.2, zorder=3)

# Colorbar
cbar = fig.colorbar(contourf_plot, ax=ax, shrink=0.75, pad=0.02, aspect=30)
cbar.set_label("Temperature Anomaly (°C)", fontsize=10, color=INK)
cbar.ax.tick_params(labelsize=8, colors=INK_SOFT)
cbar.outline.set_edgecolor(INK_SOFT)

# Axes labels and title
ax.set_xlabel("Longitude (°)", fontsize=10, color=INK)
ax.set_ylabel("Latitude (°)", fontsize=10, color=INK)
fig.suptitle(
    "Global Temperature Anomaly · contour-map-geographic · python · seaborn · anyplot.ai",
    fontsize=11,
    fontweight="bold",
    x=0.5,
    y=0.98,
    color=INK,
)
ax.tick_params(axis="both", labelsize=8, colors=INK_SOFT)

# Subtle geographic grid
ax.grid(True, alpha=0.10, linewidth=0.5, color=INK_SOFT, zorder=0)
ax.set_axisbelow(True)

# Geographic equal-aspect ratio for correct map proportions
ax.set_aspect("equal", adjustable="box")

# Remove top/right spines
ax.spines["top"].set_visible(False)
ax.spines["right"].set_visible(False)
ax.spines["left"].set_color(INK_SOFT)
ax.spines["bottom"].set_color(INK_SOFT)

plt.tight_layout()
plt.savefig(f"plot-{THEME}.png", dpi=400, facecolor=PAGE_BG)
