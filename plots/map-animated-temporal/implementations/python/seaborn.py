""" anyplot.ai
map-animated-temporal: Animated Map over Time
Library: seaborn 0.13.2 | Python 3.13.13
Quality: 88/100 | Updated: 2026-05-27
"""

import os

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
from matplotlib.colors import LinearSegmentedColormap
from matplotlib.lines import Line2D


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

# Sequential colormap for magnitude (single-polarity continuous)
imprint_seq = LinearSegmentedColormap.from_list("imprint_seq", ["#009E73", "#4467A3"])

# Ocean tint for geographic context
OCEAN_TINT = "#D4E8F0" if THEME == "light" else "#192830"

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
        "legend.facecolor": ELEVATED_BG,
        "legend.edgecolor": INK_SOFT,
    },
)

# Synthetic aftershock sequence — Tohoku region, Japan (off Miyagi coast)
np.random.seed(42)

epicenter_lat, epicenter_lon = 38.1, 142.8
n_periods = 6
mag_min, mag_max = 2.5, 5.8

data_records = []
for period in range(n_periods):
    spread = 0.4 + period * 0.25
    n_pts = 12 + period * 4
    lats = epicenter_lat + np.random.randn(n_pts) * spread
    lons = epicenter_lon + np.random.randn(n_pts) * spread
    upper = max(mag_min + 0.5, mag_max - period * 0.4)
    mags = np.random.uniform(mag_min, upper, n_pts)
    for i in range(n_pts):
        data_records.append(
            {"lat": float(lats[i]), "lon": float(lons[i]), "magnitude": float(mags[i]), "period": f"Day {period + 1}"}
        )

df = pd.DataFrame(data_records)

# Simplified Tohoku coastline (Sanriku coast, Miyagi–Iwate prefectures)
coast_lons = [141.2, 141.3, 141.5, 141.4, 141.1, 141.0, 141.1, 141.4, 141.6, 141.9]
coast_lats = [40.5, 40.1, 39.5, 39.0, 38.5, 38.0, 37.5, 37.0, 36.8, 36.5]

# Small multiples grid — 2 rows × 3 cols
fig, axes = plt.subplots(2, 3, figsize=(8, 4.5), dpi=400, facecolor=PAGE_BG)
axes = axes.flatten()

for idx in range(n_periods):
    ax = axes[idx]
    ax.set_facecolor(PAGE_BG)
    period_label = f"Day {idx + 1}"
    period_data = df[df["period"] == period_label].copy()
    cumulative_data = df[df["period"].isin([f"Day {i + 1}" for i in range(idx + 1)])].copy()

    # Ocean tint east of coastline
    ax.axvspan(141.5, epicenter_lon + 3.5, color=OCEAN_TINT, alpha=0.35, zorder=0)

    # Simplified coastline for geographic context
    ax.plot(coast_lons, coast_lats, color=INK_SOFT, linewidth=0.8, alpha=0.65, zorder=2)

    # Cumulative KDE density contours (seaborn-distinctive): show where aftershocks cluster
    if idx >= 1:
        sns.kdeplot(
            data=cumulative_data,
            x="lon",
            y="lat",
            ax=ax,
            color=INK_SOFT,
            alpha=0.30,
            fill=False,
            levels=3,
            linewidths=0.7,
            zorder=1,
        )

    # Ghost trail: previous periods' scatter points (temporal history)
    if idx > 0:
        trail_data = df[df["period"].isin([f"Day {i + 1}" for i in range(idx)])].copy()
        ax.scatter(trail_data["lon"], trail_data["lat"], s=3, c=INK_SOFT, alpha=0.15, zorder=2, linewidths=0)

    # Aftershock scatter with dual encoding: hue + size for magnitude
    sns.scatterplot(
        data=period_data,
        x="lon",
        y="lat",
        size="magnitude",
        sizes=(10, 110),
        hue="magnitude",
        palette=imprint_seq,
        hue_norm=(mag_min, mag_max),
        alpha=0.80,
        edgecolor=PAGE_BG,
        linewidth=0.3,
        ax=ax,
        legend=False,
    )

    # Epicenter marker (matte red — danger semantic anchor)
    ax.scatter(
        epicenter_lon, epicenter_lat, marker="*", s=90, c=IMPRINT_PALETTE[4], edgecolors=INK, linewidths=0.5, zorder=10
    )

    ax.set_xlim(epicenter_lon - 3.5, epicenter_lon + 3.5)
    ax.set_ylim(epicenter_lat - 3.5, epicenter_lat + 3.5)
    ax.set_title(period_label, fontsize=9, fontweight="bold", color=INK)
    ax.set_xlabel("Lon (°E)" if idx >= 3 else "", fontsize=8, color=INK)
    ax.set_ylabel("Lat (°N)" if idx % 3 == 0 else "", fontsize=8, color=INK)
    ax.tick_params(axis="both", labelsize=6.5, colors=INK_SOFT)
    ax.grid(True, alpha=0.12, linewidth=0.5, color=INK)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)

    # Point count annotation per panel
    ax.text(
        0.97,
        0.04,
        f"n={len(period_data)}",
        transform=ax.transAxes,
        ha="right",
        va="bottom",
        fontsize=6.5,
        color=INK_SOFT,
        style="italic",
    )

# Overall title
title = "map-animated-temporal · python · seaborn · anyplot.ai"
fig.suptitle(title, fontsize=12, fontweight="medium", color=INK, y=0.98)

# Shared colorbar for magnitude scale
norm = plt.Normalize(vmin=mag_min, vmax=mag_max)
sm = plt.cm.ScalarMappable(cmap=imprint_seq, norm=norm)
sm.set_array([])
cbar_ax = fig.add_axes([0.93, 0.20, 0.013, 0.58])
cbar = fig.colorbar(sm, cax=cbar_ax)
cbar.set_label("Magnitude", fontsize=7.5, color=INK)
cbar.ax.tick_params(labelsize=6.5, colors=INK_SOFT)
cbar.outline.set_edgecolor(INK_SOFT)

# Legend for map context markers
epicenter_handle = Line2D(
    [0],
    [0],
    marker="*",
    color="w",
    markerfacecolor=IMPRINT_PALETTE[4],
    markeredgecolor=INK,
    markersize=7,
    linestyle="None",
    label="Epicenter",
)
coast_handle = Line2D([0], [0], color=INK_SOFT, linewidth=1.2, label="Coastline")

fig.legend(
    handles=[epicenter_handle, coast_handle],
    loc="lower center",
    bbox_to_anchor=(0.46, 0.02),
    fontsize=7,
    framealpha=0.92,
    facecolor=ELEVATED_BG,
    edgecolor=INK_SOFT,
    ncol=2,
    handlelength=1.2,
)

fig.subplots_adjust(left=0.08, right=0.91, top=0.88, bottom=0.14, wspace=0.38, hspace=0.50)
plt.savefig(f"plot-{THEME}.png", dpi=400, facecolor=PAGE_BG)
