"""anyplot.ai
strip-basic: Basic Strip Plot
Library: seaborn 0.13.2 | Python 3.13.13
Quality: 90/100 | Updated: 2026-08-05
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

# Imprint palette — canonical order, first series always #009E73
IMPRINT = ["#009E73", "#C475FD", "#4467A3", "#BD8233"]

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
        "grid.alpha": 0.15,
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

# Plot — see default-style-guide.md "Visual Sizing Defaults" for canvas + sizing values
fig, ax = plt.subplots(figsize=(8, 4.5), dpi=400, facecolor=PAGE_BG)
ax.set_facecolor(PAGE_BG)

sns.stripplot(
    data=df,
    x="Department",
    y="Satisfaction Score",
    hue="Department",
    palette=IMPRINT,
    alpha=0.7,
    size=6,
    jitter=0.25,
    edgecolor=PAGE_BG,
    linewidth=0.4,
    ax=ax,
    legend=False,
)

# Group means as diamond markers — seaborn pointplot overlay, no connecting line/error bars
sns.pointplot(
    data=df,
    x="Department",
    y="Satisfaction Score",
    color=INK,
    markers="D",
    markersize=8,
    linestyle="none",
    errorbar=None,
    ax=ax,
)

# Style
ax.set_xlabel("Department", fontsize=10, color=INK)
ax.set_ylabel("Satisfaction Score", fontsize=10, color=INK)
ax.set_title("strip-basic · python · seaborn · anyplot.ai", fontsize=12, fontweight="medium", color=INK)
ax.tick_params(axis="both", labelsize=8, colors=INK_SOFT, length=0)
ax.set_ylim(35, 105)
ax.yaxis.grid(True, alpha=0.15, linewidth=0.8, color=INK)
sns.despine(ax=ax)
ax.spines["left"].set_color(INK_SOFT)
ax.spines["bottom"].set_color(INK_SOFT)

# Legend for mean reference marker
ax.plot([], [], marker="D", linestyle="none", color=INK, markersize=8, label="Group Mean")
ax.legend(fontsize=8, loc="upper right", framealpha=1)

# Save — bbox_inches MUST stay default (None); "tight" trims the canvas off-target
plt.tight_layout()
plt.savefig(f"plot-{THEME}.png", dpi=400, facecolor=PAGE_BG)
