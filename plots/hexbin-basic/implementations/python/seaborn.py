""" pyplots.ai
hexbin-basic: Basic Hexbin Plot
Library: seaborn 0.13.2 | Python 3.14.3
Quality: 91/100 | Updated: 2026-02-21
"""

import numpy as np
import seaborn as sns
from matplotlib.colors import LogNorm


# Data - simulate GPS coordinates for urban traffic hotspot analysis
np.random.seed(42)

# 50,000 points to demonstrate hexbin advantage over scatter
n_points = 50000

# Downtown business district - high density cluster
downtown = np.random.multivariate_normal([-73.985, 40.748], [[0.0001, 0.00005], [0.00005, 0.0001]], n_points // 2)

# Airport area - medium density cluster
airport = np.random.multivariate_normal([-73.875, 40.775], [[0.00008, -0.00003], [-0.00003, 0.00008]], n_points // 3)

# Shopping district - smaller cluster
shopping = np.random.multivariate_normal([-73.965, 40.785], [[0.00004, 0], [0, 0.00006]], n_points // 6)

longitude = np.concatenate([downtown[:, 0], airport[:, 0], shopping[:, 0]])
latitude = np.concatenate([downtown[:, 1], airport[:, 1], shopping[:, 1]])

# Plot - seaborn JointGrid with hexbin and marginal distributions
sns.set_theme(style="whitegrid", context="talk", font_scale=1.2)

g = sns.JointGrid(x=longitude, y=latitude, height=12, ratio=5, space=0.15)

# Main hexbin with log-normalized color scale for wide density variation
hb = g.ax_joint.hexbin(longitude, latitude, gridsize=35, cmap="viridis", mincnt=1, norm=LogNorm(), edgecolors="none")

# Marginal distributions - distinctive seaborn feature
g.plot_marginals(sns.kdeplot, color="#306998", fill=True, alpha=0.4, linewidth=2)

# Colorbar for density scale
cbar = g.figure.colorbar(hb, ax=g.ax_joint, pad=0.02, shrink=0.8)
cbar.set_label("Point Count (log scale)", fontsize=20)
cbar.ax.tick_params(labelsize=16)

# Style
g.ax_joint.set_xlabel("Longitude (°W)", fontsize=20)
g.ax_joint.set_ylabel("Latitude (°N)", fontsize=20)
g.ax_joint.tick_params(axis="both", labelsize=16)
g.ax_joint.grid(True, alpha=0.2, linestyle="--", linewidth=0.8)
g.ax_joint.spines["top"].set_visible(False)
g.ax_joint.spines["right"].set_visible(False)

g.figure.suptitle("hexbin-basic · seaborn · pyplots.ai", fontsize=24, y=0.98)

# Save
g.figure.tight_layout(rect=[0, 0, 1, 0.96])
g.savefig("plot.png", dpi=300, bbox_inches="tight")
