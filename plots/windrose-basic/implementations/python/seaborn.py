""" anyplot.ai
windrose-basic: Wind Rose Chart
Library: seaborn 0.13.2 | Python 3.13.14
Quality: 80/100 | Updated: 2026-08-05
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

# Imprint palette for speed ranges (cool to warm progression), built via
# seaborn's own palette API so downstream seaborn calls (kdeplot) share it.
IMPRINT = sns.color_palette(["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030"])

# Configure seaborn
sns.set_theme(
    style="ticks",
    rc={
        "figure.facecolor": PAGE_BG,
        "axes.facecolor": PAGE_BG,
        "axes.labelcolor": INK,
        "text.color": INK,
        "xtick.color": INK_SOFT,
        "ytick.color": INK_SOFT,
        "grid.color": INK_SOFT,
        "grid.alpha": 0.10,
        "legend.facecolor": ELEVATED_BG,
        "legend.edgecolor": INK_SOFT,
    },
)

# Data
np.random.seed(42)
n_obs = 8760

# Simulate prevailing winds with realistic distribution
direction_weights = np.zeros(360)
direction_weights[200:240] = 3.0
direction_weights[30:60] = 1.5
direction_weights[260:290] = 1.0
direction_weights += 0.2
direction_weights /= direction_weights.sum()

directions = np.random.choice(360, size=n_obs, p=direction_weights)
directions = (directions + np.random.uniform(-10, 10, n_obs)) % 360

# Wind speeds by direction
speeds = np.zeros(n_obs)
for i, d in enumerate(directions):
    if 200 <= d <= 240:
        speeds[i] = np.random.weibull(2.2) * 8 + 2
    elif 30 <= d <= 60:
        speeds[i] = np.random.weibull(2.0) * 6 + 1
    else:
        speeds[i] = np.random.weibull(1.8) * 4 + 0.5
speeds = np.clip(speeds, 0, 25)

# 8-direction bins (N, NE, E, SE, S, SW, W, NW)
n_dir_bins = 8
dir_bins = np.linspace(0, 360, n_dir_bins + 1)
dir_centers = (dir_bins[:-1] + dir_bins[1:]) / 2
dir_width = 2 * np.pi / n_dir_bins

# Speed bins
speed_bins = [0, 3, 6, 10, 15, 25]
speed_labels = ["0-3 m/s", "3-6 m/s", "6-10 m/s", "10-15 m/s", "15+ m/s"]

# Calculate frequencies
frequencies = np.zeros((n_dir_bins, len(speed_labels)))
for i in range(n_dir_bins):
    dir_min, dir_max = dir_bins[i], dir_bins[i + 1]
    in_dir = (directions >= dir_min) & (directions < dir_max)

    for j in range(len(speed_labels)):
        speed_min = speed_bins[j]
        speed_max = speed_bins[j + 1]
        in_speed = (speeds >= speed_min) & (speeds < speed_max)
        frequencies[i, j] = np.sum(in_dir & in_speed)

frequencies = frequencies / n_obs * 100

# Plot: polar wind rose fills the square canvas; legend and a seaborn KDE
# inset sit in the corners that fall outside the circle, which the bars
# (clipped to the radial axis limit) never reach regardless of direction.
fig = plt.figure(figsize=(6, 6), dpi=400, facecolor=PAGE_BG)
ax = fig.add_axes((0.06, 0.06, 0.88, 0.88), projection="polar")
ax.set_facecolor(PAGE_BG)
ax.set_theta_zero_location("N")
ax.set_theta_direction(-1)

theta = np.deg2rad(dir_centers)

# Identify prevailing wind sectors (highest frequency) for visual emphasis
total_freq = frequencies.sum(axis=1)
dominant_threshold = np.percentile(total_freq, 75)
is_dominant = total_freq > dominant_threshold

# Plot stacked bars with the Imprint palette
bottoms = np.zeros(n_dir_bins)
for j, (label, color) in enumerate(zip(speed_labels, IMPRINT, strict=False)):
    alpha_per_sector = np.where(is_dominant, 0.90, 0.65)
    # Contiguous petals (full dir_width, no inter-sector gap): a gap here would
    # leave a thin sliver of background between direction bins that, next to a
    # tall dominant sector, reads as a stray line cutting across the chart.
    bars = ax.bar(
        theta,
        frequencies[:, j],
        width=dir_width,
        bottom=bottoms,
        color=color,
        edgecolor=PAGE_BG,
        linewidth=0.7,
        label=label,
    )
    for bar, alpha_val in zip(bars, alpha_per_sector, strict=False):
        bar.set_alpha(alpha_val)
    bottoms += frequencies[:, j]

# Title
ax.set_title("windrose-basic · python · seaborn · anyplot.ai", fontsize=12, pad=16, fontweight="medium", color=INK)

max_freq = np.ceil(bottoms.max() / 5) * 5
ax.set_ylim(0, max_freq)
ax.set_yticks(np.arange(0, max_freq + 1, 5))
ax.set_yticklabels([f"{int(y)}%" for y in np.arange(0, max_freq + 1, 5)], fontsize=9, color=INK_SOFT)
# Move the radial-label spoke into the near-empty E/SE sector so it doesn't
# cut across the dominant, densely colored bars.
ax.set_rlabel_position(112.5)

direction_labels = ["N", "NE", "E", "SE", "S", "SW", "W", "NW"]
ax.set_xticks(np.deg2rad(np.arange(0, 360, 45)))
ax.set_xticklabels(direction_labels, fontsize=11, fontweight="medium", color=INK)

# Grid styling
ax.grid(True, alpha=0.12, linestyle="-", linewidth=0.8, color=INK_SOFT)
for spine in ax.spines.values():
    spine.set_color(INK_SOFT)
    spine.set_linewidth(1.1)

# Legend stays inside the axes bounding box (bottom-right corner, outside the
# circle) so nothing gets clipped by the fixed-size canvas.
legend = ax.legend(title="Wind Speed", loc="lower right", fontsize=9, title_fontsize=10, framealpha=0.95)
legend.get_frame().set_facecolor(ELEVATED_BG)
legend.get_frame().set_edgecolor(INK_SOFT)
legend.get_title().set_color(INK)
for text in legend.get_texts():
    text.set_color(INK)

# Distinctive seaborn feature: a kernel-density estimate of the overall speed
# distribution, tucked into the opposite (top-left) empty corner.
inset = fig.add_axes((0.05, 0.72, 0.24, 0.20))
sns.kdeplot(x=speeds, fill=True, color=IMPRINT[0], alpha=0.55, linewidth=1.2, ax=inset)
inset.set_facecolor(PAGE_BG)
inset.set_title("Speed distribution", fontsize=8, color=INK, pad=3)
inset.set_xlabel("Wind speed (m/s)", fontsize=7, color=INK_SOFT)
inset.set_ylabel("")
inset.set_yticks([])
inset.tick_params(axis="x", labelsize=6, colors=INK_SOFT)
sns.despine(ax=inset, left=True)
inset.spines["bottom"].set_color(INK_SOFT)

fig.savefig(f"plot-{THEME}.png", dpi=400, facecolor=PAGE_BG)
