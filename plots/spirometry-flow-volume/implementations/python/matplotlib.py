"""anyplot.ai
spirometry-flow-volume: Spirometry Flow-Volume Loop
Library: matplotlib | Python

Theme-adaptive (ANYPLOT_THEME=light|dark). Imprint palette:
measured loop = brand green (position 1), predicted normal = muted neutral
(dashed reference), obstruction gap = matte-red semantic anchor.
"""

import os

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.patches import FancyArrowPatch


# Theme-adaptive chrome
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
INK_MUTED = "#6B6A63" if THEME == "light" else "#A8A79F"

# Imprint palette
BRAND = "#009E73"  # measured loop — always first series
MATTE_RED = "#AE3030"  # semantic anchor: obstruction / loss

# Data — simulate a realistic flow-volume loop (mild obstruction pattern)
np.random.seed(42)

# Measured values (typical adult, mild obstruction)
fvc = 4.2  # Forced Vital Capacity (L)
pef = 8.5  # Peak Expiratory Flow (L/s)
fev1 = 3.1  # FEV1 (L)

# Predicted normal values
fvc_pred = 4.8
pef_pred = 10.2
fev1_pred = 4.0

N = 200


def expiratory_limb(capacity, peak, n=N):
    """Sharp rise to PEF then a roughly linear decline (ascending volume)."""
    vol = np.linspace(0, capacity, n)
    t = vol / capacity
    raw = (1 - np.exp(-30 * t)) * (1 - t) ** 0.5
    return vol, raw / raw.max() * peak


def inspiratory_limb(capacity, peak, n=N):
    """Symmetric U-shaped curve below zero flow (ascending volume)."""
    vol = np.linspace(0, capacity, n)
    t = vol / capacity
    return vol, -peak * np.sin(np.pi * t) ** 0.8


vol_exp_m, flow_exp_m = expiratory_limb(fvc, pef)
vol_insp_m, flow_insp_m = inspiratory_limb(fvc, 5.5)
vol_exp_p, flow_exp_p = expiratory_limb(fvc_pred, pef_pred)
vol_insp_p, flow_insp_p = inspiratory_limb(fvc_pred, 6.5)

# Closed measured loop: expiration (0→FVC) then inspiration back (FVC→0)
vol_loop_m = np.concatenate([vol_exp_m, vol_insp_m[::-1]])
flow_loop_m = np.concatenate([flow_exp_m, flow_insp_m[::-1]])
vol_loop_p = np.concatenate([vol_exp_p, vol_insp_p[::-1]])
flow_loop_p = np.concatenate([flow_exp_p, flow_insp_p[::-1]])

# Peak Expiratory Flow point on the measured curve
pef_idx = int(np.argmax(flow_exp_m))
pef_volume, pef_flow = vol_exp_m[pef_idx], flow_exp_m[pef_idx]

# Common grid for obstruction-gap fills — single interpolation per limb
grid = np.linspace(0, fvc_pred, N)
exp_m_g = np.interp(grid, vol_exp_m, flow_exp_m, right=0.0)
exp_p_g = np.interp(grid, vol_exp_p, flow_exp_p)
insp_m_g = np.interp(grid, vol_insp_m, flow_insp_m, right=0.0)
insp_p_g = np.interp(grid, vol_insp_p, flow_insp_p)

# Plot — landscape 3200×1800
fig, ax = plt.subplots(figsize=(8, 4.5), dpi=400, facecolor=PAGE_BG)
ax.set_facecolor(PAGE_BG)

# Obstruction gap between predicted and measured limbs
ax.fill_between(grid, exp_m_g, exp_p_g, color=MATTE_RED, alpha=0.13, zorder=1, label="Obstruction gap")
ax.fill_between(grid, insp_m_g, insp_p_g, color=MATTE_RED, alpha=0.09, zorder=1)

# Zero-flow reference line
ax.axhline(y=0, color=INK_SOFT, linewidth=0.8, alpha=0.5, zorder=1)

# Predicted normal loop (dashed muted reference)
ax.plot(vol_loop_p, flow_loop_p, color=INK_MUTED, linewidth=1.6, linestyle="--", zorder=2, label="Predicted Normal")

# Measured loop (solid brand green)
ax.plot(vol_loop_m, flow_loop_m, color=BRAND, linewidth=2.5, solid_capstyle="round", zorder=3, label="Measured")

# Directional arrows along the measured loop
for vol, flow, idx in (
    (vol_exp_m, flow_exp_m, N // 5),
    (vol_exp_m, flow_exp_m, int(N * 0.65)),
    (vol_insp_m[::-1], flow_insp_m[::-1], N // 2),
):
    ax.add_patch(
        FancyArrowPatch(
            (vol[idx], flow[idx]),
            (vol[idx + 4], flow[idx + 4]),
            arrowstyle="-|>",
            mutation_scale=11,
            color=BRAND,
            linewidth=2.0,
            zorder=4,
        )
    )

# Mark PEF
ax.scatter(pef_volume, pef_flow, s=90, color=BRAND, edgecolors=PAGE_BG, linewidth=1.2, zorder=5)
ax.annotate(
    f"PEF = {pef_flow:.1f} L/s",
    xy=(pef_volume, pef_flow),
    xytext=(pef_volume + 0.55, pef_flow - 0.7),
    fontsize=8,
    fontweight="bold",
    color=INK,
    arrowprops={"arrowstyle": "->", "color": INK_SOFT, "lw": 1.2, "connectionstyle": "arc3,rad=0.2"},
)

# Breathing-direction labels
ax.text(2.1, pef * 0.82, "EXPIRATION →", fontsize=8, color=INK_MUTED, fontweight="bold", ha="center")
ax.text(2.1, -5.5 * 0.72, "← INSPIRATION", fontsize=8, color=INK_MUTED, fontweight="bold", ha="center")

# Clinical values text box
textstr = (
    f"FVC      = {fvc:.1f} L   (pred {fvc_pred:.1f})\n"
    f"FEV₁     = {fev1:.1f} L   (pred {fev1_pred:.1f})\n"
    f"FEV₁/FVC = {fev1 / fvc:.0%}\n"
    f"PEF      = {pef_flow:.1f} L/s (pred {pef_pred:.1f})"
)
ax.text(
    0.975,
    0.96,
    textstr,
    transform=ax.transAxes,
    fontsize=8,
    color=INK,
    va="top",
    ha="right",
    family="monospace",
    bbox={
        "boxstyle": "round,pad=0.5",
        "facecolor": ELEVATED_BG,
        "edgecolor": INK_SOFT,
        "alpha": 0.95,
        "linewidth": 0.8,
    },
)

# Axes & chrome
ax.set_xlabel("Volume (L)", fontsize=10, color=INK)
ax.set_ylabel("Flow (L/s)", fontsize=10, color=INK)
ax.set_title("spirometry-flow-volume · python · matplotlib · anyplot.ai", fontsize=12, fontweight="medium", color=INK)
ax.tick_params(axis="both", labelsize=8, colors=INK_SOFT, labelcolor=INK_SOFT)
ax.spines["top"].set_visible(False)
ax.spines["right"].set_visible(False)
for s in ("left", "bottom"):
    ax.spines[s].set_color(INK_SOFT)
ax.yaxis.grid(True, alpha=0.15, color=INK, linewidth=0.8)

leg = ax.legend(fontsize=8, loc="lower left", framealpha=0.95)
leg.get_frame().set_facecolor(ELEVATED_BG)
leg.get_frame().set_edgecolor(INK_SOFT)
plt.setp(leg.get_texts(), color=INK_SOFT)

fig.subplots_adjust(left=0.07, right=0.97, top=0.91, bottom=0.11)
plt.savefig(f"plot-{THEME}.png", dpi=400, facecolor=PAGE_BG)
