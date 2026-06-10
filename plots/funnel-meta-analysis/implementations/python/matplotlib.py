"""anyplot.ai
funnel-meta-analysis: Meta-Analysis Funnel Plot for Publication Bias
Library: matplotlib 3.10.9 | Python 3.13.13
Quality: 88/100 | Updated: 2026-06-10
"""

import os

import matplotlib.patheffects as pe
import matplotlib.pyplot as plt
import numpy as np


# Theme
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
INK_MUTED = "#6B6A63" if THEME == "light" else "#A8A79F"

# Imprint palette — position 1 (inside funnel) and position 5 semantic anchor (outside = bias)
BRAND = "#009E73"  # Imprint palette position 1
RED = "#AE3030"  # Imprint palette position 5 — semantic anchor for bad/error

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

# Classify studies: inside or outside the pseudo 95% CI funnel
study_upper = summary_effect + 1.96 * std_errors
study_lower = summary_effect - 1.96 * std_errors
inside_funnel = (effect_sizes >= study_lower) & (effect_sizes <= study_upper)

# Weight-proportional marker sizing — standard meta-analysis convention (larger = more precise)
weights = 1 / std_errors**2
w_min, w_max = weights.min(), weights.max()
marker_sizes = 80 + (weights - w_min) / (w_max - w_min) * 440  # range: 80–520

# Plot
fig, ax = plt.subplots(figsize=(8, 4.5), dpi=400, facecolor=PAGE_BG)
ax.set_facecolor(PAGE_BG)

# Funnel region
ax.fill_betweenx(se_range, lower_ci, upper_ci, color=BRAND, alpha=0.06)
ax.plot(upper_ci, se_range, color=BRAND, linewidth=1.8, alpha=0.5, linestyle="--")
ax.plot(lower_ci, se_range, color=BRAND, linewidth=1.8, alpha=0.5, linestyle="--")

# Reference lines
summary_line = ax.axvline(x=summary_effect, color=INK, linewidth=2.0, alpha=0.85, label="Summary effect")
summary_line.set_path_effects([pe.Stroke(linewidth=3.5, foreground=PAGE_BG, alpha=0.5), pe.Normal()])
ax.axvline(x=0, color=INK_SOFT, linewidth=1.5, linestyle=":", alpha=0.6, label="Null effect (OR=1)")

# Studies — color by funnel position, sized by inverse-variance weight
ax.scatter(
    effect_sizes[inside_funnel],
    std_errors[inside_funnel],
    s=marker_sizes[inside_funnel],
    color=BRAND,
    edgecolors=PAGE_BG,
    linewidth=0.8,
    zorder=5,
    alpha=0.85,
    label="Inside funnel",
)
ax.scatter(
    effect_sizes[~inside_funnel],
    std_errors[~inside_funnel],
    s=marker_sizes[~inside_funnel],
    color=RED,
    edgecolors=PAGE_BG,
    linewidth=0.8,
    zorder=5,
    alpha=0.85,
    marker="D",
    label="Outside funnel",
)

# Annotate the most prominent outlier suggesting publication bias
if (~inside_funnel).any():
    outlier_idx = np.where(~inside_funnel)[0]
    left_outliers = outlier_idx[effect_sizes[outlier_idx] < summary_effect]
    if len(left_outliers) > 0:
        target = left_outliers[np.argmax(std_errors[left_outliers])]
    else:
        target = outlier_idx[np.argmax(np.abs(effect_sizes[outlier_idx] - summary_effect))]
    ax.annotate(
        "Potential\npublication bias",
        xy=(effect_sizes[target], std_errors[target]),
        xytext=(effect_sizes[target] + 0.35, std_errors[target] + 0.06),
        fontsize=9,
        color=RED,
        fontweight="medium",
        ha="left",
        arrowprops={"arrowstyle": "->", "color": RED, "lw": 1.5, "connectionstyle": "arc3,rad=-0.2"},
        path_effects=[pe.withStroke(linewidth=3, foreground=PAGE_BG)],
    )

# Subtle y-axis grid only
ax.yaxis.grid(True, alpha=0.15, linewidth=0.8, color=INK)

# Style
ax.set_ylim(0.65, 0)  # inverted: SE=0 (precise studies) at top, larger SE at bottom

ax.set_xlabel("Log Odds Ratio", fontsize=10, color=INK)
ax.set_ylabel("Standard Error", fontsize=10, color=INK)

title = "funnel-meta-analysis · python · matplotlib · anyplot.ai"
title_fontsize = max(8, round(12 * 67 / len(title))) if len(title) > 67 else 12
ax.set_title(
    title,
    fontsize=title_fontsize,
    fontweight="medium",
    color=INK,
    path_effects=[pe.withStroke(linewidth=4, foreground=PAGE_BG, alpha=0.6)],
)

ax.tick_params(axis="both", labelsize=8, colors=INK_SOFT, labelcolor=INK_SOFT)
ax.spines["top"].set_visible(False)
ax.spines["right"].set_visible(False)
for s in ("left", "bottom"):
    ax.spines[s].set_color(INK_SOFT)

leg = ax.legend(fontsize=8, loc="upper right")
leg.get_frame().set_facecolor(ELEVATED_BG)
leg.get_frame().set_edgecolor(INK_SOFT)
plt.setp(leg.get_texts(), color=INK_SOFT)

fig.subplots_adjust(left=0.10, right=0.95, top=0.91, bottom=0.13)
plt.savefig(f"plot-{THEME}.png", dpi=400, facecolor=PAGE_BG)
