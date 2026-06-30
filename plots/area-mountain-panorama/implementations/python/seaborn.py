""" anyplot.ai
area-mountain-panorama: Mountain Panorama Profile with Labeled Peaks
Library: seaborn 0.13.2 | Python 3.13.14
Quality: 83/100 | Updated: 2026-06-30
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
        "legend.facecolor": ELEVATED_BG,
        "legend.edgecolor": INK_SOFT,
    },
)

# Data — Wallis (Valais, Switzerland) panorama from Gornergrat, west → east sweep.
# sigma controls angular half-width: smaller = sharper, more iconic summit profile.
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

# Build skyline as upper envelope of per-peak Gaussian bumps over undulating valley floor
np.random.seed(42)
sample_angles = np.linspace(-5.0, 205.0, 1800)

valley_floor = 2950 + 90 * np.sin(sample_angles * np.pi / 95.0 + 0.4) + 55 * np.cos(sample_angles * np.pi / 47.0 + 1.1)

ridge = np.copy(valley_floor)
for _, row in peaks.iterrows():
    floor_at_peak = valley_floor[np.argmin(np.abs(sample_angles - row["angle_deg"]))]
    bump_height = row["elevation_m"] - floor_at_peak
    bump = bump_height * np.exp(-0.5 * ((sample_angles - row["angle_deg"]) / row["sigma"]) ** 2)
    ridge = np.maximum(ridge, valley_floor + bump)

# High-frequency rocky texture, tapered at panorama edges
texture = (
    35 * np.sin(sample_angles * 1.7 + 0.3)
    + 22 * np.sin(sample_angles * 3.1 + 1.7)
    + np.random.normal(0, 14, size=sample_angles.shape)
)
edge_taper = np.clip((sample_angles - 0) / 6, 0, 1) * np.clip((200 - sample_angles) / 6, 0, 1)
ridge = ridge + texture * edge_taper

skyline = pd.DataFrame({"angle_deg": sample_angles, "elevation_m": ridge})

# Plot — 3200×1800 px landscape canvas (figsize=(8,4.5) × dpi=400)
fig, ax = plt.subplots(figsize=(8, 4.5), dpi=400, facecolor=PAGE_BG)
ax.set_facecolor(PAGE_BG)

Y_FLOOR = 2500
LABEL_BASE_Y = 4880
LABEL_STAGGER = 200

# Filled silhouette + crisp ridgeline edge via sns.lineplot
ax.fill_between(skyline["angle_deg"], skyline["elevation_m"], Y_FLOOR, color=BRAND, alpha=1.0, linewidth=0, zorder=2)
sns.lineplot(data=skyline, x="angle_deg", y="elevation_m", color=BRAND, linewidth=1.2, ax=ax, legend=False)

# Assign 3-level stagger based on angular proximity (threshold 20°) to avoid
# same-height labels when peaks cluster (e.g. Breithorn / Pollux / Castor).
peak_angles = peaks["angle_deg"].values
label_levels = np.zeros(len(peaks), dtype=int)
for i in range(1, len(peaks)):
    for lvl in range(3):
        conflict = any(abs(peak_angles[j] - peak_angles[i]) < 20 and label_levels[j] == lvl for j in range(i))
        if not conflict:
            label_levels[i] = lvl
            break
    else:
        label_levels[i] = i % 3

# Peak labels with leader lines
for i, (_, row) in enumerate(peaks.iterrows()):
    is_anchor = row["name"] == "Matterhorn"
    label_y = LABEL_BASE_Y + label_levels[i] * LABEL_STAGGER
    elev_y = label_y - 130
    leader_top = elev_y - 30

    ax.plot(
        [row["angle_deg"], row["angle_deg"]],
        [row["elevation_m"], leader_top],
        color=INK_SOFT,
        linewidth=0.8,
        alpha=0.55,
        zorder=3,
    )
    ax.text(
        row["angle_deg"],
        label_y,
        row["name"],
        fontsize=9 if is_anchor else 8,
        fontweight="semibold" if is_anchor else "regular",
        color=INK,
        ha="center",
        va="bottom",
        zorder=4,
    )
    ax.text(
        row["angle_deg"],
        elev_y,
        f"{int(row['elevation_m'])} m",
        fontsize=7,
        color=INK_MUTED,
        ha="center",
        va="bottom",
        zorder=4,
    )

# Matterhorn focal highlight via sns.scatterplot (open circle on summit)
matterhorn = peaks.loc[peaks["name"] == "Matterhorn"].iloc[0]
sns.scatterplot(
    x=[matterhorn["angle_deg"]],
    y=[matterhorn["elevation_m"]],
    s=90,
    color=PAGE_BG,
    edgecolor=BRAND,
    linewidth=2.0,
    ax=ax,
    zorder=6,
    legend=False,
)

# Style
ax.set_xlim(0, 200)
ax.set_ylim(Y_FLOOR, LABEL_BASE_Y + 2 * LABEL_STAGGER + 350)
ax.set_xlabel("Compass bearing", fontsize=10, color=INK)
ax.set_ylabel("Elevation (m)", fontsize=10, color=INK)
ax.set_title(
    "area-mountain-panorama · python · seaborn · anyplot.ai", fontsize=12, fontweight="medium", color=INK, pad=10
)

ax.set_xticks([0, 50, 100, 150, 200])
ax.set_xticklabels(["W", "SW", "S", "SE", "E"])
ax.tick_params(axis="x", labelsize=8, colors=INK_SOFT, length=0)
ax.tick_params(axis="y", labelsize=8, colors=INK_SOFT, length=0)

sns.despine(ax=ax, top=True, right=True)
ax.spines["left"].set_color(INK_SOFT)
ax.spines["bottom"].set_color(INK_SOFT)
ax.yaxis.grid(True, alpha=0.10, linewidth=0.6, color=INK)
ax.set_axisbelow(True)

fig.subplots_adjust(left=0.09, right=0.97, top=0.91, bottom=0.11)
plt.savefig(f"plot-{THEME}.png", dpi=400, facecolor=PAGE_BG)
