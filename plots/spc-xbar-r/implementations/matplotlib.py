"""pyplots.ai
spc-xbar-r: Statistical Process Control Chart (X-bar/R)
Library: matplotlib | Python 3.13
Quality: pending | Created: 2026-03-19
"""

import matplotlib.pyplot as plt
import numpy as np


# Data - CNC shaft diameter measurements (subgroups of n=5)
np.random.seed(42)
n_samples = 30
subgroup_size = 5
target_diameter = 25.0
process_std = 0.05

# Control chart constants for n=5
A2 = 0.577
D3 = 0.0
D4 = 2.114

# Generate subgroup measurements (mostly in-control with a few shifts)
measurements = np.random.normal(target_diameter, process_std, (n_samples, subgroup_size))

# Inject out-of-control points
measurements[7] += 0.15
measurements[18] -= 0.18
measurements[24] += 0.20

sample_ids = np.arange(1, n_samples + 1)
sample_means = measurements.mean(axis=1)
sample_ranges = measurements.max(axis=1) - measurements.min(axis=1)

# X-bar chart limits
xbar_bar = sample_means.mean()
r_bar = sample_ranges.mean()
xbar_ucl = xbar_bar + A2 * r_bar
xbar_lcl = xbar_bar - A2 * r_bar
xbar_upper_warn = xbar_bar + (2 / 3) * A2 * r_bar
xbar_lower_warn = xbar_bar - (2 / 3) * A2 * r_bar

# R chart limits
r_ucl = D4 * r_bar
r_lcl = D3 * r_bar
r_upper_warn = r_bar + (2 / 3) * (r_ucl - r_bar)
r_lower_warn = r_bar - (2 / 3) * (r_bar - r_lcl)

# Identify out-of-control points
xbar_ooc = (sample_means > xbar_ucl) | (sample_means < xbar_lcl)
r_ooc = (sample_ranges > r_ucl) | (sample_ranges < r_lcl)

# Plot
fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(16, 9), sharex=True, gridspec_kw={"height_ratios": [1, 1]})

# Colors
blue = "#306998"
red = "#D9534F"
gray_line = "#888888"
warn_color = "#E8A838"

# --- X-bar chart ---
ax1.plot(
    sample_ids,
    sample_means,
    color=blue,
    linewidth=2.5,
    marker="o",
    markersize=8,
    markerfacecolor=blue,
    markeredgecolor="white",
    markeredgewidth=1,
    zorder=3,
)
ax1.scatter(sample_ids[xbar_ooc], sample_means[xbar_ooc], color=red, s=250, zorder=4, edgecolors="white", linewidth=1.5)

ax1.axhline(xbar_bar, color=gray_line, linewidth=2, linestyle="-", label="CL")
ax1.axhline(xbar_ucl, color=red, linewidth=2, linestyle="--", label="UCL / LCL")
ax1.axhline(xbar_lcl, color=red, linewidth=2, linestyle="--")
ax1.axhline(xbar_upper_warn, color=warn_color, linewidth=1.5, linestyle=":", alpha=0.8, label="±2σ Warning")
ax1.axhline(xbar_lower_warn, color=warn_color, linewidth=1.5, linestyle=":", alpha=0.8)

ax1.text(n_samples + 0.5, xbar_ucl, "UCL", fontsize=14, color=red, va="center", fontweight="bold")
ax1.text(n_samples + 0.5, xbar_lcl, "LCL", fontsize=14, color=red, va="center", fontweight="bold")
ax1.text(n_samples + 0.5, xbar_bar, "CL", fontsize=14, color=gray_line, va="center", fontweight="bold")

ax1.set_ylabel("Sample Mean (X̄)", fontsize=20)
ax1.set_title("spc-xbar-r · matplotlib · pyplots.ai", fontsize=24, fontweight="medium")
ax1.legend(fontsize=14, loc="upper left", framealpha=0.9)
ax1.tick_params(axis="both", labelsize=16)
ax1.spines["top"].set_visible(False)
ax1.spines["right"].set_visible(False)
ax1.yaxis.grid(True, alpha=0.2, linewidth=0.8)

# --- R chart ---
ax2.plot(
    sample_ids,
    sample_ranges,
    color=blue,
    linewidth=2.5,
    marker="s",
    markersize=8,
    markerfacecolor=blue,
    markeredgecolor="white",
    markeredgewidth=1,
    zorder=3,
)
ax2.scatter(sample_ids[r_ooc], sample_ranges[r_ooc], color=red, s=250, zorder=4, edgecolors="white", linewidth=1.5)

ax2.axhline(r_bar, color=gray_line, linewidth=2, linestyle="-")
ax2.axhline(r_ucl, color=red, linewidth=2, linestyle="--")
if r_lcl > 0:
    ax2.axhline(r_lcl, color=red, linewidth=2, linestyle="--")

ax2.axhline(r_upper_warn, color=warn_color, linewidth=1.5, linestyle=":", alpha=0.8)
if r_lower_warn > 0:
    ax2.axhline(r_lower_warn, color=warn_color, linewidth=1.5, linestyle=":", alpha=0.8)

ax2.text(n_samples + 0.5, r_ucl, "UCL", fontsize=14, color=red, va="center", fontweight="bold")
ax2.text(n_samples + 0.5, r_bar, "CL", fontsize=14, color=gray_line, va="center", fontweight="bold")

ax2.set_xlabel("Sample Number", fontsize=20)
ax2.set_ylabel("Sample Range (R)", fontsize=20)
ax2.tick_params(axis="both", labelsize=16)
ax2.spines["top"].set_visible(False)
ax2.spines["right"].set_visible(False)
ax2.yaxis.grid(True, alpha=0.2, linewidth=0.8)

fig.subplots_adjust(hspace=0.15)
plt.savefig("plot.png", dpi=300, bbox_inches="tight")
