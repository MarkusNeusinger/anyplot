"""anyplot.ai
bar-permutation-importance: Permutation Feature Importance Plot
Library: seaborn 0.13.2 | Python 3.13.13
Quality: pending | Updated: 2026-05-17
"""

import os

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
from matplotlib.colors import LinearSegmentedColormap
from sklearn.datasets import load_breast_cancer
from sklearn.ensemble import RandomForestClassifier
from sklearn.inspection import permutation_importance


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Imprint palette: all eight positions, canonical order
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

# Imprint sequential colormap (single polarity), low importance -> high importance
imprint_seq = LinearSegmentedColormap.from_list("imprint_seq", [IMPRINT_PALETTE[2], IMPRINT_PALETTE[0]])

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
    },
)

# Columns: set these to your table's column names
FEATURE = "Feature"  # role: feature
IMPORTANCE = "Mean importance (decrease in accuracy)"  # role: importance_mean
IMPORTANCE_STD = "Std of importance"  # role: importance_std

# Data: replace this block with your own table, for example df = pd.read_csv("importance.csv")
data = load_breast_cancer()
clf = RandomForestClassifier(n_estimators=100, random_state=42).fit(data.data, data.target)
perm = permutation_importance(clf, data.data, data.target, n_repeats=10, random_state=42)
df = pd.DataFrame(
    {FEATURE: data.feature_names, IMPORTANCE: perm.importances_mean, IMPORTANCE_STD: perm.importances_std}
)

# Plot: reads only df and the constants above
df = df.sort_values(IMPORTANCE, ascending=False).reset_index(drop=True)
lo, hi = df[IMPORTANCE].min(), df[IMPORTANCE].max()
span = (hi - lo) if hi > lo else 1.0
bar_colors = [imprint_seq((v - lo) / span) for v in df[IMPORTANCE]]

fig, ax = plt.subplots(figsize=(8, 4.5), dpi=400, facecolor=PAGE_BG)
ax.set_facecolor(PAGE_BG)

sns.barplot(
    data=df,
    x=IMPORTANCE,
    y=FEATURE,
    hue=FEATURE,
    palette=bar_colors,
    order=df[FEATURE],
    legend=False,
    ax=ax,
    width=0.75,
    linewidth=0,
)

# Horizontal error bars: variability across permutation repeats
ax.errorbar(
    df[IMPORTANCE],
    np.arange(len(df)),
    xerr=df[IMPORTANCE_STD],
    fmt="none",
    ecolor=INK,
    elinewidth=0.8,
    capsize=2,
    capthick=0.8,
)

# Reference line at zero
ax.axvline(0, color=INK, linewidth=1.0, alpha=0.8)

# Style
ax.set_title("bar-permutation-importance · python · seaborn · anyplot.ai", fontsize=12, fontweight="medium")
ax.set_xlabel(IMPORTANCE, fontsize=10)
ax.set_ylabel(FEATURE, fontsize=10)
ax.tick_params(axis="y", labelsize=6)
ax.tick_params(axis="x", labelsize=8)
ax.yaxis.grid(False)
ax.xaxis.grid(True, alpha=0.10, linewidth=0.5)
sns.despine(ax=ax)

fig.tight_layout()
plt.savefig(f"plot-{THEME}.png", dpi=400, facecolor=PAGE_BG)
