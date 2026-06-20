"""anyplot.ai
heatmap-cohort-retention: Cohort Retention Heatmap
Library: seaborn | Python 3.13
Quality: pending | Created: 2026-06-20
"""

import os

import matplotlib.colors as mcolors
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

# Imprint sequential colormap — blue (low retention) to green (high retention)
imprint_seq = mcolors.LinearSegmentedColormap.from_list("imprint_seq", ["#4467A3", "#009E73"])

# Theme-aware seaborn style
sns.set_theme(
    style="white",
    rc={
        "figure.facecolor": PAGE_BG,
        "axes.facecolor": PAGE_BG,
        "axes.edgecolor": INK_SOFT,
        "axes.labelcolor": INK,
        "text.color": INK,
        "xtick.color": INK_SOFT,
        "ytick.color": INK_SOFT,
    },
)

# Data — 8 cohorts x 8 periods (triangular shape)
np.random.seed(42)

cohort_labels = ["Jan 2024", "Feb 2024", "Mar 2024", "Apr 2024", "May 2024", "Jun 2024", "Jul 2024", "Aug 2024"]
n_cohorts = len(cohort_labels)
n_periods = n_cohorts
cohort_sizes = np.random.randint(800, 2800, size=n_cohorts)

# Deliberately varied decay rates for distinct cross-cohort comparison
base_decays = [0.88, 0.74, 0.82, 0.67, 0.79, 0.86, 0.71, 0.90]
retention_data = np.full((n_cohorts, n_periods), np.nan)
for i in range(n_cohorts):
    max_periods = n_periods - i
    retention_data[i, 0] = 100.0
    for j in range(1, max_periods):
        prev = retention_data[i, j - 1]
        noise = np.random.uniform(-0.02, 0.02)
        decay = min(base_decays[i] + noise, 0.98)
        retention_data[i, j] = round(prev * decay, 1)

period_labels = [f"Month {i}" for i in range(n_periods)]
df_heatmap = pd.DataFrame(retention_data, index=cohort_labels, columns=period_labels)

# Plot — landscape canvas (3200 x 1800 px); wider cells accommodate annotations
fig, ax = plt.subplots(figsize=(8, 4.5), dpi=400)
fig.set_facecolor(PAGE_BG)
ax.set_facecolor(PAGE_BG)

mask = df_heatmap.isna()
annot_strings = df_heatmap.map(lambda v: f"{v:.0f}%" if not np.isnan(v) else "")

sns.heatmap(
    df_heatmap,
    mask=mask,
    annot=annot_strings,
    fmt="",
    cmap=imprint_seq,
    vmin=0,
    vmax=100,
    linewidths=2.5,
    linecolor=PAGE_BG,
    ax=ax,
    annot_kws={"fontsize": 12, "fontweight": "bold", "color": "#F0EFE8"},
    cbar_kws={"label": "Retention %", "shrink": 0.7, "aspect": 20, "pad": 0.02},
    square=False,
)

# Style
y_labels = [f"{label}  (n={size:,})" for label, size in zip(cohort_labels, cohort_sizes, strict=True)]
ax.set_yticklabels(y_labels, rotation=0, fontsize=9)
ax.set_xticklabels(period_labels, rotation=0, fontsize=9)
ax.set_xlabel("Periods Since Signup", fontsize=10, labelpad=10)
ax.set_ylabel("Signup Cohort", fontsize=10, labelpad=10)

title = "heatmap-cohort-retention · python · seaborn · anyplot.ai"
ax.set_title(title, fontsize=12, fontweight="medium", pad=14)

# Colorbar styling
cbar = ax.collections[0].colorbar
cbar.ax.tick_params(labelsize=8, colors=INK_SOFT)
cbar.set_label("Retention %", fontsize=9, labelpad=8, color=INK)
cbar.outline.set_visible(False)

# Remove all spines; hide tick marks
sns.despine(ax=ax, top=True, right=True, bottom=True, left=True)
ax.tick_params(axis="both", length=0)

# Explicit layout control — no bbox_inches="tight" (causes canvas drift per seaborn.md)
fig.subplots_adjust(left=0.20, right=0.89, top=0.91, bottom=0.14)

# Save
plt.savefig(f"plot-{THEME}.png", dpi=400, facecolor=PAGE_BG)
plt.close()
