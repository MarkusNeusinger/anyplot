""" pyplots.ai
lightcurve-transit: Astronomical Light Curve
Library: seaborn 0.13.2 | Python 3.14.3
Quality: 91/100 | Created: 2026-03-18
"""

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns


# Data
np.random.seed(42)

n_points = 500
phase = np.sort(np.random.uniform(0.0, 1.0, n_points))

# Transit parameters
transit_center = 0.5
transit_width = 0.025
transit_depth = 0.01
u1, u2 = 0.4, 0.2

# Transit model for data points
z = np.abs(phase - transit_center) / transit_width
dip = np.where(z < 1.0, np.sqrt(np.clip(1.0 - z**2, 0, None)), 0.0)
limb = 1.0 - u1 * (1 - dip) - u2 * (1 - dip) ** 2
model_flux = 1.0 - transit_depth * dip * limb

# Observed flux with noise
flux_err = np.random.uniform(0.0008, 0.0015, n_points)
flux = model_flux + np.random.normal(0, 1, n_points) * flux_err
residuals = flux - model_flux

# Smooth model curve
phase_model = np.linspace(0.0, 1.0, 2000)
z_model = np.abs(phase_model - transit_center) / transit_width
dip_model = np.where(z_model < 1.0, np.sqrt(np.clip(1.0 - z_model**2, 0, None)), 0.0)
limb_model = 1.0 - u1 * (1 - dip_model) - u2 * (1 - dip_model) ** 2
model_smooth = 1.0 - transit_depth * dip_model * limb_model

df = pd.DataFrame({"phase": phase, "flux": flux, "flux_err": flux_err, "residuals": residuals})
df_model = pd.DataFrame({"phase": phase_model, "flux": model_smooth})

# Custom palette: Python Blue primary + complementary amber for model
data_color = "#306998"
model_color = "#C8702A"
custom_palette = sns.color_palette([data_color, model_color])
sns.set_palette(custom_palette)

# Seaborn styling
sns.set_style("ticks", {"axes.grid": False})
sns.set_context("talk", font_scale=1.05)

# Plot — two-panel layout: light curve + residuals
fig, (ax_main, ax_resid) = plt.subplots(
    2, 1, figsize=(16, 9), height_ratios=[3, 1], sharex=True, gridspec_kw={"hspace": 0.05}
)

# Error bars on main panel
ax_main.errorbar(
    df["phase"],
    df["flux"],
    yerr=df["flux_err"],
    fmt="none",
    ecolor=data_color,
    elinewidth=0.9,
    alpha=0.35,
    capsize=0,
    zorder=1,
)

# Scatter using seaborn
sns.scatterplot(
    data=df,
    x="phase",
    y="flux",
    color=data_color,
    s=35,
    alpha=0.45,
    edgecolor="white",
    linewidth=0.3,
    ax=ax_main,
    zorder=2,
    legend=False,
)

# Model curve using seaborn lineplot
sns.lineplot(
    data=df_model, x="phase", y="flux", color=model_color, linewidth=2.5, ax=ax_main, zorder=3, label="Transit model"
)

# Residuals panel using seaborn scatterplot
sns.scatterplot(
    data=df,
    x="phase",
    y="residuals",
    color=data_color,
    s=20,
    alpha=0.4,
    edgecolor="white",
    linewidth=0.2,
    ax=ax_resid,
    legend=False,
)
ax_resid.axhline(0, color=model_color, linewidth=1.5, linestyle="--", alpha=0.6, zorder=3)

# Seaborn rugplot on residuals to show density distribution
sns.rugplot(data=df, y="residuals", color=data_color, alpha=0.1, height=0.015, ax=ax_resid)

# Transit depth annotation
transit_min = model_smooth.min()
ax_main.annotate(
    f"Transit depth\n{transit_depth * 100:.1f}%",
    xy=(transit_center, transit_min),
    xytext=(transit_center + 0.12, transit_min - 0.001),
    fontsize=14,
    color=model_color,
    fontweight="medium",
    arrowprops={"arrowstyle": "->", "color": model_color, "lw": 1.5},
    ha="left",
    va="top",
    zorder=5,
)

# Styling — main panel
ax_main.set_ylabel("Relative Flux", fontsize=20)
ax_main.set_title("lightcurve-transit · seaborn · pyplots.ai", fontsize=24, fontweight="medium", pad=15)
ax_main.tick_params(axis="both", labelsize=16)
ax_main.tick_params(axis="x", labelbottom=False)
ax_main.yaxis.grid(True, alpha=0.15, linewidth=0.6)
ax_main.legend(fontsize=15, frameon=False, loc="lower right")

# Styling — residuals panel
ax_resid.set_xlabel("Orbital Phase", fontsize=20)
ax_resid.set_ylabel("Residuals", fontsize=16)
ax_resid.tick_params(axis="both", labelsize=16)
ax_resid.yaxis.grid(True, alpha=0.15, linewidth=0.6)
ax_resid.set_xlim(0.0, 1.0)

# Despine using seaborn
sns.despine(ax=ax_main)
sns.despine(ax=ax_resid)

plt.savefig("plot.png", dpi=300, bbox_inches="tight")
