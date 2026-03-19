"""pyplots.ai
histogram-capability: Process Capability Plot with Specification Limits
Library: seaborn 0.13.2 | Python 3.14.3
Quality: 85/100 | Created: 2026-03-19
"""

import matplotlib.pyplot as plt
import numpy as np
import seaborn as sns


# Data
np.random.seed(42)
measurements = np.random.normal(loc=10.00, scale=0.015, size=200)
lsl = 9.95
usl = 10.05
target = 10.00

mean = np.mean(measurements)
sigma = np.std(measurements, ddof=1)
cp = (usl - lsl) / (6 * sigma)
cpk = min((usl - mean) / (3 * sigma), (mean - lsl) / (3 * sigma))

# Plot
sns.set_style("whitegrid", {"grid.alpha": 0.15, "grid.linewidth": 0.8})
fig, ax = plt.subplots(figsize=(16, 9))

# Histogram with seaborn KDE overlay (leveraging seaborn's integrated density estimation)
sns.histplot(
    measurements,
    bins=25,
    stat="density",
    color="#306998",
    edgecolor="white",
    linewidth=0.8,
    alpha=0.7,
    kde=True,
    line_kws={"linewidth": 3, "color": "#1a3a5c", "label": "KDE Fit"},
    ax=ax,
)

# Specification lines - colorblind-safe palette (orange for limits, teal for target)
ax.axvline(lsl, color="#e67e22", linestyle="--", linewidth=2.5, label=f"LSL = {lsl}")
ax.axvline(usl, color="#e67e22", linestyle="--", linewidth=2.5, label=f"USL = {usl}")
ax.axvline(target, color="#16a085", linestyle="-.", linewidth=2.5, label=f"Target = {target}")

# Shaded capability zones (after data is plotted so axis limits are correct)
xlim = ax.get_xlim()
ax.axvspan(lsl, usl, alpha=0.05, color="#306998", zorder=0, label="_nolegend_")
ax.axvspan(xlim[0], lsl, alpha=0.07, color="#e67e22", zorder=0, label="_nolegend_")
ax.axvspan(usl, xlim[1], alpha=0.07, color="#e67e22", zorder=0, label="_nolegend_")

# Color-coded capability annotation
cp_color = "#27ae60" if cpk >= 1.33 else "#e67e22" if cpk >= 1.0 else "#c0392b"
annotation_text = f"Cp = {cp:.2f}\nCpk = {cpk:.2f}\n\u03bc = {mean:.4f}\n\u03c3 = {sigma:.4f}"
ax.text(
    0.97,
    0.95,
    annotation_text,
    transform=ax.transAxes,
    fontsize=18,
    verticalalignment="top",
    horizontalalignment="right",
    bbox={"boxstyle": "round,pad=0.5", "facecolor": "white", "edgecolor": cp_color, "linewidth": 2, "alpha": 0.95},
    color="#2c3e50",
)

# Capability status label
status = "Capable" if cpk >= 1.33 else "Adequate" if cpk >= 1.0 else "Not Capable"
ax.text(
    0.97,
    0.72,
    status,
    transform=ax.transAxes,
    fontsize=16,
    fontweight="bold",
    verticalalignment="top",
    horizontalalignment="right",
    color=cp_color,
)

# Style
ax.set_xlabel("Shaft Diameter (mm)", fontsize=20)
ax.set_ylabel("Density", fontsize=20)
ax.set_title("histogram-capability \u00b7 seaborn \u00b7 pyplots.ai", fontsize=24, fontweight="medium")
ax.tick_params(axis="both", labelsize=16)
ax.legend(fontsize=16, loc="upper left", frameon=True, facecolor="white", edgecolor="#cccccc", framealpha=0.95)
ax.spines["top"].set_visible(False)
ax.spines["right"].set_visible(False)

plt.tight_layout()
plt.savefig("plot.png", dpi=300, bbox_inches="tight")
