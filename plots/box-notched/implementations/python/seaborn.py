""" anyplot.ai
box-notched: Notched Box Plot
Library: seaborn 0.13.2 | Python 3.13.13
Quality: 94/100 | Updated: 2026-05-07
"""

import os

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns


THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

IMPRINT = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD"]

# Data - Test score distributions across student cohorts
np.random.seed(42)

cohorts = ["Cohort A", "Cohort B", "Cohort C", "Cohort D"]
data = []

# Cohort A: strong performance, tight cluster
data.extend([{"Cohort": "Cohort A", "Test Score": val} for val in np.random.normal(82, 8, 85)])

# Cohort B: moderate performance, some high outliers
cohort_b_base = np.random.normal(75, 12, 75)
cohort_b_outliers = np.array([95, 96, 98])
data.extend([{"Cohort": "Cohort B", "Test Score": val} for val in np.concatenate([cohort_b_base, cohort_b_outliers])])

# Cohort C: wide variation in performance
data.extend([{"Cohort": "Cohort C", "Test Score": val} for val in np.random.normal(70, 15, 80)])

# Cohort D: lower performance, tight clustering
data.extend([{"Cohort": "Cohort D", "Test Score": val} for val in np.random.normal(68, 9, 70)])

df = pd.DataFrame(data)

# Setup theme
sns.set_theme(
    style="whitegrid",
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

# Create plot
fig, ax = plt.subplots(figsize=(16, 9), facecolor=PAGE_BG)

# Create notched box plot with Okabe-Ito palette
sns.boxplot(
    data=df,
    x="Cohort",
    y="Test Score",
    hue="Cohort",
    palette=IMPRINT[: len(cohorts)],
    notch=True,
    width=0.5,
    linewidth=2.0,
    fliersize=10,
    flierprops={"marker": "o", "markerfacecolor": INK_SOFT, "markeredgecolor": INK, "alpha": 0.6},
    ax=ax,
    legend=False,
)

# Styling
ax.set_title("box-notched · seaborn · anyplot.ai", fontsize=24, fontweight="medium", color=INK)
ax.set_xlabel("Student Cohort", fontsize=20, color=INK)
ax.set_ylabel("Test Score (%)", fontsize=20, color=INK)
ax.tick_params(axis="both", labelsize=16, colors=INK_SOFT)

# Remove top and right spines
ax.spines["top"].set_visible(False)
ax.spines["right"].set_visible(False)
ax.spines["left"].set_color(INK_SOFT)
ax.spines["bottom"].set_color(INK_SOFT)

# Grid styling
ax.yaxis.grid(True, alpha=0.15, linewidth=0.8, color=INK)
ax.set_axisbelow(True)

plt.tight_layout()
plt.savefig(f"plot-{THEME}.png", dpi=300, bbox_inches="tight", facecolor=PAGE_BG)
