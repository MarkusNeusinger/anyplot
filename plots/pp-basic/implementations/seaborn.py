""" pyplots.ai
pp-basic: Probability-Probability (P-P) Plot
Library: seaborn 0.13.2 | Python 3.14.3
Quality: 87/100 | Created: 2026-03-15
"""

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
from scipy import stats


# Data
np.random.seed(42)
sample_size = 200
normal_component = np.random.normal(loc=50, scale=10, size=int(sample_size * 0.85))
skewed_component = np.random.exponential(scale=5, size=int(sample_size * 0.15)) + 55
observed = np.concatenate([normal_component, skewed_component])

sorted_data = np.sort(observed)
empirical_cdf = np.arange(1, len(sorted_data) + 1) / (len(sorted_data) + 1)

mu, sigma = stats.norm.fit(sorted_data)
theoretical_cdf = stats.norm.cdf(sorted_data, loc=mu, scale=sigma)

deviation = np.abs(empirical_cdf - theoretical_cdf)

df = pd.DataFrame({"Theoretical CDF": theoretical_cdf, "Empirical CDF": empirical_cdf, "Deviation": deviation})

# Plot
sns.set_theme(
    style="whitegrid",
    rc={"axes.spines.top": False, "axes.spines.right": False, "grid.alpha": 0.25, "grid.linewidth": 0.6},
)
sns.set_context("talk", font_scale=1.1)

fig, ax = plt.subplots(figsize=(12, 12))

ax.plot([0, 1], [0, 1], color="#C84B31", linewidth=2.5, linestyle="--", alpha=0.6, zorder=1, label="Perfect fit")

sns.scatterplot(
    data=df,
    x="Theoretical CDF",
    y="Empirical CDF",
    hue="Deviation",
    palette="flare",
    size="Deviation",
    sizes=(30, 120),
    alpha=0.75,
    edgecolor="white",
    linewidth=0.4,
    ax=ax,
    legend=False,
)

norm = plt.Normalize(vmin=df["Deviation"].min(), vmax=df["Deviation"].max())
sm = plt.cm.ScalarMappable(cmap="flare", norm=norm)
sm.set_array([])
cbar = fig.colorbar(sm, ax=ax, shrink=0.6, aspect=25, pad=0.03)
cbar.set_label("Absolute Deviation from\nPerfect Fit", fontsize=16)
cbar.ax.tick_params(labelsize=13)

ax.fill_between(
    np.linspace(0, 1, 100),
    np.linspace(0, 1, 100) - 0.02,
    np.linspace(0, 1, 100) + 0.02,
    color="#306998",
    alpha=0.08,
    zorder=0,
    label="±0.02 tolerance band",
)

# Style
ax.set_xlabel("Theoretical Cumulative Probability", fontsize=20)
ax.set_ylabel("Empirical Cumulative Probability", fontsize=20)
ax.set_title("pp-basic · seaborn · pyplots.ai", fontsize=24, fontweight="medium")
ax.tick_params(axis="both", labelsize=16)
ax.set_xlim(-0.02, 1.02)
ax.set_ylim(-0.02, 1.02)
ax.set_aspect("equal")
ax.legend(fontsize=14, loc="lower right", framealpha=0.9)

plt.tight_layout()
plt.savefig("plot.png", dpi=300, bbox_inches="tight")
