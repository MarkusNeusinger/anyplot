"""anyplot.ai
bar-feature-importance: Feature Importance Bar Chart
Library: seaborn 0.13.2 | Python 3.13.13
Quality: pending | Updated: 2026-05-10
"""

import os

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
from matplotlib.colors import LinearSegmentedColormap, Normalize


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Imprint palette: all eight positions; the gradient runs between the first and third
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]
imprint_seq = LinearSegmentedColormap.from_list("imprint_seq", [IMPRINT_PALETTE[0], IMPRINT_PALETTE[2]])

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

# Columns: set these to your table's column names
FEATURE = "Feature"  # role: feature
IMPORTANCE = "Feature Importance"  # role: importance
STD = "Std"  # role: std

# Data: simulated Random Forest importances for a credit-default model; replace with e.g. pd.read_csv("importances.csv")
np.random.seed(42)
features = [
    "Annual Income",
    "Credit Score",
    "Employment Years",
    "Debt-to-Income Ratio",
    "Age",
    "Number of Accounts",
    "Loan Amount",
    "Payment History",
    "Credit Utilization",
    "Home Ownership",
    "Education Level",
    "Marital Status",
    "Monthly Expenses",
    "Savings Balance",
    "Previous Defaults",
]
raw_importance = np.array([0.18, 0.15, 0.12, 0.11, 0.09, 0.08, 0.07, 0.06, 0.05, 0.03, 0.02, 0.015, 0.01, 0.008, 0.007])
df = pd.DataFrame(
    {
        FEATURE: features,
        IMPORTANCE: raw_importance / raw_importance.sum(),
        STD: np.random.uniform(0.005, 0.025, len(features)),
    }
)

# Plot: reads only df and the constants above
ranked = df.sort_values(IMPORTANCE, ascending=False).reset_index(drop=True)
norm = Normalize(vmin=ranked[IMPORTANCE].min(), vmax=ranked[IMPORTANCE].max())
bar_colors = {name: imprint_seq(norm(value)) for name, value in zip(ranked[FEATURE], ranked[IMPORTANCE], strict=True)}
spread = np.fmax(ranked[STD], 0)
bar_end = ranked[IMPORTANCE] + spread
x_max = bar_end.max() * 1.15

fig, ax = plt.subplots(figsize=(8, 4.5), dpi=400)
sns.barplot(
    data=ranked,
    x=IMPORTANCE,
    y=FEATURE,
    hue=FEATURE,
    palette=bar_colors,
    legend=False,
    ax=ax,
    edgecolor=PAGE_BG,
    linewidth=0.6,
)

# Ensemble variability as error bars centered on each bar end
ax.errorbar(
    ranked[IMPORTANCE],
    np.arange(len(ranked)),
    xerr=ranked[STD],
    fmt="none",
    ecolor=INK,
    capsize=2.5,
    capthick=1,
    linewidth=1,
)

# Importance values just past the end of each error bar
for i, (value, end) in enumerate(zip(ranked[IMPORTANCE], bar_end, strict=True)):
    ax.text(end + x_max * 0.01, i, f"{value:.3f}", va="center", ha="left", fontsize=7, color=INK_SOFT)

# Style
title = "bar-feature-importance · python · seaborn · anyplot.ai"
ax.set_title(title, fontsize=round(12 * (67 / len(title) if len(title) > 67 else 1.0)), pad=10)
ax.set_xlabel(IMPORTANCE, fontsize=10)
ax.set_ylabel(FEATURE, fontsize=10)
ax.tick_params(axis="both", labelsize=8)
ax.set_xlim(0, x_max)
ax.xaxis.grid(True, linewidth=0.8)
ax.set_axisbelow(True)
sns.despine(ax=ax)

fig.subplots_adjust(left=0.2, right=0.97, top=0.9, bottom=0.13)
plt.savefig(f"plot-{THEME}.png", dpi=400, facecolor=PAGE_BG)
