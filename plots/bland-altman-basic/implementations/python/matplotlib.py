""" anyplot.ai
bland-altman-basic: Bland-Altman Agreement Plot
Library: matplotlib 3.10.9 | Python 3.13.13
Quality: 98/100 | Updated: 2026-05-07
"""

import os

import matplotlib.pyplot as plt
import numpy as np


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
BRAND = "#009E73"  # Okabe-Ito position 1 — first categorical series
ACCENT2 = "#C475FD"  # Okabe-Ito position 2 — for limits of agreement lines

# Data: Simulated blood pressure readings from two sphygmomanometers
np.random.seed(42)
n_samples = 80

# Method 1: Reference sphygmomanometer
method1 = np.random.normal(120, 15, n_samples)

# Method 2: New sphygmomanometer (slightly biased with some random error)
bias_true = 2.5
method2 = method1 + bias_true + np.random.normal(0, 5, n_samples)

# Bland-Altman calculations
mean_values = (method1 + method2) / 2
differences = method1 - method2

mean_diff = np.mean(differences)
std_diff = np.std(differences, ddof=1)
upper_loa = mean_diff + 1.96 * std_diff
lower_loa = mean_diff - 1.96 * std_diff

# Plot
fig, ax = plt.subplots(figsize=(16, 9), facecolor=PAGE_BG)
ax.set_facecolor(PAGE_BG)

# Scatter points with transparency
ax.scatter(mean_values, differences, s=150, alpha=0.6, color=BRAND, edgecolors=PAGE_BG, linewidth=0.5)

# Mean difference (bias) line
ax.axhline(y=mean_diff, color=BRAND, linestyle="-", linewidth=2.5, label=f"Mean: {mean_diff:.2f} mmHg")

# Limits of agreement (dashed lines)
ax.axhline(y=upper_loa, color=ACCENT2, linestyle="--", linewidth=2.5, label=f"+1.96 SD: {upper_loa:.2f} mmHg")
ax.axhline(y=lower_loa, color=ACCENT2, linestyle="--", linewidth=2.5, label=f"-1.96 SD: {lower_loa:.2f} mmHg")

# Zero reference line (subtle)
ax.axhline(y=0, color=INK_SOFT, linestyle=":", linewidth=1.5, alpha=0.4)

# Annotations on the right side
x_max = ax.get_xlim()[1]
ax.text(
    x_max + 1, mean_diff, f"Bias: {mean_diff:.2f}", fontsize=14, va="center", ha="left", color=INK, fontweight="bold"
)
ax.text(x_max + 1, upper_loa, f"+1.96 SD: {upper_loa:.2f}", fontsize=14, va="center", ha="left", color=INK_SOFT)
ax.text(x_max + 1, lower_loa, f"-1.96 SD: {lower_loa:.2f}", fontsize=14, va="center", ha="left", color=INK_SOFT)

# Labels and title
ax.set_xlabel("Mean of Two Methods (mmHg)", fontsize=20, color=INK)
ax.set_ylabel("Difference (Method 1 - Method 2) (mmHg)", fontsize=20, color=INK)
ax.set_title("bland-altman-basic · matplotlib · anyplot.ai", fontsize=24, color=INK, fontweight="medium")

# Tick parameters
ax.tick_params(axis="both", labelsize=16, colors=INK_SOFT, labelcolor=INK_SOFT)

# Spines
for s in ("left", "bottom"):
    ax.spines[s].set_color(INK_SOFT)
ax.spines["top"].set_visible(False)
ax.spines["right"].set_visible(False)

# Grid
ax.yaxis.grid(True, alpha=0.10, linewidth=0.8, color=INK)

# Legend
leg = ax.legend(fontsize=14, loc="upper left")
if leg:
    leg.get_frame().set_facecolor(ELEVATED_BG)
    leg.get_frame().set_edgecolor(INK_SOFT)
    leg.get_frame().set_linewidth(0.8)
    plt.setp(leg.get_texts(), color=INK_SOFT)

# Adjust layout
plt.tight_layout()
plt.subplots_adjust(right=0.85)

plt.savefig(f"plot-{THEME}.png", dpi=300, bbox_inches="tight", facecolor=PAGE_BG)
