""" anyplot.ai
violin-grouped-swarm: Grouped Violin Plot with Swarm Overlay
Library: seaborn 0.13.2 | Python 3.13.13
Quality: 93/100 | Updated: 2026-05-18
"""

import os

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Okabe-Ito palette
OKABE_ITO = ["#009E73", "#D55E00"]

# Data: Cognitive test performance across different test types and experience levels
np.random.seed(42)

test_types = ["Reading Comprehension", "Arithmetic", "Pattern Recognition"]
experience_levels = ["Novice", "Expert"]

data = []
for test_type in test_types:
    for exp_level in experience_levels:
        # Create different distributions based on test type and experience
        if test_type == "Reading Comprehension":
            base_mean = 72 if exp_level == "Novice" else 88
            base_std = 12 if exp_level == "Novice" else 6
        elif test_type == "Arithmetic":
            base_mean = 65 if exp_level == "Novice" else 85
            base_std = 15 if exp_level == "Novice" else 8
        else:  # Pattern Recognition
            base_mean = 58 if exp_level == "Novice" else 82
            base_std = 18 if exp_level == "Novice" else 10

        scores = np.random.normal(base_mean, base_std, 45)
        scores = np.clip(scores, 20, 100)  # Keep scores in 0-100 range

        for score in scores:
            data.append({"Test Type": test_type, "Experience": exp_level, "Score": score})

df = pd.DataFrame(data)

# Plot
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

# Violin plot with transparency
sns.violinplot(
    data=df, x="Test Type", y="Score", hue="Experience", palette=OKABE_ITO, alpha=0.5, inner=None, ax=ax, linewidth=2
)

# Swarm overlay with matching colors and dodging
sns.swarmplot(
    data=df,
    x="Test Type",
    y="Score",
    hue="Experience",
    palette=OKABE_ITO,
    dodge=True,
    size=3.5,
    alpha=0.7,
    ax=ax,
    legend=False,
)

# Labels and styling
ax.set_xlabel("Test Type", fontsize=20, color=INK)
ax.set_ylabel("Score", fontsize=20, color=INK)
ax.set_title("violin-grouped-swarm · Python · seaborn · anyplot.ai", fontsize=24, fontweight="medium", color=INK)
ax.tick_params(axis="both", labelsize=16, colors=INK_SOFT)

# Remove top and right spines
ax.spines["top"].set_visible(False)
ax.spines["right"].set_visible(False)
ax.spines["left"].set_color(INK_SOFT)
ax.spines["bottom"].set_color(INK_SOFT)

# Subtle grid on y-axis
ax.yaxis.grid(True, alpha=0.10, linewidth=0.8, color=INK)
ax.set_axisbelow(True)

# Legend styling
ax.legend(title="Experience", fontsize=16, title_fontsize=18, loc="upper right")

plt.tight_layout()
plt.savefig(f"plot-{THEME}.png", dpi=300, bbox_inches="tight", facecolor=PAGE_BG)
