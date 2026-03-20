"""pyplots.ai
bifurcation-basic: Bifurcation Diagram for Dynamical Systems
Library: seaborn 0.13.2 | Python 3.14.3
Quality: 87/100 | Created: 2026-03-20
"""

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns


# Data - Logistic map: x(n+1) = r * x(n) * (1 - x(n))
r_values = np.linspace(2.5, 4.0, 5000)
transient = 300
n_plot = 200

r_all = np.empty(len(r_values) * n_plot)
x_all = np.empty(len(r_values) * n_plot)

idx = 0
for r in r_values:
    x = 0.5
    for _ in range(transient):
        x = r * x * (1.0 - x)
    for _ in range(n_plot):
        x = r * x * (1.0 - x)
        r_all[idx] = r
        x_all[idx] = x
        idx += 1

# Classify regions for color storytelling
regime = np.where(r_all < 3.0, "Stable", np.where(r_all < 3.57, "Period-Doubling", "Chaos"))

df = pd.DataFrame({"r": r_all, "x": x_all, "Regime": regime})

# Colorblind-safe palette: blue, orange, red - high perceptual distance
palette = {"Stable": "#306998", "Period-Doubling": "#E88C30", "Chaos": "#DC2626"}
regime_order = ["Stable", "Period-Doubling", "Chaos"]

# Use seaborn JointGrid with marginal KDE — a distinctive seaborn feature
sns.set_theme(
    style="ticks",
    context="talk",
    font_scale=1.1,
    rc={"font.family": "sans-serif", "axes.edgecolor": "#888888", "axes.linewidth": 0.8},
)

g = sns.JointGrid(data=df, x="r", y="x", height=9, ratio=8, space=0.08, marginal_ticks=False)
g.figure.set_size_inches(16, 9)

# Main plot: scatter per regime with size adapted to data density
# Stable region has few unique points per r → larger markers for visibility
for regime_name, marker_s, marker_alpha in [("Stable", 1.5, 0.8), ("Period-Doubling", 0.3, 0.55), ("Chaos", 0.3, 0.5)]:
    subset = df[df["Regime"] == regime_name]
    sns.scatterplot(
        data=subset,
        x="r",
        y="x",
        color=palette[regime_name],
        s=marker_s,
        alpha=marker_alpha,
        linewidth=0,
        edgecolor="none",
        label=regime_name,
        ax=g.ax_joint,
        rasterized=True,
    )

# Marginal KDE on y-axis: distinctive seaborn density visualization per regime
for regime_name in regime_order:
    subset = df[df["Regime"] == regime_name]
    sns.kdeplot(
        y=subset["x"], color=palette[regime_name], fill=True, alpha=0.3, linewidth=1.5, ax=g.ax_marg_y, clip=(0, 1)
    )

# Remove x-marginal (uniform r sampling adds no insight)
g.ax_marg_x.set_visible(False)

ax = g.ax_joint

# Annotate key bifurcation points
bifurcation_points = [
    (3.0, "Period-2\nr ≈ 3.0", 0.04),
    (3.449, "Period-4\nr ≈ 3.449", -0.14),
    (3.544, "Period-8\nr ≈ 3.544", 0.04),
]

for r_bif, label, x_offset in bifurcation_points:
    ax.axvline(r_bif, color="#94a3b8", linewidth=0.8, linestyle="--", alpha=0.6)
    ax.annotate(
        label,
        xy=(r_bif, 0.03),
        xytext=(r_bif + x_offset, 0.13),
        fontsize=15,
        color="#475569",
        ha="left" if x_offset > 0 else "right",
        va="bottom",
        arrowprops={"arrowstyle": "-", "color": "#94a3b8", "lw": 0.8},
    )

# Style
ax.set_title("bifurcation-basic · seaborn · pyplots.ai", fontsize=24, fontweight="medium", color="#333333", pad=16)
ax.set_xlabel("Growth Rate (r)", fontsize=20, color="#444444")
ax.set_ylabel("Steady-State Population (x)", fontsize=20, color="#444444")
ax.set_xlim(2.5, 4.0)
ax.set_ylim(0, 1)
ax.tick_params(axis="both", labelsize=16, colors="#555555")
sns.despine(ax=ax)
sns.despine(ax=g.ax_marg_y, bottom=True, left=True)

# Refine legend
legend = ax.get_legend()
legend.set_title("Regime")
legend.get_title().set_fontsize(15)
for text in legend.get_texts():
    text.set_fontsize(14)
legend.set_frame_on(True)
legend.get_frame().set_alpha(0.9)
legend.get_frame().set_edgecolor("#cccccc")

plt.savefig("plot.png", dpi=300, bbox_inches="tight")
