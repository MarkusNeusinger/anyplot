""" anyplot.ai
errorbar-basic: Basic Error Bar Plot
Library: seaborn 0.13.2 | Python 3.13.14
Quality: 88/100 | Updated: 2026-06-30
"""

import os

import matplotlib.patches as mpatches
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns


THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
INK_MUTED = "#6B6A63" if THEME == "light" else "#A8A79F"

# Imprint palette
IMPRINT = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477"]
BRAND = IMPRINT[0]
ACCENT = IMPRINT[1]

# Clinical trial: symptom reduction (%) by dose group (n=30 per group)
np.random.seed(42)
categories = ["Control", "Placebo", "10 mg", "25 mg", "50 mg", "100 mg"]
means = [45.2, 46.8, 52.3, 57.4, 61.3, 58.9]
stds = [4.5, 5.1, 6.2, 4.9, 5.8, 7.1]
n_per_group = 30

records = [
    {"Dose": cat, "Symptom Reduction (%)": value}
    for cat, mu, sigma in zip(categories, means, stds, strict=True)
    for value in np.random.normal(mu, sigma, n_per_group)
]
df = pd.DataFrame(records)

top_performer = categories[int(np.argmax(means))]
palette = {c: (ACCENT if c == top_performer else BRAND) for c in categories}

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

fig, ax = plt.subplots(figsize=(8, 4.5), dpi=400)

sns.barplot(
    data=df,
    x="Dose",
    y="Symptom Reduction (%)",
    hue="Dose",
    palette=palette,
    legend=False,
    errorbar="sd",
    capsize=0.25,
    err_kws={"color": INK, "linewidth": 1.5},
    edgecolor=INK_SOFT,
    linewidth=0.6,
    ax=ax,
)

ax.set_xlabel("Dose Group", fontsize=10)
ax.set_ylabel("Symptom Reduction (%)", fontsize=10)
ax.tick_params(axis="both", labelsize=8)
ax.yaxis.grid(True, alpha=0.15, linewidth=0.8)
ax.xaxis.grid(False)
ax.set_axisbelow(True)
ax.spines["top"].set_visible(False)
ax.spines["right"].set_visible(False)

# Legend explaining the two-color strategy: all groups vs. top performer
brand_patch = mpatches.Patch(color=BRAND, label="Dose group")
accent_patch = mpatches.Patch(color=ACCENT, label=f"Top performer ({top_performer})")
ax.legend(handles=[brand_patch, accent_patch], fontsize=8, framealpha=0.9, loc="lower right")

# Title and subtitle placed in figure coordinates to control vertical spacing precisely
fig.text(
    0.5,
    0.96,
    "errorbar-basic · python · seaborn · anyplot.ai",
    ha="center",
    va="top",
    fontsize=12,
    fontweight="medium",
    color=INK,
)
fig.text(
    0.5,
    0.90,
    f"Bars show mean ± 1 SD — {top_performer} achieves the highest mean symptom reduction",
    ha="center",
    va="top",
    fontsize=9,
    color=INK_MUTED,
)

fig.subplots_adjust(top=0.81, bottom=0.13, left=0.11, right=0.97)
plt.savefig(f"plot-{THEME}.png", dpi=400, facecolor=PAGE_BG)
