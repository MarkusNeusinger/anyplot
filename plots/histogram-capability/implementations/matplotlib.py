""" pyplots.ai
histogram-capability: Process Capability Plot with Specification Limits
Library: matplotlib 3.10.8 | Python 3.14.3
Quality: 89/100 | Created: 2026-03-19
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

ax.hist(measurements, bins=25, density=True, alpha=0.7, color="#306998", edgecolor="white", linewidth=0.8, zorder=3)

x_curve = np.linspace(measurements.min() - 0.01, measurements.max() + 0.01, 300)
y_curve = stats.norm.pdf(x_curve, mean, sigma)
ax.plot(x_curve, y_curve, color="#1a3a5c", linewidth=3, zorder=4)

# Rejection regions (shaded areas beyond spec limits) — distinctive matplotlib fill_between
x_full = np.linspace(mean - 5 * sigma, mean + 5 * sigma, 500)
y_full = stats.norm.pdf(x_full, mean, sigma)
ax.fill_between(x_full, y_full, where=(x_full < lsl), color="#c0392b", alpha=0.15, zorder=2)
ax.fill_between(x_full, y_full, where=(x_full > usl), color="#c0392b", alpha=0.15, zorder=2)

# Specification limits and target — colorblind-safe palette (no red-green pairing)
ax.axvline(lsl, color="#c0392b", linestyle="--", linewidth=2.5, zorder=5, label=f"LSL = {lsl}")
ax.axvline(usl, color="#c0392b", linestyle="--", linewidth=2.5, zorder=5, label=f"USL = {usl}")
ax.axvline(target, color="#2980b9", linestyle="-.", linewidth=2.5, zorder=5, label=f"Target = {target}")
ax.axvline(mean, color="#e67e22", linestyle="-", linewidth=2.5, alpha=0.8, zorder=5, label=f"Mean = {mean:.4f}")

# Capability annotation with process verdict
verdict = "CAPABLE" if cpk >= 1.0 else "NOT CAPABLE"
verdict_color = "#27ae60" if cpk >= 1.0 else "#c0392b"
ax.text(
    0.97,
    0.95,
    f"Cp  = {cp:.2f}\nCpk = {cpk:.2f}\n\u03c3   = {sigma:.4f}\nn    = {len(measurements)}\n\n{verdict}",
    transform=ax.transAxes,
    fontsize=18,
    verticalalignment="top",
    horizontalalignment="right",
    bbox={"boxstyle": "round,pad=0.5", "facecolor": "white", "edgecolor": "#cccccc", "alpha": 0.9},
    fontfamily="monospace",
    color="#333333",
    zorder=6,
)

# Style
ax.set_xlabel("Shaft Diameter (mm)", fontsize=20)
ax.set_ylabel("Density", fontsize=20)
ax.set_title("histogram-capability \u00b7 matplotlib \u00b7 pyplots.ai", fontsize=24, fontweight="medium")
ax.tick_params(axis="both", labelsize=16)
ax.yaxis.grid(True, alpha=0.2, linewidth=0.8)
ax.legend(fontsize=16, loc="upper left")
ax.spines["top"].set_visible(False)
ax.spines["right"].set_visible(False)

plt.tight_layout()
plt.savefig("plot.png", dpi=300, bbox_inches="tight")
