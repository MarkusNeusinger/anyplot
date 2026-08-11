"""anyplot.ai
bland-altman-basic: Bland-Altman Agreement Plot
Library: matplotlib 3.11.1 | Python 3.13.14
Quality: 84/100 | Updated: 2026-08-11
"""

import os

import matplotlib.pyplot as plt
import matplotlib.transforms as transforms
import numpy as np


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
BRAND = "#009E73"  # Okabe-Ito position 1 — first categorical series
ACCENT2 = "#C475FD"  # Okabe-Ito position 2 — for limits of agreement lines

# Data: Simulated blood pressure readings from two sphygmomanometers
np.random.seed(42)
n_samples = 80

# Method 1: Reference sphygmomanometer
method1 = np.random.normal(120, 15, n_samples)

# Method 2: New sphygmomanometer — constant bias plus error that widens at
# higher pressure readings (mild heteroscedasticity), the proportional-bias
# pattern Bland-Altman plots are specifically designed to expose
bias_true = 2.5
error_scale = 4.0 + 0.08 * (method1 - method1.min())
method2 = method1 + bias_true + np.random.normal(0, 1, n_samples) * error_scale

# Bland-Altman calculations
mean_values = (method1 + method2) / 2
differences = method1 - method2

mean_diff = np.mean(differences)
std_diff = np.std(differences, ddof=1)
upper_loa = mean_diff + 1.96 * std_diff
lower_loa = mean_diff - 1.96 * std_diff

# Plot
fig, ax = plt.subplots(figsize=(8, 4.5), dpi=400, facecolor=PAGE_BG)
ax.set_facecolor(PAGE_BG)

# Scatter points with transparency
ax.scatter(mean_values, differences, s=130, alpha=0.65, color=BRAND, edgecolors=PAGE_BG, linewidth=0.5)

# Mean difference (bias) line
ax.axhline(y=mean_diff, color=BRAND, linestyle="-", linewidth=2.5)

# Limits of agreement (dashed lines)
ax.axhline(y=upper_loa, color=ACCENT2, linestyle="--", linewidth=2.5)
ax.axhline(y=lower_loa, color=ACCENT2, linestyle="--", linewidth=2.5)

# Zero reference line (subtle)
ax.axhline(y=0, color=INK_SOFT, linestyle=":", linewidth=1.5, alpha=0.4)

# Value annotations, anchored to the axes fraction in x (via a blended
# transform) so they stay flush against the right edge regardless of the
# data range — the bias line gets a plain label, the LOA lines get an
# arrow-connected callout so the reader can trace label back to line
trans = transforms.blended_transform_factory(ax.transAxes, ax.transData)
ax.annotate(
    f"Bias: {mean_diff:.2f}",
    xy=(1.0, mean_diff),
    xycoords=trans,
    xytext=(12, 0),
    textcoords="offset points",
    fontsize=8,
    va="center",
    ha="left",
    color=INK,
    fontweight="bold",
    annotation_clip=False,
)
for loa_value, loa_label in ((upper_loa, f"+1.96 SD: {upper_loa:.2f}"), (lower_loa, f"-1.96 SD: {lower_loa:.2f}")):
    ax.annotate(
        loa_label,
        xy=(1.0, loa_value),
        xycoords=trans,
        xytext=(24, 0),
        textcoords="offset points",
        fontsize=8,
        va="center",
        ha="left",
        color=INK_SOFT,
        arrowprops={"arrowstyle": "->", "color": INK_SOFT, "linewidth": 0.8, "shrinkA": 0, "shrinkB": 3},
        annotation_clip=False,
    )

# Labels and title
ax.set_xlabel("Mean of Two Methods (mmHg)", fontsize=10, color=INK)
ax.set_ylabel("Difference (Method 1 - Method 2) (mmHg)", fontsize=10, color=INK)
ax.set_title("bland-altman-basic · python · matplotlib · anyplot.ai", fontsize=12, color=INK, fontweight="medium")

# Tick parameters
ax.tick_params(axis="both", labelsize=8, colors=INK_SOFT, labelcolor=INK_SOFT)

# Spines
for s in ("left", "bottom"):
    ax.spines[s].set_color(INK_SOFT)
ax.spines["top"].set_visible(False)
ax.spines["right"].set_visible(False)

# Grid
ax.yaxis.grid(True, alpha=0.10, linewidth=0.8, color=INK)

# Adjust layout — right margin reserved for the line-anchored annotations
plt.tight_layout()
plt.subplots_adjust(right=0.82)

plt.savefig(f"plot-{THEME}.png", dpi=400, facecolor=PAGE_BG)
