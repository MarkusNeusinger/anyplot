""" pyplots.ai
pp-basic: Probability-Probability (P-P) Plot
Library: seaborn 0.13.2 | Python 3.14.3
Quality: 90/100 | Created: 2026-03-15
"""

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
from scipy import stats


# Data — Manufacturing quality control: checking if bolt tensile strengths follow a normal distribution
# Realistic scenario: a batch of steel bolts tested for tensile strength (MPa), slight right-skew from hardening variation
np.random.seed(42)
sample_size = 200
main_batch = np.random.normal(loc=520, scale=35, size=int(sample_size * 0.85))
hardened_bolts = np.random.exponential(scale=18, size=int(sample_size * 0.15)) + 560
tensile_strengths = np.concatenate([main_batch, hardened_bolts])

sorted_data = np.sort(tensile_strengths)
empirical_cdf = np.arange(1, len(sorted_data) + 1) / (len(sorted_data) + 1)

mu, sigma = stats.norm.fit(sorted_data)
theoretical_cdf = stats.norm.cdf(sorted_data, loc=mu, scale=sigma)

deviation = np.abs(empirical_cdf - theoretical_cdf)

df = pd.DataFrame(
    {
        "Theoretical CDF": theoretical_cdf,
        "Empirical CDF": empirical_cdf,
        "Deviation": deviation,
        "Region": pd.cut(theoretical_cdf, bins=[0, 0.33, 0.66, 1.0], labels=["Lower tail", "Center", "Upper tail"]),
    }
)

# Plot
sns.set_theme(
    style="whitegrid",
    rc={"axes.spines.top": False, "axes.spines.right": False, "grid.alpha": 0.2, "grid.linewidth": 0.5},
)
sns.set_context("talk", font_scale=1.1)

fig, ax = plt.subplots(figsize=(12, 12))

# Tolerance band
band_x = np.linspace(0, 1, 100)
ax.fill_between(
    band_x, band_x - 0.02, band_x + 0.02, color="#306998", alpha=0.08, zorder=0, label="±0.02 tolerance band"
)

# Reference diagonal
ax.plot([0, 1], [0, 1], color="#C84B31", linewidth=2.5, linestyle="--", alpha=0.6, zorder=1, label="Perfect normal fit")

# Scatter — use seaborn's hue + size mapping with style for region distinction
scatter = sns.scatterplot(
    data=df,
    x="Theoretical CDF",
    y="Empirical CDF",
    hue="Deviation",
    palette="viridis_r",
    size="Deviation",
    sizes=(50, 140),
    style="Region",
    markers={"Lower tail": "o", "Center": "D", "Upper tail": "s"},
    alpha=0.75,
    edgecolor="white",
    linewidth=0.5,
    ax=ax,
    legend=False,
)

# Colorbar
norm = plt.Normalize(vmin=df["Deviation"].min(), vmax=df["Deviation"].max())
sm = plt.cm.ScalarMappable(cmap="viridis_r", norm=norm)
sm.set_array([])
cbar = fig.colorbar(sm, ax=ax, shrink=0.55, aspect=25, pad=0.02)
cbar.set_label("Absolute Deviation\nfrom Normal Fit", fontsize=16)
cbar.ax.tick_params(labelsize=13)

# Annotate the region of largest deviation to tell the story
max_dev_idx = df["Deviation"].idxmax()
ax.annotate(
    f"Max deviation: {df.loc[max_dev_idx, 'Deviation']:.3f}\n(hardening skew)",
    xy=(df.loc[max_dev_idx, "Theoretical CDF"], df.loc[max_dev_idx, "Empirical CDF"]),
    xytext=(0.25, 0.82),
    fontsize=14,
    color="#333333",
    arrowprops={"arrowstyle": "->", "color": "#555555", "lw": 1.5},
    bbox={"boxstyle": "round,pad=0.4", "facecolor": "white", "edgecolor": "#cccccc", "alpha": 0.9},
)

# Style
ax.set_xlabel("Theoretical Cumulative Probability (Normal)", fontsize=20)
ax.set_ylabel("Empirical Cumulative Probability", fontsize=20)
ax.set_title("pp-basic · seaborn · pyplots.ai", fontsize=24, fontweight="medium")
ax.tick_params(axis="both", labelsize=16)
ax.set_xlim(-0.02, 1.02)
ax.set_ylim(-0.02, 1.02)
ax.set_aspect("equal")
ax.legend(fontsize=14, loc="lower right", framealpha=0.9)

plt.tight_layout()
plt.savefig("plot.png", dpi=300, bbox_inches="tight")
