""" pyplots.ai
funnel-meta-analysis: Meta-Analysis Funnel Plot for Publication Bias
Library: matplotlib 3.10.8 | Python 3.14.3
Quality: 91/100 | Created: 2026-03-15
"""

import matplotlib.patheffects as pe
import matplotlib.pyplot as plt
import numpy as np


# Data - 15 RCTs comparing drug vs placebo (log odds ratios)
np.random.seed(42)
n_studies = 15
true_effect = -0.4

std_errors = np.concatenate(
    [np.random.uniform(0.05, 0.15, 4), np.random.uniform(0.15, 0.30, 5), np.random.uniform(0.30, 0.55, 6)]
)

effect_sizes = true_effect + np.random.normal(0, std_errors)

# Introduce mild asymmetry (publication bias): shift small studies toward significance
small_study_mask = std_errors > 0.35
effect_sizes[small_study_mask] -= np.random.uniform(0.05, 0.20, small_study_mask.sum())

summary_effect = np.average(effect_sizes, weights=1 / std_errors**2)

# Funnel boundaries
se_range = np.linspace(0, 0.60, 200)
upper_ci = summary_effect + 1.96 * se_range
lower_ci = summary_effect - 1.96 * se_range

# Classify studies: inside or outside the funnel
study_upper = summary_effect + 1.96 * std_errors
study_lower = summary_effect - 1.96 * std_errors
inside_funnel = (effect_sizes >= study_lower) & (effect_sizes <= study_upper)

# Plot
fig, ax = plt.subplots(figsize=(16, 9))

# Funnel region
ax.fill_betweenx(se_range, lower_ci, upper_ci, color="#306998", alpha=0.06)
ax.plot(upper_ci, se_range, color="#306998", linewidth=1.8, alpha=0.4, linestyle="--")
ax.plot(lower_ci, se_range, color="#306998", linewidth=1.8, alpha=0.4, linestyle="--")

# Reference lines
summary_line = ax.axvline(x=summary_effect, color="#306998", linewidth=2.5, alpha=0.7, label="Summary effect")
summary_line.set_path_effects([pe.Stroke(linewidth=4, foreground="white", alpha=0.3), pe.Normal()])
ax.axvline(x=0, color="#999999", linewidth=1.5, linestyle=":", alpha=0.6, label="Null effect (OR=1)")

# Studies - color by position relative to funnel
ax.scatter(
    effect_sizes[inside_funnel],
    std_errors[inside_funnel],
    s=240,
    color="#306998",
    edgecolors="white",
    linewidth=1.0,
    zorder=5,
    alpha=0.85,
    label="Inside funnel",
)
ax.scatter(
    effect_sizes[~inside_funnel],
    std_errors[~inside_funnel],
    s=240,
    color="#C44E52",
    edgecolors="white",
    linewidth=1.0,
    zorder=5,
    alpha=0.85,
    marker="D",
    label="Outside funnel",
)

# Annotate outlier studies outside the funnel
if (~inside_funnel).any():
    outlier_idx = np.where(~inside_funnel)[0]
    # Pick the outlier on the negative side (left) where there's more annotation space
    left_outliers = outlier_idx[effect_sizes[outlier_idx] < summary_effect]
    if len(left_outliers) > 0:
        target = left_outliers[np.argmax(std_errors[left_outliers])]
    else:
        target = outlier_idx[np.argmax(np.abs(effect_sizes[outlier_idx] - summary_effect))]
    ax.annotate(
        "Potential\npublication bias",
        xy=(effect_sizes[target], std_errors[target]),
        xytext=(effect_sizes[target] + 0.35, std_errors[target] + 0.06),
        fontsize=13,
        color="#C44E52",
        fontweight="medium",
        ha="left",
        arrowprops={"arrowstyle": "->", "color": "#C44E52", "lw": 1.5, "connectionstyle": "arc3,rad=-0.2"},
        path_effects=[pe.withStroke(linewidth=3, foreground="white")],
    )

# Subtle grid
ax.yaxis.grid(True, alpha=0.15, linewidth=0.8, color="#cccccc")
ax.xaxis.grid(True, alpha=0.10, linewidth=0.6, color="#cccccc")

# Style
ax.set_xlabel("Log Odds Ratio", fontsize=20)
ax.set_ylabel("Standard Error", fontsize=20)
ax.set_title(
    "funnel-meta-analysis · matplotlib · pyplots.ai",
    fontsize=24,
    fontweight="medium",
    path_effects=[pe.withStroke(linewidth=4, foreground="white")],
)
ax.tick_params(axis="both", labelsize=16)

ax.invert_yaxis()
ax.set_ylim(0.65, 0)

ax.spines["top"].set_visible(False)
ax.spines["right"].set_visible(False)

ax.legend(fontsize=16, frameon=False, loc="upper right")

plt.tight_layout()
plt.savefig("plot.png", dpi=300, bbox_inches="tight")
