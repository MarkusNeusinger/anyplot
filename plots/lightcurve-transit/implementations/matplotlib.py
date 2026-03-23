""" pyplots.ai
lightcurve-transit: Astronomical Light Curve
Library: matplotlib 3.10.8 | Python 3.14.3
Quality: 92/100 | Created: 2026-03-18
"""

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.patches import FancyArrowPatch


# Data
np.random.seed(42)

transit_center = 0.5
transit_duration = 0.08
transit_depth = 0.01
u1, u2 = 0.3, 0.1
half_dur = transit_duration / 2.0
n_points = 500

# Phase-folded observations
phase = np.sort(np.random.uniform(0.0, 1.0, n_points))

# Quadratic limb-darkened transit model for observations
model_flux = np.ones(n_points)
in_transit = np.abs(phase - transit_center) < half_dur
z = np.abs(phase[in_transit] - transit_center) / half_dur
limb = 1.0 - u1 * (1 - np.sqrt(1 - z**2)) - u2 * (1 - np.sqrt(1 - z**2)) ** 2
model_flux[in_transit] = 1.0 - transit_depth * limb

# Simulated photometry with realistic noise
flux_err = np.random.uniform(0.0008, 0.0020, n_points)
flux = model_flux + np.random.normal(0, 1, n_points) * flux_err

# Smooth model curve for overlay
phase_smooth = np.linspace(0.0, 1.0, 2000)
model_smooth = np.ones(2000)
in_transit_s = np.abs(phase_smooth - transit_center) < half_dur
z_s = np.abs(phase_smooth[in_transit_s] - transit_center) / half_dur
limb_s = 1.0 - u1 * (1 - np.sqrt(1 - z_s**2)) - u2 * (1 - np.sqrt(1 - z_s**2)) ** 2
model_smooth[in_transit_s] = 1.0 - transit_depth * limb_s

# Colors
c_data = "#306998"
c_transit = "#1a3a5c"
c_model = "#E74C3C"
c_fill = "#E74C3C"
c_baseline = "#888888"

# Two-panel layout: full light curve + transit zoom
fig, (ax, ax_zoom) = plt.subplots(1, 2, figsize=(16, 9), gridspec_kw={"width_ratios": [3, 1.2], "wspace": 0.05})

# === Main panel: full light curve ===

# Out-of-transit points
out_mask = ~in_transit
ax.errorbar(
    phase[out_mask],
    flux[out_mask],
    yerr=flux_err[out_mask],
    fmt="o",
    markersize=5,
    color=c_data,
    ecolor=c_data,
    elinewidth=0.8,
    alpha=0.6,
    markeredgecolor="white",
    markeredgewidth=0.4,
    capsize=0,
    zorder=2,
    label="Photometry",
)

# In-transit points: darker, more prominent
ax.errorbar(
    phase[in_transit],
    flux[in_transit],
    yerr=flux_err[in_transit],
    fmt="o",
    markersize=7,
    color=c_transit,
    ecolor=c_transit,
    elinewidth=1.0,
    alpha=0.85,
    markeredgecolor="white",
    markeredgewidth=0.5,
    capsize=0,
    zorder=4,
)

# Transit model
ax.plot(phase_smooth, model_smooth, color=c_model, linewidth=3, zorder=5, label="Transit model")

# Fill between baseline and model
transit_mask_smooth = np.abs(phase_smooth - transit_center) < half_dur
ax.fill_between(
    phase_smooth[transit_mask_smooth], 1.0, model_smooth[transit_mask_smooth], color=c_fill, alpha=0.08, zorder=1
)

# Baseline reference
ax.axhline(y=1.0, color=c_baseline, linewidth=1, linestyle="--", alpha=0.4, zorder=1)

# Ingress/egress contact markers
t1 = transit_center - half_dur
t4 = transit_center + half_dur
for t_val, label in [(t1, "$t_1$"), (t4, "$t_4$")]:
    ax.axvline(x=t_val, color="#999999", linewidth=0.8, linestyle=":", alpha=0.5, zorder=1)
    ax.text(t_val, 1.006, label, fontsize=13, color="#666666", ha="center", va="bottom")

# Shaded region showing zoom area
ax.axvspan(transit_center - half_dur * 1.8, transit_center + half_dur * 1.8, color=c_data, alpha=0.04, zorder=0)

# Main panel styling
ax.set_xlabel("Orbital Phase", fontsize=20)
ax.set_ylabel("Relative Flux", fontsize=20)
ax.tick_params(axis="both", labelsize=16)
ax.spines["top"].set_visible(False)
ax.spines["right"].set_visible(False)
ax.yaxis.grid(True, alpha=0.15, linewidth=0.6)
ax.legend(fontsize=16, frameon=False, loc="upper right")
ax.set_xlim(0.0, 1.0)

# === Zoom panel: transit detail ===

# In-transit data
ax_zoom.errorbar(
    phase[in_transit],
    flux[in_transit],
    yerr=flux_err[in_transit],
    fmt="o",
    markersize=7,
    color=c_transit,
    ecolor=c_transit,
    elinewidth=1.0,
    alpha=0.85,
    markeredgecolor="white",
    markeredgewidth=0.5,
    capsize=0,
    zorder=4,
)

# Nearby out-of-transit for context
near_mask = (np.abs(phase - transit_center) < half_dur * 2.0) & ~in_transit
ax_zoom.errorbar(
    phase[near_mask],
    flux[near_mask],
    yerr=flux_err[near_mask],
    fmt="o",
    markersize=5,
    color=c_data,
    ecolor=c_data,
    elinewidth=0.8,
    alpha=0.6,
    markeredgecolor="white",
    markeredgewidth=0.4,
    capsize=0,
    zorder=2,
)

# Zoomed model
zoom_phase = phase_smooth[transit_mask_smooth]
zoom_model = model_smooth[transit_mask_smooth]
ax_zoom.plot(zoom_phase, zoom_model, color=c_model, linewidth=3, zorder=5)
ax_zoom.fill_between(zoom_phase, 1.0, zoom_model, color=c_fill, alpha=0.10, zorder=1)
ax_zoom.axhline(y=1.0, color=c_baseline, linewidth=1, linestyle="--", alpha=0.4)

# Transit depth annotation with double-headed arrow
min_model = zoom_model.min()
arrow = FancyArrowPatch(
    (transit_center - half_dur * 1.6, 1.0),
    (transit_center - half_dur * 1.6, min_model),
    arrowstyle="<->",
    color=c_model,
    linewidth=1.8,
    mutation_scale=14,
    zorder=6,
)
ax_zoom.add_patch(arrow)
ax_zoom.text(
    transit_center - half_dur * 1.5,
    (1.0 + min_model) / 2,
    f"$\\Delta F = {transit_depth * 100:.1f}\\%$",
    fontsize=14,
    color=c_model,
    va="center",
    ha="left",
    fontweight="medium",
    zorder=6,
)

# Contact point labels
for t_val, label in [(t1, "$t_1$"), (t4, "$t_4$")]:
    ax_zoom.axvline(x=t_val, color="#999999", linewidth=0.8, linestyle=":", alpha=0.5, zorder=1)
    ax_zoom.text(t_val, 1.004, label, fontsize=13, color="#666666", ha="center", va="bottom")

# Zoom panel styling
zoom_margin = half_dur * 2.0
ax_zoom.set_xlim(transit_center - zoom_margin, transit_center + zoom_margin)
ax_zoom.set_ylim(min_model - 0.002, 1.006)
ax_zoom.set_xlabel("Orbital Phase", fontsize=20)
ax_zoom.tick_params(axis="both", labelsize=16)
ax_zoom.tick_params(axis="y", labelleft=False)
ax_zoom.spines["top"].set_visible(False)
ax_zoom.spines["right"].set_visible(False)
ax_zoom.yaxis.grid(True, alpha=0.15, linewidth=0.6)
ax_zoom.set_title("Transit Detail", fontsize=18, fontweight="medium", pad=10)

# Figure title
fig.suptitle("lightcurve-transit · matplotlib · pyplots.ai", fontsize=24, fontweight="medium", y=0.98)

fig.subplots_adjust(left=0.08, right=0.97, top=0.91, bottom=0.10, wspace=0.08)
plt.savefig("plot.png", dpi=300, bbox_inches="tight")
