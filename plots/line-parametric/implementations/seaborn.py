""" pyplots.ai
line-parametric: Parametric Curve Plot
Library: seaborn 0.13.2 | Python 3.14.3
Quality: 77/100 | Created: 2026-03-20
"""

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
from matplotlib.gridspec import GridSpec


sns.set_theme(style="whitegrid")
sns.set_context("talk", font_scale=1.1)

# Data - Lissajous figure
t_liss = np.linspace(0, 2 * np.pi, 1000)
df_liss = pd.DataFrame({"x": np.sin(3 * t_liss), "y": np.sin(2 * t_liss), "t": t_liss})

# Data - Archimedean spiral
t_spiral = np.linspace(0, 4 * np.pi, 1000)
df_spiral = pd.DataFrame({"x": t_spiral * np.cos(t_spiral), "y": t_spiral * np.sin(t_spiral), "t": t_spiral})

# Plot - square figure for equal-aspect subplots
fig = plt.figure(figsize=(18, 9))
gs = GridSpec(1, 2, figure=fig, wspace=0.4)
ax1 = fig.add_subplot(gs[0, 0])
ax2 = fig.add_subplot(gs[0, 1])

# Lissajous figure using sns.scatterplot with color gradient
sns.scatterplot(data=df_liss, x="x", y="y", hue="t", palette="viridis", s=20, edgecolor="none", legend=False, ax=ax1)
sns.scatterplot(
    x=[df_liss["x"].iloc[0]],
    y=[df_liss["y"].iloc[0]],
    s=280,
    color="#306998",
    marker="o",
    zorder=5,
    label="Start (t = 0)",
    edgecolor="white",
    linewidth=1.5,
    ax=ax1,
)
sns.scatterplot(
    x=[df_liss["x"].iloc[-1]],
    y=[df_liss["y"].iloc[-1]],
    s=280,
    color="#e74c3c",
    marker="s",
    zorder=5,
    label="End (t = 2\u03c0)",
    edgecolor="white",
    linewidth=1.5,
    ax=ax1,
)

# Archimedean spiral using sns.scatterplot with color gradient
sns.scatterplot(data=df_spiral, x="x", y="y", hue="t", palette="plasma", s=20, edgecolor="none", legend=False, ax=ax2)
sns.scatterplot(
    x=[df_spiral["x"].iloc[0]],
    y=[df_spiral["y"].iloc[0]],
    s=280,
    color="#306998",
    marker="o",
    zorder=5,
    label="Start (t = 0)",
    edgecolor="white",
    linewidth=1.5,
    ax=ax2,
)
sns.scatterplot(
    x=[df_spiral["x"].iloc[-1]],
    y=[df_spiral["y"].iloc[-1]],
    s=280,
    color="#e74c3c",
    marker="s",
    zorder=5,
    label="End (t = 4\u03c0)",
    edgecolor="white",
    linewidth=1.5,
    ax=ax2,
)

# Colorbars
norm_l = plt.Normalize(0, 2 * np.pi)
norm_s = plt.Normalize(0, 4 * np.pi)
sm_l = plt.cm.ScalarMappable(cmap="viridis", norm=norm_l)
sm_s = plt.cm.ScalarMappable(cmap="plasma", norm=norm_s)
cb1 = fig.colorbar(sm_l, ax=ax1, shrink=0.7, pad=0.03)
cb1.set_label("Parameter t", fontsize=18)
cb1.ax.tick_params(labelsize=14)
cb2 = fig.colorbar(sm_s, ax=ax2, shrink=0.7, pad=0.03)
cb2.set_label("Parameter t", fontsize=18)
cb2.ax.tick_params(labelsize=14)

# Style - Lissajous
ax1.set_aspect("equal")
ax1.set_title("Lissajous: x = sin(3t), y = sin(2t)", fontsize=24, fontweight="medium")
ax1.set_xlabel("x(t)", fontsize=20)
ax1.set_ylabel("y(t)", fontsize=20)
ax1.tick_params(axis="both", labelsize=16)
ax1.legend(fontsize=14, loc="upper right", framealpha=0.9)
ax1.grid(True, alpha=0.15, linewidth=0.5)
sns.despine(ax=ax1)

# Style - Spiral
ax2.set_aspect("equal")
ax2.set_title("Spiral: x = t\u00b7cos(t), y = t\u00b7sin(t)", fontsize=24, fontweight="medium")
ax2.set_xlabel("x(t)", fontsize=20)
ax2.set_ylabel("y(t)", fontsize=20)
ax2.tick_params(axis="both", labelsize=16)
ax2.legend(fontsize=14, loc="upper right", framealpha=0.9)
ax2.grid(True, alpha=0.15, linewidth=0.5)
sns.despine(ax=ax2)

fig.suptitle("line-parametric \u00b7 seaborn \u00b7 pyplots.ai", fontsize=26, fontweight="medium", y=0.98)

# Save
plt.savefig("plot.png", dpi=300, bbox_inches="tight")
