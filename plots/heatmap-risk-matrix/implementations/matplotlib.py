""" pyplots.ai
heatmap-risk-matrix: Risk Assessment Matrix (Probability vs Impact)
Library: matplotlib 3.10.8 | Python 3.14.3
Quality: 89/100 | Created: 2026-03-17
"""

import matplotlib.patches as mpatches
import matplotlib.patheffects as pe
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.colors import LinearSegmentedColormap
from matplotlib.lines import Line2D


# Data
np.random.seed(42)

likelihood_labels = ["Rare", "Unlikely", "Possible", "Likely", "Almost\nCertain"]
impact_labels = ["Negligible", "Minor", "Moderate", "Major", "Catastrophic"]

risk_scores = np.array([[1, 2, 3, 4, 5], [2, 4, 6, 8, 10], [3, 6, 9, 12, 15], [4, 8, 12, 16, 20], [5, 10, 15, 20, 25]])

risks = [
    ("Supply Chain\nDisruption", 4, 4, "Operational"),
    ("Data Breach", 3, 5, "Technical"),
    ("Budget\nOverrun", 4, 3, "Financial"),
    ("Key Staff\nTurnover", 3, 3, "Operational"),
    ("Regulatory\nChange", 2, 4, "Financial"),
    ("Server\nOutage", 3, 4, "Technical"),
    ("Scope\nCreep", 4, 2, "Operational"),
    ("Vendor\nFailure", 2, 3, "Financial"),
    ("Cyber\nAttack", 2, 5, "Technical"),
    ("Market\nShift", 3, 2, "Financial"),
    ("Power\nFailure", 1, 4, "Technical"),
    ("Deadline\nSlip", 5, 2, "Operational"),
    ("Equipment\nWear", 1, 1, "Operational"),
    ("Minor\nDelay", 2, 1, "Financial"),
]

# Colorblind-safe colormap: light yellow -> amber -> deep orange -> dark crimson
cmap = LinearSegmentedColormap.from_list("risk_cb", ["#fef9e7", "#f9e154", "#e8882f", "#c0392b", "#7b241c"], N=256)

# Plot
fig, ax = plt.subplots(figsize=(16, 9))

# Draw zone boundary lines for visual storytelling
# Zone boundaries: Low (1-4), Medium (5-9), High (10-16), Critical (20-25)
zone_boundaries = [
    # Medium zone lower boundary (score=5 diagonal)
    ([0, 1, 2, 3, 4, 5], [4, 3, 2, 1, 1, 1]),
    # High zone lower boundary (score=10 diagonal)
    ([0, 1, 2, 3, 4, 5], [5, 5, 4, 3, 2, 2]),
    # Critical zone lower boundary (score=20 diagonal)
    ([2, 3, 4, 5], [5, 5, 5, 4]),
]

# Draw cells with rounded rectangles and score annotations
for i in range(5):
    for j in range(5):
        score = risk_scores[i, j]
        color = cmap(score / 25.0)
        rect = mpatches.FancyBboxPatch(
            (j, i), 1, 1, boxstyle="round,pad=0.02", facecolor=color, edgecolor="white", linewidth=2.5
        )
        ax.add_patch(rect)
        score_text = ax.text(
            j + 0.5,
            i + 0.12,
            str(score),
            ha="center",
            va="center",
            fontsize=18,
            fontweight="bold",
            color="white" if score >= 10 else "#444444",
            alpha=0.5,
        )
        score_text.set_path_effects([pe.withStroke(linewidth=2, foreground="white" if score < 10 else "#00000033")])

# Draw zone boundary dashed lines for storytelling
for xs, ys in zone_boundaries:
    ax.plot(xs, ys, color="#ffffff", linewidth=2.5, linestyle="--", alpha=0.6, zorder=3)

# Plot risk items with jitter and size proportional to risk score
category_colors = {"Technical": "#1a5276", "Financial": "#6c3483", "Operational": "#0e6655"}
jitter_offsets = np.random.uniform(-0.15, 0.15, (len(risks), 2))

# Label offset directions to avoid overlap (manually tuned)
label_offsets = {}
label_offsets["Key Staff\nTurnover"] = (0.0, -0.24, "top")
label_offsets["Market\nShift"] = (0.0, 0.22, "bottom")
label_offsets["Supply Chain\nDisruption"] = (0.18, -0.24, "top")
label_offsets["Server\nOutage"] = (0.15, -0.24, "top")
label_offsets["Regulatory\nChange"] = (-0.1, -0.24, "top")
label_offsets["Equipment\nWear"] = (0.0, 0.22, "bottom")
label_offsets["Minor\nDelay"] = (0.0, 0.22, "bottom")

for idx, (name, lik, imp, cat) in enumerate(risks):
    x = (imp - 1) + 0.5 + jitter_offsets[idx, 0]
    y = (lik - 1) + 0.5 + jitter_offsets[idx, 1]
    marker_color = category_colors[cat]

    # Scale marker size by risk score for visual hierarchy
    score = lik * imp
    if score >= 20:
        msize = 22
    elif score >= 10:
        msize = 18
    elif score >= 5:
        msize = 15
    else:
        msize = 12

    ax.plot(
        x,
        y,
        "o",
        markersize=msize,
        color=marker_color,
        markeredgecolor="white",
        markeredgewidth=2.5,
        zorder=5,
        alpha=0.92,
    )

    # Position labels with custom offsets where needed
    if name in label_offsets:
        dx, dy, va = label_offsets[name]
        lx, ly = x + dx, y + dy
    else:
        lx, ly, va = x, y + 0.25, "bottom"

    label = ax.text(
        lx, ly, name, ha="center", va=va, fontsize=14, fontweight="bold", color="#1a1a1a", zorder=6, linespacing=0.85
    )
    label.set_path_effects([pe.withStroke(linewidth=4.5, foreground="white")])

# Style
ax.set_xlim(0, 5)
ax.set_ylim(0, 5)
ax.set_xticks([0.5, 1.5, 2.5, 3.5, 4.5])
ax.set_xticklabels(impact_labels, fontsize=16, fontweight="medium")
ax.set_yticks([0.5, 1.5, 2.5, 3.5, 4.5])
ax.set_yticklabels(likelihood_labels, fontsize=16, fontweight="medium")
ax.set_xlabel("Impact", fontsize=20, fontweight="medium", labelpad=12)
ax.set_ylabel("Likelihood", fontsize=20, fontweight="medium", labelpad=12)
ax.set_title("heatmap-risk-matrix · matplotlib · pyplots.ai", fontsize=24, fontweight="medium", pad=20)
ax.set_aspect("equal")
ax.tick_params(axis="both", length=0)

for spine in ax.spines.values():
    spine.set_visible(False)

# Legend - categories using Line2D markers for distinctive style
cat_handles = [
    Line2D(
        [0],
        [0],
        marker="o",
        color="w",
        markerfacecolor=color,
        markersize=12,
        markeredgecolor="white",
        markeredgewidth=1.5,
        label=label,
    )
    for label, color in category_colors.items()
]

# Legend - risk zones
zone_info = [
    ("Low (1–4)", cmap(2 / 25.0)),
    ("Medium (5–9)", cmap(7 / 25.0)),
    ("High (10–16)", cmap(13 / 25.0)),
    ("Critical (20–25)", cmap(22 / 25.0)),
]
zone_handles = [
    mpatches.Patch(facecolor=color, edgecolor="#cccccc", linewidth=0.5, label=label) for label, color in zone_info
]

legend1 = ax.legend(
    handles=cat_handles,
    title="Category",
    fontsize=14,
    title_fontsize=15,
    loc="upper left",
    bbox_to_anchor=(1.01, 1.0),
    frameon=False,
    handletextpad=0.8,
)
ax.add_artist(legend1)
ax.legend(
    handles=zone_handles,
    title="Risk Level",
    fontsize=14,
    title_fontsize=15,
    loc="upper left",
    bbox_to_anchor=(1.01, 0.62),
    frameon=False,
    handletextpad=0.8,
)

# Save
plt.tight_layout()
plt.savefig("plot.png", dpi=300, bbox_inches="tight")
