""" anyplot.ai
shap-waterfall: SHAP Waterfall Plot for Feature Attribution
Library: seaborn 0.13.2 | Python 3.13.13
Quality: 84/100 | Created: 2026-05-07
"""

import os
import sys


# Prevent self-import: remove this script's directory from sys.path
_script_dir = os.path.dirname(os.path.abspath(__file__))
if _script_dir in sys.path:
    sys.path.remove(_script_dir)

import matplotlib.patches as mpatches
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
INK_MUTED = "#6B6A63" if THEME == "light" else "#A8A79F"

COLOR_POS = "#AE3030"  # imprint red — positive SHAP (raises prediction)
COLOR_NEG = "#4467A3"  # imprint blue — negative SHAP (lowers prediction)

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

# Data — credit scoring model predicting loan default probability (single applicant)
base_value = 0.32

feature_names = [
    "Late Payment Count",
    "Credit Score",
    "Debt-to-Income Ratio",
    "Loan Amount",
    "Monthly Income",
    "Employment Years",
    "Public Records",
    "Savings Balance",
    "Account Age",
    "Credit Lines",
]
# SHAP values sorted by absolute magnitude descending (index 0 = largest impact)
shap_values = np.array([0.24, -0.18, 0.16, 0.11, -0.10, -0.07, 0.06, -0.05, -0.04, 0.03])
final_value = base_value + shap_values.sum()

n = len(feature_names)

# Display: largest |SHAP| at top (y = n-1), smallest at bottom (y = 0)
# Cumulative flow builds bottom-to-top — smallest feature processed first from base_value
shap_btt = shap_values[::-1]
running = np.concatenate([[base_value], base_value + np.cumsum(shap_btt)])
starts_btt = running[:-1]
ends_btt = running[1:]
features_btt = feature_names[::-1]

bar_lefts = np.where(shap_btt >= 0, starts_btt, ends_btt)
bar_widths = np.abs(shap_btt)
bar_colors = [COLOR_POS if v >= 0 else COLOR_NEG for v in shap_btt]
y_pos = np.arange(n)

# Plot
fig, ax = plt.subplots(figsize=(16, 9), facecolor=PAGE_BG)
ax.set_facecolor(PAGE_BG)

# Waterfall bars — dominant feature (top bar, y=n-1) gets thicker edge for focal emphasis
for i, (yi, left, width, color) in enumerate(zip(y_pos, bar_lefts, bar_widths, bar_colors, strict=False)):
    is_dominant = i == n - 1
    ax.barh(
        yi,
        width,
        left=left,
        color=color,
        height=0.55,
        zorder=3,
        edgecolor=INK_SOFT if is_dominant else PAGE_BG,
        linewidth=1.5 if is_dominant else 0.5,
    )

# Vertical dotted connector lines at cumulative junctions between adjacent bars
for j in range(n - 1):
    cx = ends_btt[j]
    ax.plot([cx, cx], [j + 0.30, j + 0.70], color=INK_SOFT, linewidth=1.0, linestyle=":", zorder=2, alpha=0.65)

# Connector dots using seaborn scatterplot — mark the running cumulative total at each junction
connector_df = pd.DataFrame({"x": ends_btt[:-1], "y": np.arange(n - 1) + 0.5})
sns.scatterplot(data=connector_df, x="x", y="y", ax=ax, color=INK_SOFT, s=50, zorder=5, alpha=0.75)

# SHAP value labels beside bars
for yi, left, width, shap in zip(y_pos, bar_lefts, bar_widths, shap_btt, strict=False):
    label = f"+{shap:.2f}" if shap >= 0 else f"{shap:.2f}"
    if shap >= 0:
        ax.text(
            left + width,
            yi,
            f"  {label}",
            ha="left",
            va="center",
            color=COLOR_POS,
            fontsize=14,
            fontweight="bold",
            zorder=4,
        )
    else:
        ax.text(
            left, yi, f"{label}  ", ha="right", va="center", color=COLOR_NEG, fontsize=14, fontweight="bold", zorder=4
        )

# Reference lines
ax.axvline(base_value, color=INK_SOFT, linewidth=1.5, linestyle="--", zorder=1, alpha=0.85)
ax.axvline(final_value, color=INK, linewidth=2.0, linestyle="-", zorder=1, alpha=0.90)

# Annotations for reference lines — 15pt for adequate secondary text legibility
ax.text(base_value, -0.75, f"E[f(x)] = {base_value:.2f}", ha="center", va="center", fontsize=15, color=INK_SOFT)
ax.text(
    final_value,
    n - 0.5,
    f"f(x) = {final_value:.2f}",
    ha="center",
    va="center",
    fontsize=15,
    color=INK,
    fontweight="bold",
)

# Axes — dominant feature label is bold to create visual focal point
ax.set_yticks(y_pos)
ax.set_yticklabels(features_btt, fontsize=16)
for label_obj in ax.get_yticklabels():
    if label_obj.get_text() == "Late Payment Count":
        label_obj.set_fontweight("bold")

ax.tick_params(axis="y", length=0)
ax.tick_params(axis="x", labelsize=16, colors=INK_SOFT)
ax.set_xlabel("Model Output  (Default Probability)", fontsize=20, color=INK)

# Subtle x-axis grid
ax.xaxis.grid(True, alpha=0.10, linewidth=0.8, color=INK, zorder=0)
ax.set_axisbelow(True)

# Spine removal using seaborn's despine — idiomatic seaborn API
sns.despine(ax=ax, left=True, top=True, right=True)
ax.spines["bottom"].set_color(INK_SOFT)

# Legend
pos_patch = mpatches.Patch(color=COLOR_POS, label="Positive SHAP  (↑ prediction)")
neg_patch = mpatches.Patch(color=COLOR_NEG, label="Negative SHAP  (↓ prediction)")
ax.legend(
    handles=[pos_patch, neg_patch],
    loc="lower right",
    fontsize=16,
    framealpha=0.9,
    facecolor=ELEVATED_BG,
    edgecolor=INK_SOFT,
)

# Axis limits
x_all = np.concatenate([starts_btt, ends_btt])
ax.set_xlim(x_all.min() - 0.06, x_all.max() + 0.16)
ax.set_ylim(-1.0, n)

ax.set_title(
    "Credit Default Prediction · shap-waterfall · seaborn · anyplot.ai",
    fontsize=24,
    fontweight="medium",
    color=INK,
    pad=16,
)

plt.tight_layout()
plt.savefig(f"plot-{THEME}.png", dpi=300, bbox_inches="tight", facecolor=PAGE_BG)
