""" anyplot.ai
area-mountain-panorama: Mountain Panorama Profile with Labeled Peaks
Library: matplotlib 3.10.9 | Python 3.14.4
Quality: 82/100 | Created: 2026-04-25
"""

import os

import matplotlib.pyplot as plt
import numpy as np


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
INK_MUTED = "#6B6A63" if THEME == "light" else "#A8A79F"
BRAND = "#009E73"

# Data — Wallis (Valais) summit panorama, ordered W → E
peaks = [
    ("Weisshorn", 12, 4506),
    ("Zinalrothorn", 30, 4221),
    ("Ober Gabelhorn", 45, 4063),
    ("Dent Blanche", 58, 4358),
    ("Dent d'Hérens", 76, 4171),
    ("Matterhorn", 92, 4478),
    ("Breithorn", 120, 4164),
    ("Pollux", 132, 4092),
    ("Castor", 139, 4223),
    ("Liskamm", 152, 4527),
    ("Monte Rosa", 170, 4634),
    ("Strahlhorn", 192, 4190),
    ("Rimpfischhorn", 204, 4199),
    ("Allalinhorn", 215, 4027),
    ("Alphubel", 225, 4206),
    ("Täschhorn", 236, 4491),
    ("Dom", 250, 4545),
]

# Skyline construction
np.random.seed(42)
angle = np.linspace(0, 262, 2000)


def gaussian_smooth(arr, sigma):
    radius = max(1, int(3 * sigma))
    grid = np.arange(-radius, radius + 1)
    kernel = np.exp(-(grid**2) / (2 * sigma**2))
    kernel = kernel / kernel.sum()
    return np.convolve(arr, kernel, mode="same")


# Base ridge: smoothed random walk in the 3000–3700 m belt (foothills + minor cols)
walk = np.cumsum(np.random.randn(len(angle)) * 1.5)
walk = gaussian_smooth(walk, sigma=22)
walk = (walk - walk.min()) / (walk.max() - walk.min())
ridge = 3000 + walk * 700

# Major summits as Gaussian peaks (max-combined for the visible silhouette)
for _, pos, elev in peaks:
    width = 5.5 + (elev - 4000) / 130
    bump = (elev - 2700) * np.exp(-((angle - pos) ** 2) / (2 * width**2))
    ridge = np.maximum(ridge, 2700 + bump)

ridge = gaussian_smooth(ridge, sigma=0.8)

# Plot
fig, ax = plt.subplots(figsize=(16, 9), facecolor=PAGE_BG)
ax.set_facecolor(PAGE_BG)

# Mountain silhouette
ax.fill_between(angle, 2400, ridge, color=BRAND, linewidth=0, zorder=2)
ax.plot(angle, ridge, color=BRAND, linewidth=1.0, zorder=3)

# Peak labels staggered across three vertical levels, with thin leader lines
label_levels = [5050, 5320, 5590]
sorted_peaks = sorted(peaks, key=lambda p: p[1])
for i, (name, pos, elev) in enumerate(sorted_peaks):
    level = label_levels[i % 3]
    is_anchor = name == "Matterhorn"
    text_color = INK if is_anchor else INK_SOFT
    text_weight = "bold" if is_anchor else "regular"
    line_color = INK if is_anchor else INK_SOFT
    line_alpha = 0.85 if is_anchor else 0.45
    line_width = 1.2 if is_anchor else 0.7
    fsize = 13 if is_anchor else 11

    ax.plot([pos, pos], [elev + 25, level - 90], color=line_color, linewidth=line_width, alpha=line_alpha, zorder=4)
    ax.text(
        pos,
        level,
        f"{name}\n{elev:,} m",
        ha="center",
        va="bottom",
        fontsize=fsize,
        fontweight=text_weight,
        color=text_color,
        linespacing=1.35,
        zorder=5,
    )

# Axes
ax.set_ylim(2500, 6050)
ax.set_xlim(0, 262)
ax.set_ylabel("Elevation (m)", fontsize=20, color=INK)
ax.set_title(
    "Wallis Alps · area-mountain-panorama · matplotlib · anyplot.ai",
    fontsize=24,
    fontweight="medium",
    color=INK,
    pad=18,
)

# Compass bearings on x-axis
compass_ticks = [10, 65, 120, 180, 245]
compass_labels = ["W", "SW", "S", "SE", "E"]
ax.set_xticks(compass_ticks)
ax.set_xticklabels(compass_labels, fontsize=16, color=INK_SOFT)
ax.tick_params(axis="x", colors=INK_SOFT, length=0)
ax.tick_params(axis="y", labelsize=16, colors=INK_SOFT)

ax.spines["top"].set_visible(False)
ax.spines["right"].set_visible(False)
for s in ("left", "bottom"):
    ax.spines[s].set_color(INK_SOFT)
ax.yaxis.grid(True, alpha=0.10, linewidth=0.8, color=INK)

plt.tight_layout()
plt.savefig(f"plot-{THEME}.png", dpi=300, bbox_inches="tight", facecolor=PAGE_BG)
