"""pyplots.ai
histogram-capability: Process Capability Plot with Specification Limits
Library: matplotlib 3.10.8 | Python 3.14.3
Quality: 89/100 | Created: 2026-03-19
"""

import matplotlib.patheffects as pe
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
import numpy as np
from scipy import stats


# Data — mean shifted from target to demonstrate Cp vs Cpk distinction
np.random.seed(42)
measurements = np.random.normal(loc=10.008, scale=0.014, size=200)
lsl = 9.95
usl = 10.05
target = 10.00

# Capability indices
mean = np.mean(measurements)
sigma = np.std(measurements, ddof=1)
cp = (usl - lsl) / (6 * sigma)
cpk = min((usl - mean) / (3 * sigma), (mean - lsl) / (3 * sigma))

# Color palette — cohesive steel-blue theme with warm accents
c_bar = "#306998"
c_curve = "#1a3a5c"
c_limit = "#b03a2e"
c_target = "#2471a3"
c_mean = "#d4840a"
c_text = "#2c3e50"

# Plot
fig, ax = plt.subplots(figsize=(16, 9), facecolor="#fafafa")
ax.set_facecolor("#fafafa")

# Histogram with gradient-like effect via layered bars
n_vals, bin_edges, patches = ax.hist(
    measurements, bins=25, density=True, alpha=0.82, color=c_bar, edgecolor="white", linewidth=1.0, zorder=3
)
for patch in patches:
    patch.set_path_effects([pe.withStroke(linewidth=1.2, foreground="white")])

# Fitted normal curve with path effect for depth
x_curve = np.linspace(measurements.min() - 0.01, measurements.max() + 0.01, 300)
y_curve = stats.norm.pdf(x_curve, mean, sigma)
ax.plot(
    x_curve,
    y_curve,
    color=c_curve,
    linewidth=3.5,
    zorder=4,
    path_effects=[pe.withStroke(linewidth=5, foreground="white", alpha=0.6)],
)

# Rejection regions shaded under the curve
x_full = np.linspace(mean - 5 * sigma, mean + 5 * sigma, 500)
y_full = stats.norm.pdf(x_full, mean, sigma)
ax.fill_between(x_full, y_full, where=(x_full < lsl), color=c_limit, alpha=0.18, zorder=2)
ax.fill_between(x_full, y_full, where=(x_full > usl), color=c_limit, alpha=0.18, zorder=2)

# Specification limits with annotation arrows using matplotlib's annotate
ax.axvline(lsl, color=c_limit, linestyle="--", linewidth=2.5, zorder=5, label=f"LSL = {lsl}")
ax.axvline(usl, color=c_limit, linestyle="--", linewidth=2.5, zorder=5, label=f"USL = {usl}")
ax.axvline(target, color=c_target, linestyle="-.", linewidth=2.5, zorder=5, label=f"Target = {target}")
ax.axvline(mean, color=c_mean, linestyle="-", linewidth=2.5, alpha=0.85, zorder=5, label=f"Mean = {mean:.4f}")

# Capability stats box with verdict — colored verdict line
verdict = "CAPABLE" if cpk >= 1.0 else "NOT CAPABLE"
verdict_color = "#1e8449" if cpk >= 1.0 else c_limit
stats_text = f"Cp   = {cp:.2f}\nCpk  = {cpk:.2f}\n\u03c3    = {sigma:.4f}\nn    = {len(measurements)}"
ax.text(
    0.97,
    0.95,
    stats_text,
    transform=ax.transAxes,
    fontsize=18,
    verticalalignment="top",
    horizontalalignment="right",
    fontfamily="monospace",
    color=c_text,
    bbox={"boxstyle": "round,pad=0.6", "facecolor": "white", "edgecolor": "#bdc3c7", "alpha": 0.92},
    zorder=6,
)
ax.text(
    0.97,
    0.68,
    verdict,
    transform=ax.transAxes,
    fontsize=20,
    fontweight="bold",
    verticalalignment="top",
    horizontalalignment="right",
    fontfamily="monospace",
    color=verdict_color,
    zorder=6,
)

# Style — refined typography and layout
ax.set_xlabel("Shaft Diameter (mm)", fontsize=20, color=c_text, labelpad=10)
ax.set_ylabel("Density", fontsize=20, color=c_text, labelpad=10)
ax.set_title(
    "histogram-capability \u00b7 matplotlib \u00b7 pyplots.ai", fontsize=24, fontweight="medium", color=c_text, pad=16
)
ax.tick_params(axis="both", labelsize=16, colors="#555555")
ax.xaxis.set_major_formatter(ticker.FormatStrFormatter("%.3f"))
ax.yaxis.grid(True, alpha=0.15, linewidth=0.6, color="#aaaaaa")
ax.legend(fontsize=16, loc="upper left", framealpha=0.9, edgecolor="#cccccc")
ax.spines["top"].set_visible(False)
ax.spines["right"].set_visible(False)
ax.spines["left"].set_color("#cccccc")
ax.spines["bottom"].set_color("#cccccc")

plt.tight_layout()
plt.savefig("plot.png", dpi=300, bbox_inches="tight", facecolor="#fafafa")
