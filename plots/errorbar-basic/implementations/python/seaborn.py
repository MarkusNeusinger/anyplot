""" anyplot.ai
errorbar-basic: Basic Error Bar Plot
Library: seaborn 0.13.2 | Python 3.14.4
Quality: 89/100 | Updated: 2026-04-25
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

OKABE_ITO = ["#009E73", "#D55E00", "#0072B2", "#CC79A7", "#E69F00", "#56B4E9", "#F0E442"]
BRAND = OKABE_ITO[0]
ACCENT = OKABE_ITO[1]

# Clinical trial: symptom reduction (%) measured for each treatment group
np.random.seed(42)
categories = ["Control", "Treatment A", "Treatment B", "Treatment C", "Treatment D", "Treatment E"]
means = [45.2, 52.8, 61.3, 48.7, 57.4, 43.1]
stds = [4.5, 6.2, 5.8, 7.1, 4.9, 5.5]
n_per_group = 30

records = [
    {"Treatment": cat, "Symptom Reduction (%)": value}
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
        "grid.alpha": 0.10,
        "legend.facecolor": ELEVATED_BG,
        "legend.edgecolor": INK_SOFT,
    },
)

fig, ax = plt.subplots(figsize=(16, 9))

sns.barplot(
    data=df,
    x="Treatment",
    y="Symptom Reduction (%)",
    hue="Treatment",
    palette=palette,
    legend=False,
    errorbar="sd",
    capsize=0.25,
    err_kws={"color": INK, "linewidth": 2.5},
    edgecolor=INK_SOFT,
    linewidth=1.0,
    ax=ax,
)

ax.set_xlabel("Treatment Group", fontsize=20)
ax.set_ylabel("Symptom Reduction (%)", fontsize=20)
ax.set_title("errorbar-basic · seaborn · anyplot.ai", fontsize=24, fontweight="medium", color=INK)
ax.tick_params(axis="both", labelsize=16)
ax.yaxis.grid(True)
ax.xaxis.grid(False)
ax.set_axisbelow(True)
ax.spines["top"].set_visible(False)
ax.spines["right"].set_visible(False)

plt.tight_layout()
plt.savefig(f"plot-{THEME}.png", dpi=300, bbox_inches="tight", facecolor=PAGE_BG)
