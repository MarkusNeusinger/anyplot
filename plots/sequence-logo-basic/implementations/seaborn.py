"""pyplots.ai
sequence-logo-basic: Sequence Logo for Motif Visualization
Library: seaborn | Python 3.13
Quality: pending | Created: 2026-03-06
"""

import matplotlib.pyplot as plt
import matplotlib.transforms as mtransforms
import numpy as np
import seaborn as sns
from matplotlib.font_manager import FontProperties
from matplotlib.patches import PathPatch
from matplotlib.textpath import TextPath


# Data - DNA transcription factor binding site motif (10 positions)
bases = ["A", "C", "G", "T"]
base_colors = {"A": "#2ca02c", "C": "#1f77b4", "G": "#ff7f0e", "T": "#d62728"}

frequencies = np.array(
    [
        [0.05, 0.80, 0.10, 0.05],  # pos 1: strong C
        [0.70, 0.10, 0.10, 0.10],  # pos 2: strong A
        [0.05, 0.05, 0.85, 0.05],  # pos 3: strong G
        [0.10, 0.10, 0.10, 0.70],  # pos 4: strong T
        [0.25, 0.25, 0.25, 0.25],  # pos 5: no preference
        [0.60, 0.15, 0.15, 0.10],  # pos 6: moderate A
        [0.05, 0.05, 0.05, 0.85],  # pos 7: strong T
        [0.90, 0.03, 0.04, 0.03],  # pos 8: very strong A
        [0.10, 0.60, 0.20, 0.10],  # pos 9: moderate C
        [0.05, 0.05, 0.80, 0.10],  # pos 10: strong G
    ]
)

n_positions = frequencies.shape[0]

# Calculate information content (bits) per position
# IC = log2(4) + sum(f * log2(f)) = 2 + sum(f * log2(f))
info_content = np.zeros(n_positions)
for i in range(n_positions):
    entropy = sum(f * np.log2(f) for f in frequencies[i] if f > 0)
    info_content[i] = 2.0 + entropy

# Plot
sns.set_style("white")
fig, ax = plt.subplots(figsize=(16, 9))

fp = FontProperties(family="monospace", weight="bold")
letter_width = 0.8

for pos in range(n_positions):
    ic = info_content[pos]
    letter_heights = frequencies[pos] * ic
    sorted_indices = np.argsort(letter_heights)
    y_offset = 0.0

    for idx in sorted_indices:
        height = letter_heights[idx]
        if height < 0.01:
            continue

        letter = bases[idx]
        color = base_colors[letter]
        x_left = pos + 1 - letter_width / 2

        tp = TextPath((0, 0), letter, size=1, prop=fp)
        bbox = tp.get_extents()
        if bbox.width == 0 or bbox.height == 0:
            continue

        scale_x = letter_width / bbox.width
        scale_y = height / bbox.height
        tx = x_left - bbox.x0 * scale_x
        ty = y_offset - bbox.y0 * scale_y

        transform = mtransforms.Affine2D().scale(scale_x, scale_y).translate(tx, ty) + ax.transData
        patch = PathPatch(tp, facecolor=color, edgecolor="none", transform=transform)
        ax.add_patch(patch)
        y_offset += height

# Style
ax.set_xlim(0.4, n_positions + 0.6)
ax.set_ylim(0, 2.1)
ax.set_xticks(range(1, n_positions + 1))
ax.set_xlabel("Position", fontsize=20)
ax.set_ylabel("Information content (bits)", fontsize=20)
ax.set_title("sequence-logo-basic \u00b7 seaborn \u00b7 pyplots.ai", fontsize=24, fontweight="medium")
ax.tick_params(axis="both", labelsize=16)
ax.spines["top"].set_visible(False)
ax.spines["right"].set_visible(False)
ax.yaxis.grid(True, alpha=0.2, linewidth=0.8)
ax.set_axisbelow(True)

plt.tight_layout()
plt.savefig("plot.png", dpi=300, bbox_inches="tight")
