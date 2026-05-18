"""anyplot.ai
heatmap-geographic: Geographic Heatmap for Spatial Density
Library: seaborn | Python 3.13
Quality: 91/100 | Updated: 2026-05-18
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
INK_MUTED = "#6B6A63" if THEME == "light" else "#A8A79F"

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

# Data: Mobile app check-in density across central Tokyo districts
np.random.seed(42)

# Shinjuku — major rail hub and entertainment district
shinjuku_lat = np.random.normal(35.690, 0.012, 280)
shinjuku_lon = np.random.normal(139.700, 0.012, 280)

# Shibuya — commercial and youth culture centre
shibuya_lat = np.random.normal(35.660, 0.010, 220)
shibuya_lon = np.random.normal(139.699, 0.010, 220)

# Ginza — luxury retail and business district
ginza_lat = np.random.normal(35.672, 0.008, 180)
ginza_lon = np.random.normal(139.763, 0.008, 180)

# Akihabara — electronics and pop-culture district
akiba_lat = np.random.normal(35.700, 0.007, 140)
akiba_lon = np.random.normal(139.773, 0.007, 140)

# Scattered activity across central Tokyo
scattered_lat = np.random.uniform(35.63, 35.73, 180)
scattered_lon = np.random.uniform(139.67, 139.80, 180)

latitude = np.concatenate([shinjuku_lat, shibuya_lat, ginza_lat, akiba_lat, scattered_lat])
longitude = np.concatenate([shinjuku_lon, shibuya_lon, ginza_lon, akiba_lon, scattered_lon])

# Plot
fig, ax = plt.subplots(figsize=(16, 9))

# KDE geographic heatmap
sns.kdeplot(
    x=longitude,
    y=latitude,
    ax=ax,
    fill=True,
    cmap="YlOrRd",
    levels=30,
    thresh=0.02,
    alpha=0.85,
    cbar=True,
    cbar_kws={"label": "Check-in Density", "shrink": 0.8},
)

# Scatter overlay: individual check-in locations
ax.scatter(longitude, latitude, s=12, alpha=0.25, color=INK_MUTED, edgecolors="none", zorder=5)

# District labels provide geographic context
districts = [
    ("Shinjuku", 139.700, 35.701),
    ("Shibuya", 139.699, 35.649),
    ("Ginza", 139.763, 35.681),
    ("Akihabara", 139.773, 35.709),
]
for name, lon, lat in districts:
    ax.text(lon, lat, name, fontsize=13, color=INK, ha="center", va="center", fontweight="semibold", alpha=0.85)

# Axis style
ax.set_xlabel("Longitude (°E)", fontsize=20)
ax.set_ylabel("Latitude (°N)", fontsize=20)
ax.set_title(
    "Tokyo Check-ins · heatmap-geographic · python · seaborn · anyplot.ai",
    fontsize=22,
    fontweight="medium",
    color=INK,
    pad=15,
)
ax.tick_params(axis="both", labelsize=16)

ax.xaxis.set_major_formatter(plt.FuncFormatter(lambda x, _: f"{x:.2f}°"))
ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda y, _: f"{y:.2f}°"))

ax.spines["top"].set_visible(False)
ax.spines["right"].set_visible(False)
for s in ("left", "bottom"):
    ax.spines[s].set_color(INK_SOFT)

ax.grid(True, alpha=0.10, linewidth=0.8)
ax.set_aspect("equal", adjustable="box")

# Style colorbar axes (theme-adaptive tick labels and label color)
for cbar_ax in fig.axes:
    if cbar_ax is not ax:
        cbar_ax.tick_params(labelsize=14, colors=INK_SOFT)
        cbar_ax.yaxis.label.set_color(INK)
        cbar_ax.yaxis.label.set_fontsize(18)
        break

plt.tight_layout()
plt.savefig(f"plot-{THEME}.png", dpi=300, bbox_inches="tight", facecolor=PAGE_BG)
