""" pyplots.ai
scatter-hr-diagram: Hertzsprung-Russell Diagram
Library: matplotlib 3.10.8 | Python 3.14.3
Quality: 86/100 | Created: 2026-03-07
"""

import matplotlib.pyplot as plt
import numpy as np


# Data
np.random.seed(42)

spectral_colors = {
    "O": "#6699ff",
    "B": "#99bbff",
    "A": "#ccddff",
    "F": "#ffee88",
    "G": "#ffdd44",
    "K": "#ff9933",
    "M": "#cc3300",
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
ms_temps = []
ms_lums = []
ms_types = []

for sp_type, (t_lo, t_hi) in temp_ranges.items():
    n = {"O": 8, "B": 20, "A": 30, "F": 35, "G": 45, "K": 55, "M": 57}[sp_type]
    temps = np.random.uniform(t_lo, t_hi, n)
    for t in temps:
        log_lum = 4.0 * np.log10(t / 5778) + np.random.normal(0, 0.3)
        ms_temps.append(t)
        ms_lums.append(10**log_lum)
        ms_types.append(sp_type)

# Red giants (50)
rg_temps = np.random.uniform(3000, 5200, 50)
rg_lums = 10 ** np.random.uniform(1.0, 3.0, 50)
rg_types = []
for t in rg_temps:
    if t < 3700:
        rg_types.append("M")
    elif t < 5200:
        rg_types.append("K")
    else:
        rg_types.append("G")

# Supergiants (20)
sg_temps = np.random.uniform(3500, 30000, 20)
sg_lums = 10 ** np.random.uniform(3.5, 5.5, 20)
sg_types = []
for t in sg_temps:
    if t < 3700:
        sg_types.append("M")
    elif t < 5200:
        sg_types.append("K")
    elif t < 6000:
        sg_types.append("G")
    elif t < 7500:
        sg_types.append("F")
    elif t < 10000:
        sg_types.append("A")
    elif t < 30000:
        sg_types.append("B")
    else:
        sg_types.append("O")

# White dwarfs (30)
wd_temps = np.random.uniform(5000, 30000, 30)
wd_lums = 10 ** np.random.uniform(-4.0, -1.5, 30)
wd_types = []
for t in wd_temps:
    if t < 6000:
        wd_types.append("G")
    elif t < 7500:
        wd_types.append("F")
    elif t < 10000:
        wd_types.append("A")
    else:
        wd_types.append("B")

all_temps = np.array(ms_temps + list(rg_temps) + list(sg_temps) + list(wd_temps))
all_lums = np.array(ms_lums + list(rg_lums) + list(sg_lums) + list(wd_lums))
all_types = ms_types + rg_types + sg_types + wd_types

# Plot
fig, ax = plt.subplots(figsize=(16, 9))

for sp_type in ["O", "B", "A", "F", "G", "K", "M"]:
    mask = np.array([t == sp_type for t in all_types])
    if mask.any():
        ax.scatter(
            all_temps[mask],
            all_lums[mask],
            c=spectral_colors[sp_type],
            label=sp_type,
            s=120,
            alpha=0.75,
            edgecolors="white",
            linewidth=0.5,
            zorder=3,
        )

# Sun reference point
ax.scatter(5778, 1.0, c="#ffdd44", s=500, edgecolors="#333333", linewidth=2, zorder=5, marker="*")
ax.annotate(
    "Sun", (5778, 1.0), textcoords="offset points", xytext=(14, -10), fontsize=16, fontweight="bold", color="#333333"
)

# Region labels
ax.annotate("Main Sequence", xy=(8500, 8), fontsize=15, fontstyle="italic", color="#555555", rotation=-42, ha="center")
ax.annotate("Red Giants", xy=(3800, 300), fontsize=15, fontstyle="italic", color="#555555", ha="center")
ax.annotate("Supergiants", xy=(8000, 60000), fontsize=15, fontstyle="italic", color="#555555", ha="center")
ax.annotate("White Dwarfs", xy=(12000, 0.0005), fontsize=15, fontstyle="italic", color="#555555", ha="center")

# Style
ax.set_xscale("log")
ax.set_yscale("log")
ax.set_xlim(45000, 2000)
ax.set_ylim(1e-5, 2e6)

ax.set_xlabel("Surface Temperature (K)", fontsize=20)
ax.set_ylabel("Luminosity (L/L☉)", fontsize=20)
ax.set_title("scatter-hr-diagram · matplotlib · pyplots.ai", fontsize=24, fontweight="medium")
ax.tick_params(axis="both", labelsize=16)

ax.legend(title="Spectral Type", fontsize=14, title_fontsize=16, loc="upper right", framealpha=0.8, edgecolor="#cccccc")

ax.spines["top"].set_visible(False)
ax.spines["right"].set_visible(False)
ax.grid(True, alpha=0.15, linewidth=0.8, which="both")

# Secondary x-axis for spectral classes
ax2 = ax.twiny()
spectral_positions = [35000, 20000, 8750, 6750, 5600, 4450, 3050]
spectral_labels = ["O", "B", "A", "F", "G", "K", "M"]
ax2.set_xscale("log")
ax2.set_xlim(ax.get_xlim())
ax2.set_xticks(spectral_positions)
ax2.set_xticklabels(spectral_labels, fontsize=16)
ax2.set_xlabel("Spectral Class", fontsize=18, labelpad=12)
ax2.tick_params(axis="x", length=0)
ax2.spines["top"].set_visible(False)
ax2.spines["right"].set_visible(False)

plt.tight_layout()
plt.savefig("plot.png", dpi=300, bbox_inches="tight")
