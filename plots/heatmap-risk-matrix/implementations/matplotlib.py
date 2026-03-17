"""pyplots.ai
heatmap-risk-matrix: Risk Assessment Matrix (Probability vs Impact)
Library: matplotlib 3.10.8 | Python 3.14.3
Quality: 82/100 | Created: 2026-03-17
"""

import matplotlib.patches as mpatches
import matplotlib.patheffects as pe
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.colors import LinearSegmentedColormap


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
    ("Market\nShift", 3, 3, "Financial"),
    ("Power\nFailure", 1, 4, "Technical"),
    ("Deadline\nSlip", 5, 2, "Operational"),
]

# Colorblind-safe colormap: light yellow -> amber -> deep orange -> dark crimson
cmap = LinearSegmentedColormap.from_list("risk_cb", ["#fef9e7", "#f9e154", "#e8882f", "#c0392b", "#7b241c"], N=256)

# Plot
fig, ax = plt.subplots(figsize=(16, 9))

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
            i + 0.15,
            str(score),
            ha="center",
            va="center",
            fontsize=16,
            fontweight="bold",
            color="white" if score >= 10 else "#444444",
            alpha=0.55,
        )
        score_text.set_path_effects([pe.withStroke(linewidth=1.5, foreground="white" if score < 10 else "#00000033")])

# Plot risk items with jitter and size proportional to risk score
category_colors = {"Technical": "#1a5276", "Financial": "#6c3483", "Operational": "#0e6655"}
jitter_offsets = np.random.uniform(-0.18, 0.18, (len(risks), 2))

# Label offset directions to avoid overlap (manually tuned for crowded cells)
# Format: (dx, dy, va) relative to marker position
label_offsets = {}
# Key Staff Turnover and Market Shift both at (3,3) - offset labels in different directions
label_offsets["Key Staff\nTurnover"] = (0.0, -0.22, "top")
label_offsets["Market\nShift"] = (0.0, 0.25, "bottom")
# Supply Chain Disruption at (4,4) marker at ~(3.45, 3.66) - label below to stay in cell
label_offsets["Supply Chain\nDisruption"] = (0.15, -0.22, "top")
# Server Outage at (3,4) marker at ~(3.33, 2.67) - label below
label_offsets["Server\nOutage"] = (0.15, -0.22, "top")

for idx, (name, lik, imp, cat) in enumerate(risks):
    x = (imp - 1) + 0.5 + jitter_offsets[idx, 0]
    y = (lik - 1) + 0.5 + jitter_offsets[idx, 1]
    marker_color = category_colors[cat]

    # Scale marker size by risk score for visual hierarchy
    score = lik * imp
    if score >= 20:
        msize = 20
    elif score >= 10:
        msize = 17
    elif score >= 5:
        msize = 14
    else:
        msize = 11

    ax.plot(x, y, "o", markersize=msize, color=marker_color, markeredgecolor="white", markeredgewidth=2, zorder=5)

    # Position labels with custom offsets where needed
    if name in label_offsets:
        dx, dy, va = label_offsets[name]
        lx, ly = x + dx, y + dy
    else:
        lx, ly, va = x, y + 0.27, "bottom"

    label = ax.text(
        lx, ly, name, ha="center", va=va, fontsize=12, fontweight="bold", color="#1a1a1a", zorder=6, linespacing=0.85
    )
    label.set_path_effects([pe.withStroke(linewidth=4, foreground="white")])

# Style
ax.set_xlim(0, 5)
ax.set_ylim(0, 5)
ax.set_xticks([0.5, 1.5, 2.5, 3.5, 4.5])
ax.set_xticklabels(impact_labels, fontsize=16)
ax.set_yticks([0.5, 1.5, 2.5, 3.5, 4.5])
ax.set_yticklabels(likelihood_labels, fontsize=16)
ax.set_xlabel("Impact", fontsize=20, fontweight="medium", labelpad=12)
ax.set_ylabel("Likelihood", fontsize=20, fontweight="medium", labelpad=12)
ax.set_title("heatmap-risk-matrix · matplotlib · pyplots.ai", fontsize=24, fontweight="medium", pad=20)
ax.set_aspect("equal")
ax.tick_params(axis="both", length=0)

for spine in ax.spines.values():
    spine.set_visible(False)

# Legend - categories
cat_handles = [
    mpatches.Patch(facecolor=color, edgecolor="white", label=label) for label, color in category_colors.items()
]
# Legend - risk zones
zone_info = [
    ("Low (1–4)", cmap(2 / 25.0)),
    ("Medium (5–9)", cmap(7 / 25.0)),
    ("High (10–16)", cmap(13 / 25.0)),
    ("Critical (20–25)", cmap(22 / 25.0)),
]
zone_handles = [mpatches.Patch(facecolor=color, edgecolor="white", label=label) for label, color in zone_info]

legend1 = ax.legend(
    handles=cat_handles,
    title="Category",
    fontsize=13,
    title_fontsize=14,
    loc="upper left",
    bbox_to_anchor=(1.01, 1.0),
    frameon=False,
)
ax.add_artist(legend1)
ax.legend(
    handles=zone_handles,
    title="Risk Level",
    fontsize=13,
    title_fontsize=14,
    loc="upper left",
    bbox_to_anchor=(1.01, 0.6),
    frameon=False,
)

# Save
plt.tight_layout()
plt.savefig("plot.png", dpi=300, bbox_inches="tight")
