"""pyplots.ai
sequence-logo-basic: Sequence Logo for Motif Visualization
Library: matplotlib 3.10.8 | Python 3.14.3
Quality: 84/100 | Created: 2026-03-06
"""

import matplotlib.pyplot as plt
import matplotlib.transforms as transforms
import numpy as np
from matplotlib.font_manager import FontProperties
from matplotlib.lines import Line2D
from matplotlib.patches import FancyBboxPatch, PathPatch
from matplotlib.textpath import TextPath


# Data — a 10-position DNA transcription factor binding site motif (ETS-family-like)
position_freqs = [
    {"A": 0.25, "C": 0.25, "G": 0.25, "T": 0.25},
    {"A": 0.10, "C": 0.60, "G": 0.10, "T": 0.20},
    {"A": 0.05, "C": 0.05, "G": 0.85, "T": 0.05},
    {"A": 0.90, "C": 0.02, "G": 0.03, "T": 0.05},
    {"A": 0.02, "C": 0.02, "G": 0.94, "T": 0.02},
    {"A": 0.02, "C": 0.02, "G": 0.02, "T": 0.94},
    {"A": 0.15, "C": 0.35, "G": 0.15, "T": 0.35},
    {"A": 0.30, "C": 0.20, "G": 0.30, "T": 0.20},
    {"A": 0.05, "C": 0.05, "G": 0.05, "T": 0.85},
    {"A": 0.25, "C": 0.25, "G": 0.25, "T": 0.25},
]

# Colorblind-safe palette: replaced green/red with teal/purple for A/T
dna_colors = {"A": "#1b7837", "C": "#1f77b4", "G": "#ff7f0e", "T": "#9467bd"}
letters = ["A", "C", "G", "T"]
n_positions = len(position_freqs)
max_bits = 2.0

# Compute information content per position
info_contents = []
for freqs in position_freqs:
    entropy = sum(-f * np.log2(f) for f in freqs.values() if f > 0)
    info_contents.append(max_bits - entropy)

# Plot
fig, ax = plt.subplots(figsize=(16, 9))
fp = FontProperties(family="DejaVu Sans", weight="bold")
bar_width = 0.9

# Highlight conserved core region (positions 3-6) with background shading
core_start, core_end = 3, 6
highlight = FancyBboxPatch(
    (core_start - 0.48, -0.02),
    core_end - core_start + 0.96,
    max_bits + 0.04,
    boxstyle="round,pad=0.02",
    facecolor="#f0e68c",
    edgecolor="#c4a000",
    alpha=0.25,
    linewidth=1.5,
    zorder=0,
)
ax.add_patch(highlight)

for pos_idx, freqs in enumerate(position_freqs):
    ic = info_contents[pos_idx]
    letter_heights = {lt: freqs[lt] * ic for lt in letters}
    sorted_letters = sorted(letters, key=lambda lt: letter_heights[lt])

    y_offset = 0.0
    x_start = pos_idx + 1 - bar_width / 2
    for letter in sorted_letters:
        h = letter_heights[letter]
        if h < 0.01:
            continue
        tp = TextPath((0, 0), letter, size=1, prop=fp)
        bbox = tp.get_extents()
        if bbox.width == 0 or bbox.height == 0:
            continue
        sx = bar_width / bbox.width
        sy = h / bbox.height
        t = transforms.Affine2D().translate(-bbox.x0, -bbox.y0).scale(sx, sy).translate(x_start, y_offset)
        patch = PathPatch(tp.transformed(t), facecolor=dna_colors[letter], edgecolor="none", linewidth=0, zorder=2)
        ax.add_patch(patch)
        y_offset += h

# Annotate conserved core motif
ax.annotate(
    "Conserved core",
    xy=((core_start + core_end) / 2, max_bits * 0.88),
    fontsize=14,
    fontweight="medium",
    color="#6b5900",
    ha="center",
    va="center",
    zorder=3,
)

# Color legend for nucleotides using matplotlib legend API

legend_handles = [
    Line2D([0], [0], marker="s", color="w", markerfacecolor=dna_colors[lt], markersize=12, label=lt, linewidth=0)
    for lt in letters
]
ax.legend(
    handles=legend_handles,
    loc="upper right",
    fontsize=14,
    framealpha=0.8,
    edgecolor="#cccccc",
    handletextpad=0.4,
    labelspacing=0.3,
)

# Style
ax.set_xlim(0.5, n_positions + 0.5)
ax.set_ylim(0, max_bits)
ax.set_xticks(range(1, n_positions + 1))
ax.set_xticklabels(range(1, n_positions + 1), fontsize=16)
ax.set_xlabel("Position", fontsize=20)
ax.set_ylabel("Information content (bits)", fontsize=20)
ax.set_title("sequence-logo-basic \u00b7 matplotlib \u00b7 pyplots.ai", fontsize=24, fontweight="medium")
ax.tick_params(axis="both", labelsize=16)
ax.spines["top"].set_visible(False)
ax.spines["right"].set_visible(False)
ax.yaxis.grid(True, alpha=0.2, linewidth=0.8, zorder=0)

plt.tight_layout()
plt.savefig("plot.png", dpi=300, bbox_inches="tight")
