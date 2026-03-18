""" pyplots.ai
spirometry-flow-volume: Spirometry Flow-Volume Loop
Library: seaborn 0.13.2 | Python 3.14.3
Quality: 86/100 | Created: 2026-03-18
"""

import matplotlib.pyplot as plt
import numpy as np
import seaborn as sns


# Data
np.random.seed(42)

# Forced Vital Capacity and Peak Expiratory Flow for measured values
fvc_measured = 4.8
pef_measured = 9.5
fev1_measured = 3.5  # Volume exhaled in first second (L)

# Generate expiratory limb (positive flow)
# Sharp rise to PEF then roughly linear decline
n_points = 150
vol_exp = np.linspace(0, fvc_measured, n_points)
# Model: rapid rise then linear decay
rise_phase = np.minimum(vol_exp / 0.3, 1.0)
decay_phase = 1.0 - (vol_exp / fvc_measured) ** 0.85
flow_exp = pef_measured * rise_phase * decay_phase
flow_exp = np.maximum(flow_exp, 0)

# FEV1 flow value at the FEV1 volume point on the curve
fev1_flow = np.interp(fev1_measured, vol_exp, flow_exp)

# Generate inspiratory limb (negative flow)
vol_insp = np.linspace(fvc_measured, 0, n_points)
# Symmetric U-shaped curve
t_insp = np.linspace(0, np.pi, n_points)
flow_insp = -5.5 * np.sin(t_insp)

# Predicted normal values (slightly larger capacity, higher flows)
fvc_predicted = 5.2
pef_predicted = 10.8
vol_pred_exp = np.linspace(0, fvc_predicted, n_points)
rise_pred = np.minimum(vol_pred_exp / 0.28, 1.0)
decay_pred = 1.0 - (vol_pred_exp / fvc_predicted) ** 0.85
flow_pred_exp = pef_predicted * rise_pred * decay_pred
flow_pred_exp = np.maximum(flow_pred_exp, 0)

vol_pred_insp = np.linspace(fvc_predicted, 0, n_points)
t_pred_insp = np.linspace(0, np.pi, n_points)
flow_pred_insp = -6.2 * np.sin(t_pred_insp)

# Combine into closed loops
volume_measured = np.concatenate([vol_exp, vol_insp])
flow_measured = np.concatenate([flow_exp, flow_insp])
volume_predicted = np.concatenate([vol_pred_exp, vol_pred_insp])
flow_predicted = np.concatenate([flow_pred_exp, flow_pred_insp])

# Plot
sns.set_context("talk", font_scale=1.2)
sns.set_style("whitegrid", {"grid.alpha": 0.2, "grid.linewidth": 0.8})
fig, ax = plt.subplots(figsize=(16, 9))

# Predicted loop (dashed, behind)
ax.plot(
    volume_predicted, flow_predicted, color="#A0A0A0", linestyle="--", linewidth=2.5, label="Predicted Normal", zorder=2
)

# Measured loop (solid, foreground)
ax.plot(volume_measured, flow_measured, color="#306998", linewidth=3.5, label="Measured", zorder=3)

# Mark PEF
pef_idx = np.argmax(flow_exp)
ax.scatter(vol_exp[pef_idx], flow_exp[pef_idx], color="#E74C3C", s=250, zorder=5, edgecolors="white", linewidth=1.5)
ax.annotate(
    f"PEF = {pef_measured:.1f} L/s",
    xy=(vol_exp[pef_idx], flow_exp[pef_idx]),
    xytext=(vol_exp[pef_idx] + 0.6, flow_exp[pef_idx] + 0.3),
    fontsize=16,
    fontweight="bold",
    color="#E74C3C",
    arrowprops={"arrowstyle": "->", "color": "#E74C3C", "lw": 2},
    zorder=5,
)

# Clinical values text box
fev1_fvc_ratio = fev1_measured / fvc_measured * 100
textstr = (
    f"FVC = {fvc_measured:.1f} L\n"
    f"FEV₁ = {fev1_measured:.1f} L\n"
    f"FEV₁/FVC = {fev1_fvc_ratio:.0f}%\n"
    f"PEF = {pef_measured:.1f} L/s"
)
props = {"boxstyle": "round,pad=0.5", "facecolor": "#F0F4F8", "edgecolor": "#306998", "alpha": 0.9}
ax.text(
    0.97,
    0.03,
    textstr,
    transform=ax.transAxes,
    fontsize=16,
    verticalalignment="bottom",
    horizontalalignment="right",
    bbox=props,
    zorder=6,
)

# Zero flow reference line
ax.axhline(y=0, color="#888888", linewidth=1.0, linestyle="-", zorder=1)

# Style
ax.set_xlabel("Volume (L)", fontsize=20)
ax.set_ylabel("Flow (L/s)", fontsize=20)
ax.set_title("spirometry-flow-volume · seaborn · pyplots.ai", fontsize=24, fontweight="medium", pad=15)
ax.tick_params(axis="both", labelsize=16)
ax.spines["top"].set_visible(False)
ax.spines["right"].set_visible(False)
ax.legend(fontsize=16, loc="upper right", framealpha=0.9)

plt.tight_layout()
plt.savefig("plot.png", dpi=300, bbox_inches="tight")
