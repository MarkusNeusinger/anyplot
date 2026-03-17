"""pyplots.ai
heatmap-risk-matrix: Risk Assessment Matrix (Probability vs Impact)
Library: matplotlib | Python 3.13
Quality: pending | Created: 2026-03-17
"""

import matplotlib.patches as mpatches
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

# Color map: green -> yellow -> orange -> red
cmap = LinearSegmentedColormap.from_list("risk", ["#2ecc71", "#f1c40f", "#e67e22", "#e74c3c", "#c0392b"], N=256)

# Plot
fig, ax = plt.subplots(figsize=(16, 9))

for i in range(5):
    for j in range(5):
        score = risk_scores[i, j]
        color = cmap(score / 25.0)
        rect = mpatches.FancyBboxPatch(
            (j, i), 1, 1, boxstyle="round,pad=0.02", facecolor=color, edgecolor="white", linewidth=2
        )
        ax.add_patch(rect)
        ax.text(
            j + 0.5,
            i + 0.15,
            str(score),
            ha="center",
            va="center",
            fontsize=14,
            fontweight="bold",
            color="white" if score >= 10 else "#333333",
            alpha=0.6,
        )

# Plot risk items with jitter
category_colors = {"Technical": "#1a5276", "Financial": "#4a235a", "Operational": "#0e6655"}
jitter_offsets = np.random.uniform(-0.2, 0.2, (len(risks), 2))

for idx, (name, lik, imp, cat) in enumerate(risks):
    x = (imp - 1) + 0.5 + jitter_offsets[idx, 0]
    y = (lik - 1) + 0.5 + jitter_offsets[idx, 1]
    marker_color = category_colors[cat]
    ax.plot(x, y, "o", markersize=14, color=marker_color, markeredgecolor="white", markeredgewidth=1.5, zorder=5)
    ax.text(x, y + 0.25, name, ha="center", va="bottom", fontsize=9, fontweight="bold", color="#1a1a1a", zorder=6)

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
