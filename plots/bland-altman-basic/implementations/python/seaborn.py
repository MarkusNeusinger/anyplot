""" anyplot.ai
bland-altman-basic: Bland-Altman Agreement Plot
Library: seaborn 0.13.2 | Python 3.13.13
Quality: 90/100 | Updated: 2026-05-07
"""

import os
import sys


# Remove current directory from path to avoid importing this file as 'seaborn'
sys.path = [p for p in sys.path if os.path.abspath(p) != os.getcwd()]

import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import seaborn as sns  # noqa: E402


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
RULE = "rgba(26,26,23,0.10)" if THEME == "light" else "rgba(240,239,232,0.10)"

BRAND = "#009E73"  # Okabe-Ito position 1
ACCENT_1 = "#C475FD"  # Vermillion for LoA
NEUTRAL = "#6B6A63" if THEME == "light" else "#A8A79F"

# Data - Simulated blood pressure measurements from two sphygmomanometers
np.random.seed(42)
n = 80

# Method 1: Reference standard (e.g., mercury sphygmomanometer)
method1 = np.random.normal(120, 15, n)

# Method 2: New device with slight systematic bias and proportional error
method2 = method1 + np.random.normal(2, 5, n) + 0.02 * (method1 - 120)

# Calculate Bland-Altman statistics
mean_values = (method1 + method2) / 2
differences = method1 - method2
mean_diff = np.mean(differences)
std_diff = np.std(differences, ddof=1)
upper_loa = mean_diff + 1.96 * std_diff
lower_loa = mean_diff - 1.96 * std_diff

# Create plot
fig, ax = plt.subplots(figsize=(16, 9), facecolor=PAGE_BG)
ax.set_facecolor(PAGE_BG)

# Scatter plot of differences vs means
sns.scatterplot(x=mean_values, y=differences, s=150, alpha=0.7, color=BRAND, edgecolor=PAGE_BG, linewidth=0.5, ax=ax)

# Mean difference line (bias)
ax.axhline(y=mean_diff, color=BRAND, linewidth=3, label=f"Mean: {mean_diff:.2f} mmHg")

# Limits of agreement (±1.96 SD)
ax.axhline(y=upper_loa, color=ACCENT_1, linewidth=2, linestyle="--", label=f"+1.96 SD: {upper_loa:.2f} mmHg")
ax.axhline(y=lower_loa, color=ACCENT_1, linewidth=2, linestyle="--", label=f"-1.96 SD: {lower_loa:.2f} mmHg")

# Zero reference line
ax.axhline(y=0, color=NEUTRAL, linewidth=1, linestyle=":", alpha=0.6)

# Annotate values on the right side
x_max = ax.get_xlim()[1]
ax.annotate(
    f"{mean_diff:.1f}",
    xy=(x_max, mean_diff),
    xytext=(5, 0),
    textcoords="offset points",
    fontsize=16,
    color=BRAND,
    fontweight="bold",
    va="center",
)
ax.annotate(
    f"{upper_loa:.1f}",
    xy=(x_max, upper_loa),
    xytext=(5, 0),
    textcoords="offset points",
    fontsize=14,
    color=ACCENT_1,
    va="center",
)
ax.annotate(
    f"{lower_loa:.1f}",
    xy=(x_max, lower_loa),
    xytext=(5, 0),
    textcoords="offset points",
    fontsize=14,
    color=ACCENT_1,
    va="center",
)

# Labels and styling
ax.set_xlabel("Mean of Two Methods (mmHg)", fontsize=20, color=INK)
ax.set_ylabel("Difference (Method 1 - Method 2) (mmHg)", fontsize=20, color=INK)
ax.set_title("bland-altman-basic · seaborn · anyplot.ai", fontsize=24, fontweight="medium", color=INK)
ax.tick_params(axis="both", labelsize=16, colors=INK_SOFT)

# Spine styling
ax.spines["top"].set_visible(False)
ax.spines["right"].set_visible(False)
for spine in ["left", "bottom"]:
    ax.spines[spine].set_color(INK_SOFT)

# Grid - subtle
ax.yaxis.grid(True, alpha=0.10, linewidth=0.8, color=INK)

# Legend with theme-adaptive styling
ax.legend(loc="upper left", fontsize=14, facecolor=ELEVATED_BG, edgecolor=INK_SOFT, framealpha=1.0)

plt.tight_layout()
plt.savefig(f"plot-{THEME}.png", dpi=300, bbox_inches="tight", facecolor=PAGE_BG)
