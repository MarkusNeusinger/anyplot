""" anyplot.ai
lightcurve-transit: Astronomical Light Curve
Library: matplotlib 3.11.0 | Python 3.13.14
Quality: 91/100 | Updated: 2026-06-20
"""

import os
import sys


# Prevent this file (matplotlib.py) from shadowing the matplotlib package
_d = os.path.dirname(os.path.abspath(__file__))
while _d in sys.path:
    sys.path.remove(_d)

import matplotlib.pyplot as plt
import numpy as np
from matplotlib import patheffects
from matplotlib.patches import FancyArrowPatch
from matplotlib.ticker import FormatStrFormatter


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
INK_MUTED = "#6B6A63" if THEME == "light" else "#A8A79F"

# Imprint palette — position 1 for photometry, position 3 for transit model
BRAND = "#009E73"  # Imprint position 1 — photometry data
MODEL_COLOR = "#4467A3"  # Imprint position 3 — transit model curve

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

# Two-panel layout: full light curve + transit zoom (landscape 3200×1800)
fig, (ax, ax_zoom) = plt.subplots(
    1, 2, figsize=(8, 4.5), dpi=400, facecolor=PAGE_BG, gridspec_kw={"width_ratios": [3, 1.2], "wspace": 0.15}
)
ax.set_facecolor(PAGE_BG)
ax_zoom.set_facecolor(PAGE_BG)

# === Main panel: full light curve ===

out_mask = ~in_transit
ax.errorbar(
    phase[out_mask],
    flux[out_mask],
    yerr=flux_err[out_mask],
    fmt="o",
    markersize=2.5,
    color=BRAND,
    ecolor=BRAND,
    elinewidth=0.7,
    alpha=0.55,
    markeredgecolor=PAGE_BG,
    markeredgewidth=0.3,
    capsize=0,
    zorder=2,
    label="Photometry",
)
ax.errorbar(
    phase[in_transit],
    flux[in_transit],
    yerr=flux_err[in_transit],
    fmt="o",
    markersize=3.5,
    color=BRAND,
    ecolor=BRAND,
    elinewidth=0.7,
    alpha=0.9,
    markeredgecolor=PAGE_BG,
    markeredgewidth=0.3,
    capsize=0,
    zorder=4,
)

transit_mask_smooth = np.abs(phase_smooth - transit_center) < half_dur
ax.plot(phase_smooth, model_smooth, color=MODEL_COLOR, linewidth=1.8, zorder=5, label="Transit model")
ax.fill_between(
    phase_smooth[transit_mask_smooth], 1.0, model_smooth[transit_mask_smooth], color=MODEL_COLOR, alpha=0.08, zorder=1
)
ax.axhline(y=1.0, color=INK_MUTED, linewidth=0.8, linestyle="--", alpha=0.5, zorder=1)

# Ingress/egress contact markers
t1 = transit_center - half_dur
t4 = transit_center + half_dur
for t_val, label in [(t1, "$t_1$"), (t4, "$t_4$")]:
    ax.axvline(x=t_val, color=INK_MUTED, linewidth=0.6, linestyle=":", alpha=0.6, zorder=1)
    ax.text(t_val, 1.0055, label, fontsize=9, color=INK_MUTED, ha="center", va="bottom")

ax.axvspan(transit_center - half_dur * 1.8, transit_center + half_dur * 1.8, color=BRAND, alpha=0.04, zorder=0)

ax.set_xlabel("Orbital Phase", fontsize=10, color=INK)
ax.set_ylabel("Relative Flux", fontsize=10, color=INK)
ax.tick_params(axis="both", labelsize=8, colors=INK_SOFT, length=0)
ax.spines["top"].set_visible(False)
ax.spines["right"].set_visible(False)
for s in ("left", "bottom"):
    ax.spines[s].set_color(INK_SOFT)
ax.yaxis.grid(True, alpha=0.15, linewidth=0.6, color=INK)
ax.set_xlim(0.0, 1.0)

ax.xaxis.set_major_formatter(FormatStrFormatter("%.2f"))

leg = ax.legend(fontsize=8, frameon=True, loc="upper right")
if leg:
    leg.get_frame().set_facecolor(ELEVATED_BG)
    leg.get_frame().set_edgecolor(INK_SOFT)
    plt.setp(leg.get_texts(), color=INK_SOFT)

# === Zoom panel: transit detail ===

ax_zoom.errorbar(
    phase[in_transit],
    flux[in_transit],
    yerr=flux_err[in_transit],
    fmt="o",
    markersize=3.5,
    color=BRAND,
    ecolor=BRAND,
    elinewidth=0.7,
    alpha=0.9,
    markeredgecolor=PAGE_BG,
    markeredgewidth=0.3,
    capsize=0,
    zorder=4,
)
near_mask = (np.abs(phase - transit_center) < half_dur * 2.0) & ~in_transit
ax_zoom.errorbar(
    phase[near_mask],
    flux[near_mask],
    yerr=flux_err[near_mask],
    fmt="o",
    markersize=2.5,
    color=BRAND,
    ecolor=BRAND,
    elinewidth=0.7,
    alpha=0.55,
    markeredgecolor=PAGE_BG,
    markeredgewidth=0.3,
    capsize=0,
    zorder=2,
)

zoom_phase = phase_smooth[transit_mask_smooth]
zoom_model = model_smooth[transit_mask_smooth]
ax_zoom.plot(zoom_phase, zoom_model, color=MODEL_COLOR, linewidth=1.8, zorder=5)
ax_zoom.fill_between(zoom_phase, 1.0, zoom_model, color=MODEL_COLOR, alpha=0.10, zorder=1)
ax_zoom.axhline(y=1.0, color=INK_MUTED, linewidth=0.8, linestyle="--", alpha=0.5)

# Transit depth annotation with double-headed arrow
min_model = zoom_model.min()
arrow = FancyArrowPatch(
    (transit_center - half_dur * 1.6, 1.0),
    (transit_center - half_dur * 1.6, min_model),
    arrowstyle="<->",
    color=MODEL_COLOR,
    linewidth=1.2,
    mutation_scale=8,
    zorder=6,
)
ax_zoom.add_patch(arrow)
df_text = ax_zoom.text(
    transit_center - half_dur * 1.5,
    (1.0 + min_model) / 2,
    f"$\\Delta F = {transit_depth * 100:.1f}\\%$",
    fontsize=10,
    color=MODEL_COLOR,
    va="center",
    ha="left",
    fontweight="bold",
    zorder=6,
)
df_text.set_path_effects([patheffects.withStroke(linewidth=3, foreground=PAGE_BG), patheffects.Normal()])

for t_val, label in [(t1, "$t_1$"), (t4, "$t_4$")]:
    ax_zoom.axvline(x=t_val, color=INK_MUTED, linewidth=0.6, linestyle=":", alpha=0.6, zorder=1)
    ax_zoom.text(t_val, 1.004, label, fontsize=9, color=INK_MUTED, ha="center", va="bottom")

zoom_margin = half_dur * 2.0
ax_zoom.set_xlim(transit_center - zoom_margin, transit_center + zoom_margin)
ax_zoom.set_ylim(min_model - 0.002, 1.006)
ax_zoom.set_xlabel("Orbital Phase", fontsize=10, color=INK)
ax_zoom.tick_params(axis="both", labelsize=8, colors=INK_SOFT, length=0)
ax_zoom.tick_params(axis="y", labelleft=False)
ax_zoom.xaxis.set_major_formatter(FormatStrFormatter("%.2f"))
ax_zoom.spines["top"].set_visible(False)
ax_zoom.spines["right"].set_visible(False)
for s in ("left", "bottom"):
    ax_zoom.spines[s].set_color(INK_SOFT)
ax_zoom.yaxis.grid(True, alpha=0.15, linewidth=0.6, color=INK)
ax_zoom.set_title("Transit Detail", fontsize=10, fontweight="medium", pad=8, color=INK)

# Figure title — "lightcurve-transit · python · matplotlib · anyplot.ai" is ~53 chars, fits at 12pt
fig.suptitle(
    "lightcurve-transit · python · matplotlib · anyplot.ai", fontsize=12, fontweight="medium", y=0.98, color=INK
)

fig.subplots_adjust(left=0.09, right=0.97, top=0.91, bottom=0.12, wspace=0.15)
plt.savefig(f"plot-{THEME}.png", dpi=400, facecolor=PAGE_BG)
