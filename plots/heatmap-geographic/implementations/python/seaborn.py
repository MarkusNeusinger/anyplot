"""anyplot.ai
heatmap-geographic: Geographic Heatmap for Spatial Density
Library: seaborn 0.13.2 | Python 3.13.13
Quality: 83/100 | Updated: 2026-05-19
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
INK_MUTED = "#6B6A63" if THEME == "light" else "#A8A79F"

# Imprint palette: first series is always #009E73
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

# Imprint sequential colormap for density (single polarity)
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
        "grid.alpha": 0.10,
        "legend.facecolor": ELEVATED_BG,
        "legend.edgecolor": INK_SOFT,
    },
)

# Constants: basemap geometry of the Tokyo Bay shoreline as (longitude, latitude), simplified
BAY_SHORE = [
    (139.700, 35.480),
    (139.740, 35.580),
    (139.752, 35.625),
    (139.770, 35.633),
    (139.785, 35.645),
    (139.800, 35.652),
    (139.900, 35.640),
]
BAY_FLOOR = 35.480  # southern edge of the water polygon
BAY_EAST = 139.950  # eastern edge of the water polygon
OUTSIDE = "Scattered"  # group name for check-ins that belong to no district

# Columns: set these to your table's column names
LATITUDE = "Latitude (°N)"  # role: latitude
LONGITUDE = "Longitude (°E)"  # role: longitude
DISTRICT = "District"  # role: extra

# Data: replace this block with your own table, for example df = pd.read_csv("checkins.csv")
rng = np.random.default_rng(42)
districts = {
    # name: (centre latitude, centre longitude, spread in degrees, check-ins)
    "Shinjuku": (35.690, 139.700, 0.012, 280),
    "Shibuya": (35.660, 139.699, 0.010, 220),
    "Ginza": (35.672, 139.763, 0.008, 180),
    "Akihabara": (35.700, 139.773, 0.007, 140),
}
frames = [
    pd.DataFrame({LATITUDE: rng.normal(lat, spread, count), LONGITUDE: rng.normal(lon, spread, count), DISTRICT: name})
    for name, (lat, lon, spread, count) in districts.items()
]
frames.append(
    pd.DataFrame(
        {LATITUDE: rng.uniform(35.63, 35.73, 180), LONGITUDE: rng.uniform(139.67, 139.80, 180), DISTRICT: OUTSIDE}
    )
)
df = pd.concat(frames, ignore_index=True)

# Plot
fig, ax = plt.subplots(figsize=(8, 4.5), dpi=400)

# Basemap: bay water and shoreline
shore_lon, shore_lat = zip(*BAY_SHORE, strict=True)
water_lon = [*shore_lon, BAY_EAST, BAY_EAST, shore_lon[0]]
water_lat = [*shore_lat, shore_lat[-1], BAY_FLOOR, BAY_FLOOR]
ax.fill(water_lon, water_lat, color=IMPRINT_PALETTE[5], alpha=0.16, linewidth=0, zorder=0)
ax.plot(shore_lon, shore_lat, color=INK_SOFT, linewidth=1.4, zorder=1)

# KDE geographic heatmap, translucent so the shoreline shows through
sns.kdeplot(
    data=df,
    x=LONGITUDE,
    y=LATITUDE,
    ax=ax,
    fill=True,
    cmap=imprint_seq,
    levels=30,
    thresh=0.12,
    alpha=0.6,
    zorder=2,
    cbar=True,
    cbar_kws={"label": "Check-in density", "shrink": 0.8},
)

# Scatter overlay: individual check-in locations
ax.scatter(df[LONGITUDE], df[LATITUDE], s=5, alpha=0.35, color=INK_MUTED, edgecolors="none", zorder=5)

# District labels at the centre of each group, placed just above it
centres = df[df[DISTRICT] != OUTSIDE].groupby(DISTRICT, sort=False)[[LONGITUDE, LATITUDE]].median()
for name, row in centres.iterrows():
    ax.annotate(
        name,
        (row[LONGITUDE], row[LATITUDE]),
        xytext=(0, 14),
        textcoords="offset points",
        fontsize=8,
        color=INK,
        ha="center",
        va="center",
        fontweight="semibold",
        zorder=6,
    )

# Bay label near the water, offset from the shoreline's east end
ax.annotate(
    "Tokyo Bay",
    (shore_lon[-2], shore_lat[-2]),
    xytext=(40, -26),
    textcoords="offset points",
    fontsize=9,
    color=INK_SOFT,
    style="italic",
    ha="center",
    zorder=6,
)

# Style
ax.set_xlabel(LONGITUDE, fontsize=10)
ax.set_ylabel(LATITUDE, fontsize=10)
ax.set_title(
    "Tokyo Check-ins · heatmap-geographic · python · seaborn · anyplot.ai",
    fontsize=12,
    fontweight="medium",
    color=INK,
    pad=8,
)
ax.tick_params(axis="both", labelsize=8)
ax.xaxis.set_major_formatter(plt.FuncFormatter(lambda x, _: f"{x:.2f}°"))
ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda y, _: f"{y:.2f}°"))

# View: data extent with a margin, equal ground distance via the latitude correction
pad_lon = 0.12 * np.ptp(df[LONGITUDE])
pad_lat = 0.12 * np.ptp(df[LATITUDE])
ax.set_xlim(df[LONGITUDE].min() - pad_lon, df[LONGITUDE].max() + pad_lon)
ax.set_ylim(df[LATITUDE].min() - pad_lat, df[LATITUDE].max() + pad_lat)
ax.set_aspect(1 / np.cos(np.radians(df[LATITUDE].mean())), adjustable="datalim")

ax.spines["top"].set_visible(False)
ax.spines["right"].set_visible(False)
ax.grid(True, alpha=0.10, linewidth=0.6)

# Colorbar axes: theme-adaptive tick labels and label
cbar_ax = fig.axes[-1]
cbar_ax.tick_params(labelsize=8, colors=INK_SOFT)
cbar_ax.yaxis.label.set_color(INK)
cbar_ax.yaxis.label.set_fontsize(10)

fig.tight_layout()
plt.savefig(f"plot-{THEME}.png", dpi=400, facecolor=PAGE_BG)
