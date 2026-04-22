""" pyplots.ai
sequence-logo-basic: Sequence Logo for Motif Visualization
Library: seaborn 0.13.2 | Python 3.14.3
Quality: 92/100 | Created: 2026-03-06
"""

import matplotlib.pyplot as plt
import matplotlib.transforms as mtransforms
import numpy as np
import pandas as pd
import seaborn as sns
from matplotlib.font_manager import FontProperties
from matplotlib.patches import PathPatch
from matplotlib.textpath import TextPath


# Data - DNA transcription factor binding site motif (10 positions)
bases = ["A", "C", "G", "T"]

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

# Standard DNA color scheme via seaborn palette management
base_color_list = ["#3AA655", "#4169E1", "#F5A623", "#E74C3C"]
base_palette = sns.color_palette(base_color_list)
base_colors = dict(zip(bases, base_palette, strict=True))

# Build frequency DataFrame for heatmap
freq_df = pd.DataFrame(frequencies.T, index=bases, columns=range(1, n_positions + 1))

# Plot setup with seaborn context and style
sns.set_context("talk", font_scale=1.0)
sns.set_style("white")
fig, (ax_logo, ax_heat) = plt.subplots(2, 1, figsize=(16, 9), height_ratios=[3.5, 1], gridspec_kw={"hspace": 0.45})

# --- Top panel: Sequence Logo ---
fp = FontProperties(family="monospace", weight="bold")
letter_width = 0.78

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
        x_center = pos
        x_left = x_center - letter_width / 2

        tp = TextPath((0, 0), letter, size=1, prop=fp)
        bbox = tp.get_extents()
        if bbox.width == 0 or bbox.height == 0:
            continue

        scale_x = letter_width / bbox.width
        scale_y = height / bbox.height
        tx = x_left - bbox.x0 * scale_x
        ty = y_offset - bbox.y0 * scale_y

        transform = mtransforms.Affine2D().scale(scale_x, scale_y).translate(tx, ty) + ax_logo.transData
        patch = PathPatch(tp, facecolor=color, edgecolor="none", transform=transform)
        ax_logo.add_patch(patch)
        y_offset += height

# Logo axis styling
ax_logo.set_xlim(-0.6, n_positions - 0.4)
ax_logo.set_ylim(0, 2.1)
ax_logo.set_xticks(range(n_positions))
ax_logo.set_xticklabels(range(1, n_positions + 1))
ax_logo.set_xlabel("Position", fontsize=20)
ax_logo.set_ylabel("Information content (bits)", fontsize=20)
ax_logo.set_title("sequence-logo-basic \u00b7 seaborn \u00b7 pyplots.ai", fontsize=24, fontweight="medium", pad=15)
ax_logo.tick_params(axis="both", labelsize=16)
sns.despine(ax=ax_logo, top=True, right=True)
ax_logo.yaxis.grid(True, alpha=0.15, linewidth=0.5, color="#cccccc")
ax_logo.set_axisbelow(True)

# Highlight the most conserved position
max_ic_pos = int(np.argmax(info_content))
ax_logo.axvspan(max_ic_pos - 0.42, max_ic_pos + 0.42, color="#ffd700", alpha=0.12, zorder=0)

# Conservation annotation
ax_logo.annotate(
    f"Most conserved\n({info_content[max_ic_pos]:.1f} bits)",
    xy=(max_ic_pos, info_content[max_ic_pos]),
    xytext=(max_ic_pos - 2.5, 1.90),
    fontsize=13,
    fontstyle="italic",
    color="#444444",
    arrowprops={"arrowstyle": "->", "color": "#888888", "lw": 1.3, "connectionstyle": "arc3,rad=-0.2"},
    ha="center",
    va="center",
)

# --- Bottom panel: Frequency heatmap using seaborn ---
sns.heatmap(
    freq_df,
    ax=ax_heat,
    cmap=sns.light_palette("#306998", as_cmap=True),
    annot=True,
    fmt=".2f",
    annot_kws={"fontsize": 12, "fontweight": "medium"},
    linewidths=1.5,
    linecolor="white",
    cbar_kws={"label": "Frequency", "shrink": 0.8, "aspect": 15, "pad": 0.02},
    vmin=0,
    vmax=1,
    square=False,
)
ax_heat.set_xlabel("Position", fontsize=16)
ax_heat.set_ylabel("", fontsize=16)
ax_heat.tick_params(axis="both", labelsize=14)
ax_heat.tick_params(axis="y", rotation=0)

# Color the y-axis base labels to match the logo colors
for tick_label in ax_heat.get_yticklabels():
    base = tick_label.get_text()
    if base in base_colors:
        tick_label.set_color(base_colors[base])
        tick_label.set_fontweight("bold")

plt.savefig("plot.png", dpi=300, bbox_inches="tight")
