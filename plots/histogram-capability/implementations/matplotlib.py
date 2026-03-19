"""pyplots.ai
histogram-capability: Process Capability Plot with Specification Limits
Library: matplotlib | Python 3.13
Quality: pending | Created: 2026-03-19
"""

import matplotlib.pyplot as plt
import numpy as np
from scipy import stats


# Data
np.random.seed(42)
measurements = np.random.normal(loc=10.00, scale=0.015, size=200)
lsl = 9.95
usl = 10.05
target = 10.00

# Capability indices
mean = np.mean(measurements)
sigma = np.std(measurements, ddof=1)
cp = (usl - lsl) / (6 * sigma)
cpk = min((usl - mean) / (3 * sigma), (mean - lsl) / (3 * sigma))

# Plot
fig, ax = plt.subplots(figsize=(16, 9))

ax.hist(measurements, bins=25, density=True, alpha=0.7, color="#306998", edgecolor="white", linewidth=0.8)

x_curve = np.linspace(measurements.min() - 0.01, measurements.max() + 0.01, 300)
y_curve = stats.norm.pdf(x_curve, mean, sigma)
ax.plot(x_curve, y_curve, color="#1a3a5c", linewidth=3)

# Specification limits and target
ax.axvline(lsl, color="#c0392b", linestyle="--", linewidth=2.5, label=f"LSL = {lsl}")
ax.axvline(usl, color="#c0392b", linestyle="--", linewidth=2.5, label=f"USL = {usl}")
ax.axvline(target, color="#27ae60", linestyle="--", linewidth=2.5, label=f"Target = {target}")
ax.axvline(mean, color="#e67e22", linestyle="-", linewidth=2.5, alpha=0.8, label=f"Mean = {mean:.4f}")

# Capability annotation
ax.text(
    0.97,
    0.95,
    f"Cp  = {cp:.2f}\nCpk = {cpk:.2f}\n\u03c3   = {sigma:.4f}\nn    = {len(measurements)}",
    transform=ax.transAxes,
    fontsize=18,
    verticalalignment="top",
    horizontalalignment="right",
    bbox={"boxstyle": "round,pad=0.5", "facecolor": "white", "edgecolor": "#cccccc", "alpha": 0.9},
    fontfamily="monospace",
)

# Style
ax.set_xlabel("Shaft Diameter (mm)", fontsize=20)
ax.set_ylabel("Density", fontsize=20)
ax.set_title("histogram-capability \u00b7 matplotlib \u00b7 pyplots.ai", fontsize=24, fontweight="medium")
ax.tick_params(axis="both", labelsize=16)
ax.legend(fontsize=16, loc="upper left")
ax.spines["top"].set_visible(False)
ax.spines["right"].set_visible(False)

plt.tight_layout()
plt.savefig("plot.png", dpi=300, bbox_inches="tight")
