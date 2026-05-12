"""anyplot.ai
box-horizontal: Horizontal Box Plot
Library: seaborn 0.13.2 | Python 3.13
Quality: pending | Created: 2026-05-12
"""

import os

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns


# Theme tokens (see prompts/default-style-guide.md "Background" + "Theme-adaptive Chrome")
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
BRAND = "#009E73"  # Okabe-Ito position 1 — ALWAYS first series

# Data - salary ranges by job title (with realistic distributions)
np.random.seed(42)

categories = ["Software Engineer", "Product Manager", "Data Scientist", "UX Designer", "DevOps Engineer"]

data = []
# Software Engineer - moderate spread
data.extend(
    [
        {"Job Title": "Software Engineer", "Salary (USD)": v}
        for v in np.concatenate(
            [
                np.random.normal(135000, 25000, 80),
                np.random.normal(200000, 15000, 5),  # outliers (senior/staff)
            ]
        )
    ]
)

# Product Manager - higher median with tight distribution
data.extend([{"Job Title": "Product Manager", "Salary (USD)": v} for v in np.random.normal(155000, 22000, 85)])

# Data Scientist - wide spread with high values
data.extend(
    [
        {"Job Title": "Data Scientist", "Salary (USD)": v}
        for v in np.concatenate(
            [
                np.random.normal(145000, 30000, 75),
                np.random.normal(220000, 20000, 10),  # outliers
            ]
        )
    ]
)

# UX Designer - moderate values
data.extend([{"Job Title": "UX Designer", "Salary (USD)": v} for v in np.random.normal(120000, 20000, 85)])

# DevOps Engineer - highest median, tight distribution
data.extend([{"Job Title": "DevOps Engineer", "Salary (USD)": v} for v in np.random.normal(160000, 18000, 90)])

df = pd.DataFrame(data)

# Sort categories by median for easier comparison
category_order = df.groupby("Job Title")["Salary (USD)"].median().sort_values().index.tolist()

# Set theme-adaptive styling
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

# Create figure
fig, ax = plt.subplots(figsize=(16, 9), facecolor=PAGE_BG)

# Horizontal box plot with single color
sns.boxplot(
    data=df,
    x="Salary (USD)",
    y="Job Title",
    order=category_order,
    color=BRAND,
    linewidth=2,
    width=0.6,
    flierprops={"marker": "o", "markersize": 8, "alpha": 0.6},
    ax=ax,
)

# Labels and styling
ax.set_xlabel("Salary (USD)", fontsize=20, color=INK)
ax.set_ylabel("Job Title", fontsize=20, color=INK)
ax.set_title("box-horizontal · seaborn · anyplot.ai", fontsize=24, fontweight="medium", color=INK)
ax.tick_params(axis="both", labelsize=16, colors=INK_SOFT)

# Spine styling
ax.spines["top"].set_visible(False)
ax.spines["right"].set_visible(False)
for spine in ("left", "bottom"):
    ax.spines[spine].set_color(INK_SOFT)

# Grid styling - subtle on x-axis only
ax.xaxis.grid(True, alpha=0.10, linewidth=0.8, color=INK)
ax.yaxis.grid(False)

# Adjust layout
plt.tight_layout()
plt.savefig(f"plot-{THEME}.png", dpi=300, bbox_inches="tight", facecolor=PAGE_BG)
