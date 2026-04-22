""" pyplots.ai
line-pca-variance-cumulative: Cumulative Explained Variance for PCA Component Selection
Library: matplotlib 3.10.8 | Python 3.14.3
Quality: 96/100 | Created: 2026-02-17
"""

import matplotlib.patheffects as pe
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import numpy as np
from sklearn.datasets import load_wine
from sklearn.decomposition import PCA
from sklearn.preprocessing import StandardScaler


# Data
wine = load_wine()
X = StandardScaler().fit_transform(wine.data)
pca = PCA().fit(X)

variance = pca.explained_variance_ratio_
cumulative = np.cumsum(variance)
components = np.arange(1, len(cumulative) + 1)

# Detect elbow point using maximum second derivative (discrete differences)
diffs = np.diff(cumulative)
diffs2 = np.diff(diffs)
elbow_idx = np.argmin(diffs2) + 1  # +1 because second diff shifts by 1
elbow_component = elbow_idx + 1  # 1-indexed component number

# Thresholds with improved color contrast (dark amber vs deep red-violet)
thresholds = [(0.90, "90%", "#B8860B"), (0.95, "95%", "#A0325C")]
n_at_threshold = [np.argmax(cumulative >= t) + 1 for t, _, _ in thresholds]

# Plot
fig, ax = plt.subplots(figsize=(16, 9))
fig.patch.set_facecolor("#FAFAFA")
ax.set_facecolor("#FAFAFA")

# Individual variance bars with gradient effect via edge coloring
ax.bar(
    components,
    variance,
    color="#306998",
    alpha=0.25,
    width=0.65,
    edgecolor="#306998",
    linewidth=0.8,
    label="Individual variance",
    zorder=2,
)

# Fill area under cumulative curve for visual weight
ax.fill_between(components, cumulative, alpha=0.06, color="#306998", zorder=3)

# Cumulative line with styled markers
ax.plot(
    components,
    cumulative,
    color="#306998",
    linewidth=3,
    marker="o",
    markersize=10,
    markerfacecolor="white",
    markeredgecolor="#306998",
    markeredgewidth=2.5,
    label="Cumulative variance",
    zorder=5,
    path_effects=[pe.Stroke(linewidth=5, foreground="white", alpha=0.4), pe.Normal()],
)

# Threshold lines and crossing annotations with dynamic positioning
for i, ((t, label, color), n_comp) in enumerate(zip(thresholds, n_at_threshold, strict=True)):
    ax.axhline(y=t, color=color, linestyle="--", linewidth=1.8, alpha=0.55, label=f"{label} threshold")
    ax.plot(n_comp, t, marker="D", color=color, markersize=13, zorder=6, markeredgecolor="white", markeredgewidth=1.5)
    # Dynamic offset: position annotation in the empty space to the left of the crossing point
    text_x = max(n_comp - 4.0, 1.5)
    text_y = t + (0.05 if i == 1 else -0.08)
    ax.annotate(
        f"{n_comp} components \u2192 {label} variance",
        xy=(n_comp, t),
        xytext=(text_x, text_y),
        fontsize=14,
        fontweight="medium",
        color=color,
        arrowprops={"arrowstyle": "-|>", "color": color, "lw": 1.5, "connectionstyle": "arc3,rad=0.15"},
        bbox={"boxstyle": "round,pad=0.35", "facecolor": "white", "edgecolor": color, "alpha": 0.92},
        zorder=7,
    )

# Elbow point annotation
ax.plot(
    elbow_component,
    cumulative[elbow_idx],
    marker="*",
    color="#2E8B57",
    markersize=18,
    zorder=6,
    markeredgecolor="white",
    markeredgewidth=1.0,
    label="Elbow point",
)
elbow_text_y = cumulative[elbow_idx] - 0.10
ax.annotate(
    f"Elbow at {elbow_component} components ({cumulative[elbow_idx]:.0%})",
    xy=(elbow_component, cumulative[elbow_idx]),
    xytext=(elbow_component + 2.5, elbow_text_y),
    fontsize=13,
    fontweight="medium",
    color="#2E8B57",
    arrowprops={"arrowstyle": "-|>", "color": "#2E8B57", "lw": 1.5, "connectionstyle": "arc3,rad=-0.2"},
    bbox={"boxstyle": "round,pad=0.35", "facecolor": "white", "edgecolor": "#2E8B57", "alpha": 0.92},
    zorder=7,
)

# Formatting
ax.set_xlabel("Number of Components", fontsize=20, labelpad=10)
ax.set_ylabel("Explained Variance (%)", fontsize=20, labelpad=10)
ax.set_title(
    "line-pca-variance-cumulative \u00b7 matplotlib \u00b7 pyplots.ai",
    fontsize=24,
    fontweight="medium",
    pad=18,
    color="#333333",
)
ax.tick_params(axis="both", labelsize=16, colors="#555555")
ax.set_xticks(components)
ax.set_xlim(0.3, len(components) + 0.7)
ax.set_ylim(0, 1.05)

# Y-axis percentage formatting
ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda v, _: f"{v:.0%}"))

# Minor ticks for additional refinement
ax.yaxis.set_minor_locator(mticker.AutoMinorLocator(2))
ax.tick_params(axis="y", which="minor", length=3, color="#cccccc")

# Visual refinement
for spine in ("top", "right"):
    ax.spines[spine].set_visible(False)
for spine in ("left", "bottom"):
    ax.spines[spine].set_linewidth(0.6)
    ax.spines[spine].set_color("#999999")

ax.yaxis.grid(True, which="major", alpha=0.18, linewidth=0.7, color="#999999")
ax.yaxis.grid(True, which="minor", alpha=0.08, linewidth=0.4, color="#bbbbbb")
ax.set_axisbelow(True)

# Legend with refined styling
legend = ax.legend(
    fontsize=15, loc="lower right", framealpha=0.95, edgecolor="#cccccc", fancybox=True, borderpad=0.8, handlelength=2.5
)
legend.get_frame().set_linewidth(0.6)

plt.tight_layout(pad=1.5)
plt.savefig("plot.png", dpi=300, bbox_inches="tight", facecolor=fig.get_facecolor())
