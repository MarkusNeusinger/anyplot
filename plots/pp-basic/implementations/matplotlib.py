"""pyplots.ai
pp-basic: Probability-Probability (P-P) Plot
Library: matplotlib 3.10.8 | Python 3.14.3
Quality: 75/100 | Created: 2026-03-15
"""

import os as _os
import sys as _sys


# Avoid filename shadowing: remove script dir so 'matplotlib' resolves to the real package
_script_dir = _os.path.abspath(_os.path.dirname(__file__))
_sys.path = [
    p for p in _sys.path if _os.path.abspath(p) != _script_dir and not (p == "" and _os.getcwd() == _script_dir)
]
_sys.modules.pop("matplotlib", None)

from math import erf, sqrt  # noqa: E402

import matplotlib.patheffects as pe  # noqa: E402
import matplotlib.pyplot as plt  # noqa: E402
import matplotlib.ticker as mticker  # noqa: E402
import numpy as np  # noqa: E402


_sys.path.insert(0, _script_dir)

# Vectorized normal CDF without scipy
normal_cdf = np.vectorize(lambda x: 0.5 * (1 + erf(x / sqrt(2))))

# Data — manufacturing quality control: bolt tensile strength measurements
# Mixture simulates a batch with ~20% from a slightly different supplier
np.random.seed(42)
sample_size = 200
primary_batch = np.random.normal(loc=840, scale=35, size=160)  # MPa
secondary_batch = np.random.normal(loc=910, scale=28, size=40)  # MPa
tensile_strength = np.concatenate([primary_batch, secondary_batch])

observed_sorted = np.sort(tensile_strength)
empirical_cdf = np.arange(1, sample_size + 1) / (sample_size + 1)

mu, sigma = observed_sorted.mean(), observed_sorted.std(ddof=0)
theoretical_cdf = normal_cdf((observed_sorted - mu) / sigma)

# Deviation from diagonal for color-coding
deviation = empirical_cdf - theoretical_cdf

# Plot
fig, ax = plt.subplots(figsize=(12, 12))

# 95% confidence band using order-statistic variance
band_x = np.linspace(0, 1, 200)
se = np.sqrt(band_x * (1 - band_x) / sample_size)
ax.fill_between(
    band_x, band_x - 1.96 * se, band_x + 1.96 * se, color="#306998", alpha=0.08, zorder=0, label="95% confidence band"
)

# Reference line with path effect for visual depth
ref_line = ax.plot([0, 1], [0, 1], color="#888888", linewidth=1.8, linestyle="--", zorder=1, label="Perfect normal fit")
ref_line[0].set_path_effects([pe.Stroke(linewidth=3.5, foreground="#DDDDDD"), pe.Normal()])

# Scatter — color encodes deviation magnitude for storytelling
colors = np.where(np.abs(deviation) > 0.03, "#C44E52", "#306998")
ax.scatter(theoretical_cdf, empirical_cdf, s=70, c=colors, alpha=0.65, edgecolors="white", linewidth=0.6, zorder=3)

# Annotate the S-shaped deviation region
dev_mask = np.abs(deviation) > 0.03
if dev_mask.any():
    dev_indices = np.where(dev_mask)[0]
    mid = dev_indices[len(dev_indices) // 2]
    ax.annotate(
        "Heavier upper tail\n(secondary supplier batch)",
        xy=(theoretical_cdf[mid], empirical_cdf[mid]),
        xytext=(0.25, 0.82),
        fontsize=14,
        color="#C44E52",
        fontweight="medium",
        arrowprops={"arrowstyle": "-|>", "color": "#C44E52", "lw": 1.5, "connectionstyle": "arc3,rad=-0.2"},
        bbox={"boxstyle": "round,pad=0.4", "facecolor": "white", "edgecolor": "#C44E52", "alpha": 0.9},
        zorder=5,
    )

# Style
ax.set_xlabel("Theoretical Cumulative Probability (Normal)", fontsize=20)
ax.set_ylabel("Empirical Cumulative Probability", fontsize=20)
ax.set_title("pp-basic · matplotlib · pyplots.ai", fontsize=24, fontweight="medium", pad=12)
ax.tick_params(axis="both", labelsize=16)
ax.xaxis.set_major_locator(mticker.MultipleLocator(0.2))
ax.yaxis.set_major_locator(mticker.MultipleLocator(0.2))
ax.xaxis.set_minor_locator(mticker.MultipleLocator(0.1))
ax.yaxis.set_minor_locator(mticker.MultipleLocator(0.1))
ax.set_xlim(-0.02, 1.02)
ax.set_ylim(-0.02, 1.02)
ax.set_aspect("equal")
ax.spines["top"].set_visible(False)
ax.spines["right"].set_visible(False)
ax.spines["left"].set_linewidth(0.8)
ax.spines["bottom"].set_linewidth(0.8)
ax.spines["left"].set_color("#555555")
ax.spines["bottom"].set_color("#555555")
ax.yaxis.grid(True, alpha=0.15, linewidth=0.6, which="major")
ax.xaxis.grid(True, alpha=0.15, linewidth=0.6, which="major")
ax.yaxis.grid(True, alpha=0.06, linewidth=0.4, which="minor")
ax.xaxis.grid(True, alpha=0.06, linewidth=0.4, which="minor")

# Legend
ax.legend(fontsize=14, loc="lower right", framealpha=0.9, edgecolor="#CCCCCC")

# Subtitle with domain context
fig.text(
    0.5,
    0.96,
    "Bolt tensile strength (MPa) vs. normal distribution — quality control diagnostic",
    ha="center",
    fontsize=14,
    color="#666666",
    style="italic",
)

plt.subplots_adjust(top=0.91)
plt.savefig("plot.png", dpi=300, bbox_inches="tight")
