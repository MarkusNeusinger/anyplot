""" anyplot.ai
strip-basic: Basic Strip Plot
Library: seaborn 0.13.2 | Python 3.13.13
Quality: 87/100 | Updated: 2026-05-04
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
NEUTRAL = "#1A1A1A" if THEME == "light" else "#E8E8E0"

# Okabe-Ito palette — first series always #009E73
OKABE_ITO = ["#009E73", "#D55E00", "#0072B2", "#CC79A7"]

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

# Data — employee satisfaction scores by department
np.random.seed(42)

departments = ["Engineering", "Marketing", "Sales", "HR"]
records = []

for dept in departments:
    if dept == "Engineering":
        scores = np.random.normal(78, 8, 35)
    elif dept == "Marketing":
        scores = np.random.normal(72, 12, 40)
    elif dept == "Sales":
        scores = np.concatenate([np.random.normal(65, 6, 25), np.random.normal(80, 5, 15)])
    else:  # HR
        scores = np.random.normal(68, 10, 30)

    scores = np.clip(scores, 40, 100)
    for s in scores:
        records.append({"Department": dept, "Satisfaction Score": s})

df = pd.DataFrame(records)

# Plot
fig, ax = plt.subplots(figsize=(16, 9), facecolor=PAGE_BG)
ax.set_facecolor(PAGE_BG)

sns.stripplot(
    data=df,
    x="Department",
    y="Satisfaction Score",
    hue="Department",
    palette=OKABE_ITO,
    alpha=0.7,
    size=12,
    jitter=0.25,
    edgecolor=PAGE_BG,
    linewidth=0.5,
    ax=ax,
    legend=False,
)

# Add horizontal mean lines as reference
means = df.groupby("Department")["Satisfaction Score"].mean()
for i, dept in enumerate(departments):
    ax.hlines(means[dept], i - 0.35, i + 0.35, colors=NEUTRAL, linewidth=2.5)

# Style
ax.set_xlabel("Department", fontsize=20, color=INK)
ax.set_ylabel("Satisfaction Score", fontsize=20, color=INK)
ax.set_title("strip-basic · seaborn · anyplot.ai", fontsize=24, fontweight="medium", color=INK)
ax.tick_params(axis="both", labelsize=16, colors=INK_SOFT)
ax.set_ylim(35, 105)
ax.yaxis.grid(True, alpha=0.10, linewidth=0.8, color=INK)
ax.spines["top"].set_visible(False)
ax.spines["right"].set_visible(False)
ax.spines["left"].set_color(INK_SOFT)
ax.spines["bottom"].set_color(INK_SOFT)

# Legend for mean reference line
ax.plot([], [], color=NEUTRAL, linewidth=2.5, label="Group Mean")
ax.legend(fontsize=14, loc="upper right", framealpha=1)

# Save
plt.tight_layout()
plt.savefig(f"plot-{THEME}.png", dpi=300, bbox_inches="tight", facecolor=PAGE_BG)
