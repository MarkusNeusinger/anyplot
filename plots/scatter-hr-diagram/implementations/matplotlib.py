""" pyplots.ai
scatter-hr-diagram: Hertzsprung-Russell Diagram
Library: matplotlib 3.10.8 | Python 3.14.3
Quality: 88/100 | Created: 2026-03-07
"""

import matplotlib.patheffects as pe
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import numpy as np


# Data
np.random.seed(42)

spectral_colors = {
    "O": "#2244aa",
    "B": "#4488cc",
    "A": "#7799bb",
    "F": "#aacc55",
    "G": "#ffcc00",
    "K": "#ee7711",
    "M": "#cc2200",
}

temp_ranges = {
    "O": (30000, 40000),
    "B": (10000, 30000),
    "A": (7500, 10000),
    "F": (6000, 7500),
    "G": (5200, 6000),
    "K": (3700, 5200),
    "M": (2400, 3700),
}

# Main sequence stars (250)
ms_counts = {"O": 8, "B": 20, "A": 30, "F": 35, "G": 45, "K": 55, "M": 57}
all_temps, all_lums, all_types = [], [], []

for sp, (t_lo, t_hi) in temp_ranges.items():
    n = ms_counts[sp]
    temps = np.random.uniform(t_lo, t_hi, n)
    log_lums = 4.0 * np.log10(temps / 5778) + np.random.normal(0, 0.3, n)
    all_temps.extend(temps)
    all_lums.extend(10**log_lums)
    all_types.extend([sp] * n)

# Red giants (50)
rg_temps = np.random.uniform(3000, 5200, 50)
rg_lums = 10 ** np.random.uniform(1.0, 3.0, 50)
all_temps.extend(rg_temps)
all_lums.extend(rg_lums)
all_types.extend(["K" if t >= 3700 else "M" for t in rg_temps])

# Supergiants (35)
sg_temps = np.random.uniform(3500, 30000, 35)
sg_lums = 10 ** np.random.uniform(3.5, 5.5, 35)
all_temps.extend(sg_temps)
all_lums.extend(sg_lums)
all_types.extend(
    [
        "M"
        if t < 3700
        else "K"
        if t < 5200
        else "G"
        if t < 6000
        else "F"
        if t < 7500
        else "A"
        if t < 10000
        else "B"
        if t < 30000
        else "O"
        for t in sg_temps
    ]
)

# White dwarfs (30)
wd_temps = np.random.uniform(5000, 30000, 30)
wd_lums = 10 ** np.random.uniform(-4.0, -1.5, 30)
all_temps.extend(wd_temps)
all_lums.extend(wd_lums)
all_types.extend(
    ["G" if t < 6000 else "F" if t < 7500 else "A" if t < 10000 else "B" if t < 30000 else "O" for t in wd_temps]
)

all_temps = np.array(all_temps)
all_lums = np.array(all_lums)

# Plot
fig, ax = plt.subplots(figsize=(16, 9))
fig.patch.set_facecolor("#f5f5f0")
ax.set_facecolor("#f5f5f0")

for sp in ["O", "B", "A", "F", "G", "K", "M"]:
    mask = np.array([t == sp for t in all_types])
    if mask.any():
        ax.scatter(
            all_temps[mask],
            all_lums[mask],
            c=spectral_colors[sp],
            label=sp,
            s=40,
            alpha=0.5,
            edgecolors="white",
            linewidth=0.5,
            zorder=3,
        )

# Sun reference point with path effects glow
sun_marker = ax.scatter(
    5778,
    1.0,
    c="#ffcc00",
    s=600,
    edgecolors="#333333",
    linewidth=2,
    zorder=5,
    marker="*",
    path_effects=[pe.withSimplePatchShadow(offset=(1, -1), shadow_rgbFace="#ccaa00", alpha=0.4)],
)
ax.annotate(
    "Sun",
    (5778, 1.0),
    textcoords="offset points",
    xytext=(15, -12),
    fontsize=16,
    fontweight="bold",
    color="#333333",
    fontfamily="serif",
    path_effects=[pe.withStroke(linewidth=3, foreground="#f5f5f0")],
)

# Region labels with path effects for refined typography
region_style = {"fontsize": 16, "fontstyle": "italic", "color": "#444444", "fontfamily": "serif", "ha": "center"}
text_effect = [pe.withStroke(linewidth=4, foreground="#f5f5f0")]

ax.annotate(
    "Main Sequence",
    xy=(15000, 200),
    rotation=-42,
    bbox={"boxstyle": "round,pad=0.4", "fc": "#f5f5f0", "ec": "none", "alpha": 0.85},
    path_effects=text_effect,
    **region_style,
)
ax.annotate(
    "Red Giants",
    xy=(3400, 300),
    bbox={"boxstyle": "round,pad=0.4", "fc": "#f5f5f0", "ec": "none", "alpha": 0.85},
    path_effects=text_effect,
    **region_style,
)
ax.annotate(
    "Supergiants",
    xy=(8000, 400000),
    bbox={"boxstyle": "round,pad=0.4", "fc": "#f5f5f0", "ec": "none", "alpha": 0.85},
    path_effects=text_effect,
    **region_style,
)
ax.annotate(
    "White Dwarfs",
    xy=(15000, 0.00008),
    bbox={"boxstyle": "round,pad=0.4", "fc": "#f5f5f0", "ec": "none", "alpha": 0.85},
    path_effects=text_effect,
    **region_style,
)

# Style
ax.set_xscale("log")
ax.set_yscale("log")
ax.set_xlim(45000, 2000)
ax.set_ylim(1e-5, 2e6)

# Custom tick formatter using FuncFormatter
ax.xaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f"{int(x):,}"))

ax.set_xlabel("Surface Temperature (K)", fontsize=20, fontfamily="serif")
ax.set_ylabel("Luminosity (L/L$_\\odot$)", fontsize=20, fontfamily="serif")
ax.set_title(
    "scatter-hr-diagram \u00b7 matplotlib \u00b7 pyplots.ai",
    fontsize=24,
    fontweight="medium",
    fontfamily="serif",
    pad=25,
    path_effects=[pe.withStroke(linewidth=3, foreground="#f5f5f0")],
)
ax.tick_params(axis="both", labelsize=16)

legend = ax.legend(
    title="Spectral Type",
    fontsize=14,
    title_fontsize=16,
    loc="lower left",
    framealpha=0.9,
    edgecolor="#cccccc",
    facecolor="#f5f5f0",
    shadow=True,
    borderpad=1.0,
)
legend.get_title().set_fontfamily("serif")

ax.spines["top"].set_visible(False)
ax.spines["right"].set_visible(False)
ax.spines["left"].set_linewidth(0.8)
ax.spines["left"].set_color("#999999")
ax.spines["bottom"].set_linewidth(0.8)
ax.spines["bottom"].set_color("#999999")
ax.yaxis.grid(True, alpha=0.12, linewidth=0.8, which="both", color="#888888")

# Secondary x-axis for spectral classes
ax2 = ax.twiny()
spectral_positions = [35000, 20000, 8750, 6750, 5600, 4450, 3050]
spectral_labels = ["O", "B", "A", "F", "G", "K", "M"]
ax2.set_xscale("log")
ax2.set_xlim(ax.get_xlim())
ax2.set_xticks(spectral_positions)
ax2.set_xticklabels(spectral_labels, fontsize=16, fontfamily="serif")
ax2.set_xlabel("Spectral Class", fontsize=18, labelpad=12, fontfamily="serif")
ax2.tick_params(axis="x", length=0)
ax2.spines["top"].set_visible(False)
ax2.spines["right"].set_visible(False)

plt.tight_layout()
plt.savefig("plot.png", dpi=300, bbox_inches="tight")
