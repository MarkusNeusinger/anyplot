""" anyplot.ai
area-mountain-panorama: Mountain Panorama Profile with Labeled Peaks
Library: seaborn 0.13.2 | Python 3.14.4
Quality: 82/100 | Created: 2026-04-25
"""

import os

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
INK_MUTED = "#6B6A63" if THEME == "light" else "#A8A79F"
BRAND = "#009E73"

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
    },
)

# Data — Wallis (Valais, Switzerland) panorama from Gornergrat, west → east sweep.
# `sigma` is the angular half-width that shapes how broad each summit reads on
# the silhouette: smaller = sharper, more iconic profile.
peaks = pd.DataFrame(
    [
        {"name": "Weisshorn", "angle_deg": 10.0, "elevation_m": 4506, "sigma": 4.6},
        {"name": "Zinalrothorn", "angle_deg": 22.0, "elevation_m": 4221, "sigma": 4.2},
        {"name": "Ober Gabelhorn", "angle_deg": 32.0, "elevation_m": 4063, "sigma": 5.4},
        {"name": "Dent Blanche", "angle_deg": 44.0, "elevation_m": 4358, "sigma": 4.6},
        {"name": "Matterhorn", "angle_deg": 62.0, "elevation_m": 4478, "sigma": 3.0},
        {"name": "Breithorn", "angle_deg": 82.0, "elevation_m": 4164, "sigma": 7.0},
        {"name": "Pollux", "angle_deg": 92.0, "elevation_m": 4092, "sigma": 3.6},
        {"name": "Castor", "angle_deg": 99.0, "elevation_m": 4223, "sigma": 3.6},
        {"name": "Liskamm", "angle_deg": 110.0, "elevation_m": 4527, "sigma": 6.5},
        {"name": "Dufourspitze", "angle_deg": 124.0, "elevation_m": 4634, "sigma": 5.2},
        {"name": "Strahlhorn", "angle_deg": 142.0, "elevation_m": 4190, "sigma": 5.0},
        {"name": "Rimpfischhorn", "angle_deg": 152.0, "elevation_m": 4199, "sigma": 4.4},
        {"name": "Allalinhorn", "angle_deg": 161.0, "elevation_m": 4027, "sigma": 5.2},
        {"name": "Alphubel", "angle_deg": 171.0, "elevation_m": 4206, "sigma": 4.6},
        {"name": "Täschhorn", "angle_deg": 181.0, "elevation_m": 4491, "sigma": 3.6},
        {"name": "Dom", "angle_deg": 191.0, "elevation_m": 4545, "sigma": 3.4},
    ]
)

# Build the skyline as the upper envelope of per-peak Gaussian bumps over a
# slowly undulating valley floor. This produces distinct peak shapes
# (sharper for iconic summits, broader for massif shoulders) instead of the
# uniform scallop pattern a global spline would give.
np.random.seed(42)
sample_angles = np.linspace(-5.0, 205.0, 1800)

valley_floor = 2950 + 90 * np.sin(sample_angles * np.pi / 95.0 + 0.4) + 55 * np.cos(sample_angles * np.pi / 47.0 + 1.1)

ridge = np.copy(valley_floor)
for _, row in peaks.iterrows():
    floor_at_peak = valley_floor[np.argmin(np.abs(sample_angles - row["angle_deg"]))]
    bump_height = row["elevation_m"] - floor_at_peak
    bump = bump_height * np.exp(-0.5 * ((sample_angles - row["angle_deg"]) / row["sigma"]) ** 2)
    ridge = np.maximum(ridge, valley_floor + bump)

# High-frequency rocky texture; tapered so edges blend into the valley floor
texture = (
    35 * np.sin(sample_angles * 1.7 + 0.3)
    + 22 * np.sin(sample_angles * 3.1 + 1.7)
    + np.random.normal(0, 14, size=sample_angles.shape)
)
edge_taper = np.clip((sample_angles - 0) / 6, 0, 1) * np.clip((200 - sample_angles) / 6, 0, 1)
ridge = ridge + texture * edge_taper

skyline = pd.DataFrame({"angle_deg": sample_angles, "elevation_m": ridge})

# Plot
fig, ax = plt.subplots(figsize=(16, 9), facecolor=PAGE_BG)
ax.set_facecolor(PAGE_BG)

Y_FLOOR = 2500
LABEL_BASE_Y = 5150
LABEL_STAGGER = 360

# Filled silhouette
ax.fill_between(skyline["angle_deg"], skyline["elevation_m"], Y_FLOOR, color=BRAND, alpha=1.0, linewidth=0, zorder=2)
sns.lineplot(data=skyline, x="angle_deg", y="elevation_m", color=BRAND, linewidth=1.6, ax=ax, legend=False)

# Peak labels with leader lines, alternating heights to avoid overlap
for i, row in peaks.iterrows():
    is_anchor = row["name"] == "Matterhorn"
    label_y = LABEL_BASE_Y + (LABEL_STAGGER if i % 2 == 0 else 0)
    leader_top = label_y - 80

    ax.plot(
        [row["angle_deg"], row["angle_deg"]],
        [row["elevation_m"], leader_top],
        color=INK_SOFT,
        linewidth=1.0,
        alpha=0.65,
        zorder=3,
    )

    ax.text(
        row["angle_deg"],
        label_y,
        row["name"],
        fontsize=15 if is_anchor else 13,
        fontweight="semibold" if is_anchor else "regular",
        color=INK,
        ha="center",
        va="bottom",
        zorder=4,
    )
    ax.text(
        row["angle_deg"],
        label_y - 195,
        f"{int(row['elevation_m'])} m",
        fontsize=11,
        color=INK_MUTED,
        ha="center",
        va="bottom",
        zorder=4,
    )

# Highlight Matterhorn summit as the focal anchor
matterhorn = peaks.loc[peaks["name"] == "Matterhorn"].iloc[0]
ax.scatter(
    [matterhorn["angle_deg"]],
    [matterhorn["elevation_m"]],
    s=110,
    color=PAGE_BG,
    edgecolor=BRAND,
    linewidth=2.8,
    zorder=6,
)

# Style
ax.set_xlim(0, 200)
ax.set_ylim(Y_FLOOR, LABEL_BASE_Y + LABEL_STAGGER + 600)
ax.set_xlabel("Compass bearing", fontsize=20, color=INK)
ax.set_ylabel("Elevation (m)", fontsize=20, color=INK)
ax.set_title(
    "Wallis 4000ers from Gornergrat · area-mountain-panorama · seaborn · anyplot.ai",
    fontsize=24,
    fontweight="medium",
    color=INK,
    pad=18,
)

ax.set_xticks([0, 50, 100, 150, 200])
ax.set_xticklabels(["W", "SW", "S", "SE", "E"])
ax.tick_params(axis="x", labelsize=16, colors=INK_SOFT, length=0)
ax.tick_params(axis="y", labelsize=16, colors=INK_SOFT, length=0)

ax.spines["top"].set_visible(False)
ax.spines["right"].set_visible(False)
ax.spines["left"].set_color(INK_SOFT)
ax.spines["bottom"].set_color(INK_SOFT)
ax.yaxis.grid(True, alpha=0.10, linewidth=0.8, color=INK)
ax.set_axisbelow(True)

plt.tight_layout()
plt.savefig(f"plot-{THEME}.png", dpi=300, bbox_inches="tight", facecolor=PAGE_BG)
