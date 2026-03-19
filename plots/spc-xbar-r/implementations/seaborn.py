""" pyplots.ai
spc-xbar-r: Statistical Process Control Chart (X-bar/R)
Library: seaborn 0.13.2 | Python 3.14.3
Quality: 86/100 | Created: 2026-03-19
"""

import matplotlib.pyplot as plt
import numpy as np
import seaborn as sns


# Data
np.random.seed(42)

n_samples = 30
subgroup_size = 5

# Control chart constants for subgroup size 5
A2 = 0.577
D3 = 0.0
D4 = 2.114

# Simulate CNC shaft diameter measurements (target: 25.00 mm)
target = 25.00
process_std = 0.03

measurements = np.random.normal(target, process_std, (n_samples, subgroup_size))

# Inject out-of-control points
measurements[7] += 0.08
measurements[18] -= 0.09
measurements[24] += 0.10

sample_means = measurements.mean(axis=1)
sample_ranges = measurements.max(axis=1) - measurements.min(axis=1)

# Control limits for X-bar chart
xbar_bar = sample_means.mean()
r_bar = sample_ranges.mean()

xbar_ucl = xbar_bar + A2 * r_bar
xbar_lcl = xbar_bar - A2 * r_bar
xbar_upper_warn = xbar_bar + (2 / 3) * A2 * r_bar
xbar_lower_warn = xbar_bar - (2 / 3) * A2 * r_bar

# Control limits for R chart
r_ucl = D4 * r_bar
r_lcl = D3 * r_bar
r_upper_warn = r_bar + (2 / 3) * (r_ucl - r_bar)
r_lower_warn = r_bar - (2 / 3) * (r_bar - r_lcl)

sample_ids = np.arange(1, n_samples + 1)

# Identify out-of-control points
xbar_ooc = (sample_means > xbar_ucl) | (sample_means < xbar_lcl)
r_ooc = (sample_ranges > r_ucl) | (sample_ranges < r_lcl)

# Plot
fig, (ax1, ax2) = plt.subplots(
    2, 1, figsize=(16, 9), sharex=True, gridspec_kw={"height_ratios": [1, 1], "hspace": 0.12}
)

line_color = "#306998"
ooc_color = "#D64045"
cl_color = "#2A9D8F"
warn_color = "#E9C46A"

# X-bar chart
sns.lineplot(x=sample_ids, y=sample_means, ax=ax1, color=line_color, linewidth=2, marker="o", markersize=8, zorder=3)
ax1.scatter(
    sample_ids[xbar_ooc], sample_means[xbar_ooc], color=ooc_color, s=200, zorder=5, edgecolors="white", linewidth=1.5
)

ax1.axhline(xbar_bar, color=cl_color, linewidth=2, label=f"CL = {xbar_bar:.4f}")
ax1.axhline(xbar_ucl, color=ooc_color, linewidth=1.5, linestyle="--", label=f"UCL = {xbar_ucl:.4f}")
ax1.axhline(xbar_lcl, color=ooc_color, linewidth=1.5, linestyle="--", label=f"LCL = {xbar_lcl:.4f}")
ax1.axhline(xbar_upper_warn, color=warn_color, linewidth=1, linestyle=":", label=f"+2σ = {xbar_upper_warn:.4f}")
ax1.axhline(xbar_lower_warn, color=warn_color, linewidth=1, linestyle=":", label=f"−2σ = {xbar_lower_warn:.4f}")

ax1.set_ylabel("Sample Mean (mm)", fontsize=20)
ax1.set_title("spc-xbar-r · seaborn · pyplots.ai", fontsize=24, fontweight="medium", pad=16)
ax1.legend(fontsize=13, loc="upper right", framealpha=0.9)
ax1.tick_params(axis="both", labelsize=16)
ax1.spines["top"].set_visible(False)
ax1.spines["right"].set_visible(False)
ax1.yaxis.grid(True, alpha=0.2, linewidth=0.8)
ax1.text(0.01, 0.95, "X̄ Chart", transform=ax1.transAxes, fontsize=18, fontweight="bold", va="top", color="#444444")

# R chart
sns.lineplot(x=sample_ids, y=sample_ranges, ax=ax2, color=line_color, linewidth=2, marker="s", markersize=8, zorder=3)
ax2.scatter(
    sample_ids[r_ooc], sample_ranges[r_ooc], color=ooc_color, s=200, zorder=5, edgecolors="white", linewidth=1.5
)

ax2.axhline(r_bar, color=cl_color, linewidth=2, label=f"CL = {r_bar:.4f}")
ax2.axhline(r_ucl, color=ooc_color, linewidth=1.5, linestyle="--", label=f"UCL = {r_ucl:.4f}")
ax2.axhline(r_lcl, color=ooc_color, linewidth=1.5, linestyle="--", label=f"LCL = {r_lcl:.4f}")
ax2.axhline(r_upper_warn, color=warn_color, linewidth=1, linestyle=":", label=f"+2σ = {r_upper_warn:.4f}")
ax2.axhline(r_lower_warn, color=warn_color, linewidth=1, linestyle=":", label=f"−2σ = {r_lower_warn:.4f}")

ax2.set_xlabel("Sample Number", fontsize=20)
ax2.set_ylabel("Sample Range (mm)", fontsize=20)
ax2.legend(fontsize=13, loc="upper right", framealpha=0.9)
ax2.tick_params(axis="both", labelsize=16)
ax2.spines["top"].set_visible(False)
ax2.spines["right"].set_visible(False)
ax2.yaxis.grid(True, alpha=0.2, linewidth=0.8)
ax2.text(0.01, 0.95, "R Chart", transform=ax2.transAxes, fontsize=18, fontweight="bold", va="top", color="#444444")

# Save
plt.savefig("plot.png", dpi=300, bbox_inches="tight")
