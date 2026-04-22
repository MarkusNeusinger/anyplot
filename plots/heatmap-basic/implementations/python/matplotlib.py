""" pyplots.ai
heatmap-basic: Basic Heatmap
Library: matplotlib 3.10.8 | Python 3.14.3
Quality: 90/100 | Updated: 2026-02-16
"""

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.colors import TwoSlopeNorm


# Data - department correlation matrix with clear clustering patterns
# Grouped: Revenue (Sales, Marketing, Finance) cluster positively;
# Technical (Dev, Ops, Support) cluster positively; HR & Legal are distinct
departments = ["Sales", "Marketing", "Finance", "Dev", "Ops", "Support", "HR", "Legal"]
n = len(departments)

data = np.array(
    [
        [1.00, 0.82, 0.61, 0.12, 0.44, 0.35, -0.15, 0.08],  # Sales
        [0.82, 1.00, 0.48, 0.18, 0.30, 0.28, 0.10, -0.20],  # Marketing
        [0.61, 0.48, 1.00, -0.65, 0.05, -0.38, 0.30, 0.40],  # Finance
        [0.12, 0.18, -0.65, 1.00, 0.42, 0.55, -0.10, -0.30],  # Dev
        [0.44, 0.30, 0.05, 0.42, 1.00, 0.60, -0.08, 0.20],  # Ops
        [0.35, 0.28, -0.38, 0.55, 0.60, 1.00, 0.22, 0.15],  # Support
        [-0.15, 0.10, 0.30, -0.10, -0.08, 0.22, 1.00, 0.52],  # HR
        [0.08, -0.20, 0.40, -0.30, 0.20, 0.15, 0.52, 1.00],  # Legal
    ]
)

# Plot - square figure for 3600x3600 at 300 dpi
fig, ax = plt.subplots(figsize=(12, 12))

# Heatmap with RdBu_r - perceptually uniform and colorblind-friendly diverging map
norm = TwoSlopeNorm(vmin=-1, vcenter=0, vmax=1)
im = ax.imshow(data, cmap="RdBu_r", norm=norm, aspect="equal")

# Remove spines for a modern look
for spine in ax.spines.values():
    spine.set_visible(False)

# Cell separation via minor-tick grid lines
ax.set_xticks(np.arange(n + 1) - 0.5, minor=True)
ax.set_yticks(np.arange(n + 1) - 0.5, minor=True)
ax.grid(which="minor", color="white", linewidth=2)
ax.tick_params(which="minor", bottom=False, left=False)

# Tick labels
ax.set_xticks(np.arange(n))
ax.set_yticks(np.arange(n))
ax.set_xticklabels(departments, fontsize=16, rotation=45, ha="right")
ax.set_yticklabels(departments, fontsize=16)
ax.tick_params(axis="both", length=0)

# Colorbar
cbar = fig.colorbar(im, ax=ax, fraction=0.046, pad=0.04, aspect=30)
cbar.ax.tick_params(labelsize=16)
cbar.set_label("Correlation Coefficient", fontsize=18, labelpad=12)
cbar.outline.set_visible(False)

# Cell annotations - adaptive color and emphasis on strong correlations
for i in range(n):
    for j in range(n):
        val = data[i, j]
        strong = abs(val) >= 0.6 and i != j
        ax.text(
            j,
            i,
            f"{val:.2f}",
            ha="center",
            va="center",
            fontsize=16 if strong else 13,
            fontweight="bold" if strong else "medium",
            color="white" if abs(val) > 0.55 else "#333333",
        )

# Title and differentiated axis labels
ax.set_title("heatmap-basic · matplotlib · pyplots.ai", fontsize=24, fontweight="medium", pad=20)
ax.set_ylabel("Department (row)", fontsize=20, labelpad=12)
ax.set_xlabel("Department (column)", fontsize=20, labelpad=12)

plt.tight_layout()
plt.savefig("plot.png", dpi=300, bbox_inches="tight")
