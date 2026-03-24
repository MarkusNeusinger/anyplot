""" pyplots.ai
spirometry-flow-volume: Spirometry Flow-Volume Loop
Library: seaborn 0.13.2 | Python 3.14.3
Quality: 91/100 | Created: 2026-03-18
"""

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns


# Data
np.random.seed(42)

fvc_measured = 4.8
pef_measured = 9.5
fev1_measured = 3.5

n_points = 150

# Expiratory limb (positive flow): sharp rise to PEF then linear decline
vol_exp = np.linspace(0, fvc_measured, n_points)
rise_phase = np.minimum(vol_exp / 0.3, 1.0)
decay_phase = 1.0 - (vol_exp / fvc_measured) ** 0.85
flow_exp_raw = rise_phase * decay_phase
flow_exp = pef_measured * flow_exp_raw / flow_exp_raw.max()
flow_exp = np.maximum(flow_exp, 0)

# Inspiratory limb (negative flow): symmetric U-shaped curve
vol_insp = np.linspace(0, fvc_measured, n_points)
flow_insp = -5.5 * np.sin(np.linspace(np.pi, 0, n_points))

# Predicted normal values
fvc_predicted = 5.2
pef_predicted = 10.8
vol_pred_exp = np.linspace(0, fvc_predicted, n_points)
rise_pred = np.minimum(vol_pred_exp / 0.28, 1.0)
decay_pred = 1.0 - (vol_pred_exp / fvc_predicted) ** 0.85
flow_pred_exp_raw = rise_pred * decay_pred
flow_pred_exp = pef_predicted * flow_pred_exp_raw / flow_pred_exp_raw.max()
flow_pred_exp = np.maximum(flow_pred_exp, 0)

vol_pred_insp = np.linspace(0, fvc_predicted, n_points)
flow_pred_insp = -6.2 * np.sin(np.linspace(np.pi, 0, n_points))

# Build DataFrame using style column for idiomatic seaborn hue+style plotting
df = pd.DataFrame(
    {
        "Volume (L)": np.concatenate([vol_exp, vol_insp, vol_pred_exp, vol_pred_insp]),
        "Flow (L/s)": np.concatenate([flow_exp, flow_insp, flow_pred_exp, flow_pred_insp]),
        "Curve": (
            ["Measured"] * n_points
            + ["Measured"] * n_points
            + ["Predicted Normal"] * n_points
            + ["Predicted Normal"] * n_points
        ),
        "Limb": (
            ["Expiratory"] * n_points
            + ["Inspiratory"] * n_points
            + ["Expiratory"] * n_points
            + ["Inspiratory"] * n_points
        ),
    }
)

# Plot setup using seaborn theming
custom_palette = sns.color_palette(["#306998", "#A0A0A0"])
sns.set_context("talk", rc={"lines.linewidth": 3, "font.size": 16})
sns.set_style("whitegrid", {"grid.alpha": 0.15, "grid.linewidth": 0.6})

fig, ax = plt.subplots(figsize=(16, 9))

# Plot using sns.lineplot with hue AND style for idiomatic seaborn usage
# style parameter controls dash patterns natively without post-hoc iteration
for limb_name in ["Expiratory", "Inspiratory"]:
    limb_df = df[df["Limb"] == limb_name]
    sns.lineplot(
        data=limb_df,
        x="Volume (L)",
        y="Flow (L/s)",
        hue="Curve",
        style="Curve",
        palette={"Measured": "#306998", "Predicted Normal": "#A0A0A0"},
        dashes={"Measured": "", "Predicted Normal": (5, 3)},
        linewidth=3,
        ax=ax,
        legend=(limb_name == "Expiratory"),
    )

# Shade flow deficit between measured and predicted expiratory limbs
vol_shade = np.linspace(0, min(fvc_measured, fvc_predicted), 200)
flow_meas_interp = np.interp(vol_shade, vol_exp, flow_exp)
flow_pred_interp = np.interp(vol_shade, vol_pred_exp, flow_pred_exp)
ax.fill_between(
    vol_shade, flow_meas_interp, flow_pred_interp, alpha=0.10, color="#E74C3C", label="Flow deficit", zorder=1
)

# Mark PEF with sns.scatterplot
pef_idx = np.argmax(flow_exp)
pef_actual = flow_exp[pef_idx]
pef_df = pd.DataFrame({"Volume (L)": [vol_exp[pef_idx]], "Flow (L/s)": [pef_actual]})
sns.scatterplot(
    data=pef_df,
    x="Volume (L)",
    y="Flow (L/s)",
    color="#E74C3C",
    s=300,
    zorder=5,
    edgecolor="white",
    linewidth=2,
    legend=False,
    ax=ax,
)
ax.annotate(
    f"PEF = {pef_actual:.1f} L/s",
    xy=(vol_exp[pef_idx], pef_actual),
    xytext=(vol_exp[pef_idx] + 0.7, pef_actual + 0.4),
    fontsize=16,
    fontweight="bold",
    color="#E74C3C",
    arrowprops={"arrowstyle": "->", "color": "#E74C3C", "lw": 2},
    zorder=5,
)

# Mark FEV1 point on measured curve
fev1_flow = np.interp(fev1_measured, vol_exp, flow_exp)
fev1_df = pd.DataFrame({"Volume (L)": [fev1_measured], "Flow (L/s)": [fev1_flow]})
sns.scatterplot(
    data=fev1_df,
    x="Volume (L)",
    y="Flow (L/s)",
    color="#306998",
    marker="D",
    s=200,
    zorder=5,
    edgecolor="white",
    linewidth=1.5,
    legend=False,
    ax=ax,
)
ax.annotate(
    f"FEV₁ = {fev1_measured:.1f} L",
    xy=(fev1_measured, fev1_flow),
    xytext=(fev1_measured + 0.5, fev1_flow + 0.8),
    fontsize=14,
    fontweight="semibold",
    color="#306998",
    arrowprops={"arrowstyle": "->", "color": "#306998", "lw": 1.5},
    zorder=5,
)

# Clinical values text box
fev1_fvc_ratio = fev1_measured / fvc_measured * 100
textstr = (
    f"FVC = {fvc_measured:.1f} L\n"
    f"FEV₁ = {fev1_measured:.1f} L\n"
    f"FEV₁/FVC = {fev1_fvc_ratio:.0f}%\n"
    f"PEF = {pef_actual:.1f} L/s"
)
props = {"boxstyle": "round,pad=0.6", "facecolor": "#F0F4F8", "edgecolor": "#306998", "alpha": 0.92, "linewidth": 1.5}
ax.text(
    0.97,
    0.03,
    textstr,
    transform=ax.transAxes,
    fontsize=16,
    verticalalignment="bottom",
    horizontalalignment="right",
    bbox=props,
    family="monospace",
    zorder=6,
)

# Zero flow reference line
ax.axhline(y=0, color="#888888", linewidth=0.8, linestyle="-", zorder=1)

# Labels and title
ax.set_xlabel("Volume (L)", fontsize=20)
ax.set_ylabel("Flow (L/s)", fontsize=20)
ax.set_title("spirometry-flow-volume · seaborn · pyplots.ai", fontsize=24, fontweight="medium", pad=18)
ax.tick_params(axis="both", labelsize=16)
sns.despine(ax=ax)

# Clean up legend using sns.move_legend for idiomatic seaborn approach
sns.move_legend(ax, "upper right", fontsize=15, framealpha=0.9)
# Add flow deficit to legend handles
handles, labels = ax.get_legend_handles_labels()
ax.legend(handles=handles, labels=labels, fontsize=15, loc="upper right", framealpha=0.9)

plt.tight_layout()
plt.savefig("plot.png", dpi=300, bbox_inches="tight")
