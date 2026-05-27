""" anyplot.ai
frequency-polygon-basic: Frequency Polygon for Distribution Comparison
Library: seaborn 0.13.2 | Python 3.13.13
Quality: 95/100 | Updated: 2026-05-17
"""

import os

import matplotlib.pyplot as plt
import numpy as np
import seaborn as sns


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Okabe-Ito palette - first series always #009E73
IMPRINT = ["#009E73", "#C475FD", "#4467A3"]

# Data - Test scores by class
np.random.seed(42)
n_per_group = 200

# Class A: well-distributed performance centered around 75
class_a = np.random.normal(loc=75, scale=12, size=n_per_group)

# Class B: higher achieving class centered around 82
class_b = np.random.normal(loc=82, scale=10, size=n_per_group)

# Class C: bimodal - mix of high performers and struggling students
class_c = np.concatenate(
    [
        np.random.normal(loc=70, scale=11, size=n_per_group // 2),
        np.random.normal(loc=88, scale=9, size=n_per_group // 2),
    ]
)

# Align bin edges across all groups for accurate comparison
all_scores = np.concatenate([class_a, class_b, class_c])
bins = np.linspace(max(0, all_scores.min() - 5), min(100, all_scores.max() + 5), 20)
bin_centers = (bins[:-1] + bins[1:]) / 2

# Compute frequencies for each class (extend to zero at ends for closed polygon)
class_a_counts, _ = np.histogram(class_a, bins=bins)
class_a_x = np.concatenate([[bins[0]], bin_centers, [bins[-1]]])
class_a_y = np.concatenate([[0], class_a_counts, [0]])

class_b_counts, _ = np.histogram(class_b, bins=bins)
class_b_x = np.concatenate([[bins[0]], bin_centers, [bins[-1]]])
class_b_y = np.concatenate([[0], class_b_counts, [0]])

class_c_counts, _ = np.histogram(class_c, bins=bins)
class_c_x = np.concatenate([[bins[0]], bin_centers, [bins[-1]]])
class_c_y = np.concatenate([[0], class_c_counts, [0]])

# Create figure with theme-aware styling
sns.set_theme(
    style="ticks",
    rc={
        "figure.facecolor": PAGE_BG,
        "axes.facecolor": PAGE_BG,
        "axes.edgecolor": INK_SOFT,
        "axes.labelcolor": INK,
        "text.color": INK,
        "xtick.color": INK_SOFT,
        "ytick.color": INK_SOFT,
        "grid.color": INK,
        "grid.alpha": 0.10,
        "legend.facecolor": ELEVATED_BG,
        "legend.edgecolor": INK_SOFT,
    },
)

fig, ax = plt.subplots(figsize=(16, 9), facecolor=PAGE_BG)
ax.set_facecolor(PAGE_BG)

# Plot frequency polygons using seaborn's lineplot
# Class A - Okabe-Ito position 1 (brand green)
sns.lineplot(
    x=class_a_x,
    y=class_a_y,
    ax=ax,
    linewidth=3,
    color=IMPRINT[0],
    label="Class A",
    marker="o",
    markersize=8,
    markevery=slice(1, -1),
)
ax.fill_between(class_a_x, class_a_y, alpha=0.15, color=IMPRINT[0])

# Class B - Okabe-Ito position 2 (vermillion)
sns.lineplot(
    x=class_b_x,
    y=class_b_y,
    ax=ax,
    linewidth=3,
    color=IMPRINT[1],
    label="Class B",
    marker="s",
    markersize=8,
    markevery=slice(1, -1),
)
ax.fill_between(class_b_x, class_b_y, alpha=0.15, color=IMPRINT[1])

# Class C - Okabe-Ito position 3 (blue)
sns.lineplot(
    x=class_c_x,
    y=class_c_y,
    ax=ax,
    linewidth=3,
    color=IMPRINT[2],
    label="Class C",
    marker="^",
    markersize=8,
    markevery=slice(1, -1),
)
ax.fill_between(class_c_x, class_c_y, alpha=0.15, color=IMPRINT[2])

# Styling
ax.set_xlabel("Test Score", fontsize=20, color=INK)
ax.set_ylabel("Frequency", fontsize=20, color=INK)
ax.set_title("frequency-polygon-basic · seaborn · anyplot.ai", fontsize=24, fontweight="medium", color=INK)
ax.tick_params(axis="both", labelsize=16, colors=INK_SOFT)
ax.spines["top"].set_visible(False)
ax.spines["right"].set_visible(False)
for spine in ("left", "bottom"):
    ax.spines[spine].set_color(INK_SOFT)
ax.yaxis.grid(True, alpha=0.10, linewidth=0.8, color=INK)
ax.legend(fontsize=16, loc="upper right", framealpha=0.95, edgecolor=INK_SOFT)
ax.set_ylim(bottom=0)

plt.tight_layout()
plt.savefig(f"plot-{THEME}.png", dpi=300, bbox_inches="tight", facecolor=PAGE_BG)
