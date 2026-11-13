"""anyplot.ai
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

# Imprint palette: positive SHAP uses position 5 (red), negative uses position 3 (blue)
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]
COLOR_POS = IMPRINT_PALETTE[4]  # raises the prediction
COLOR_NEG = IMPRINT_PALETTE[2]  # lowers the prediction

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

# Columns: set these to your table's column names
FEATURE = "Feature"  # role: feature
SHAP = "SHAP value"  # role: shap_value
BASE = "Base value (default probability)"  # role: base_value

# Data: replace this block with your own table, for example df = pd.read_csv("shap.csv")
# Credit scoring model predicting loan default probability for a single applicant.
df = pd.DataFrame(
    {
        FEATURE: [
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
        ],
        SHAP: [0.24, -0.18, 0.16, 0.11, -0.10, -0.07, 0.06, -0.05, -0.04, 0.03],
        BASE: 0.32,
    }
)

# Plot
# Largest |SHAP| at the top; the chain is built from the smallest feature upward
table = df.reindex(df[SHAP].abs().sort_values(ascending=False, kind="stable").index)
table = table.iloc[::-1].reset_index(drop=True)
n = len(table)
base_value = table[BASE].iloc[0]
shap_btt = table[SHAP].to_numpy()
running = np.concatenate([[base_value], base_value + np.nancumsum(shap_btt)])
starts_btt, ends_btt = running[:-1], running[1:]
final_value = running[-1]

bar_lefts = np.minimum(starts_btt, ends_btt)
bar_widths = np.abs(shap_btt)
bar_colors = [COLOR_POS if v >= 0 else COLOR_NEG for v in shap_btt]
y_pos = np.arange(n)
dominant = int(np.nanargmax(bar_widths))

fig, ax = plt.subplots(figsize=(8, 4.5), dpi=400, facecolor=PAGE_BG)
ax.set_facecolor(PAGE_BG)

# Waterfall bars; the dominant feature gets a thicker edge as focal emphasis
for i, (yi, left, width, color) in enumerate(zip(y_pos, bar_lefts, bar_widths, bar_colors, strict=True)):
    ax.barh(
        yi,
        width,
        left=left,
        color=color,
        height=0.55,
        zorder=3,
        edgecolor=INK_SOFT if i == dominant else PAGE_BG,
        linewidth=0.75 if i == dominant else 0.25,
    )

# Dotted connectors at the cumulative junctions between adjacent bars
for j in range(n - 1):
    cx = ends_btt[j]
    ax.plot([cx, cx], [j + 0.30, j + 0.70], color=INK_SOFT, linewidth=0.5, linestyle=":", zorder=2, alpha=0.65)

# Connector dots (seaborn scatterplot) mark the running total at each junction
connector_df = pd.DataFrame({"running": ends_btt[:-1], "position": np.arange(n - 1) + 0.5})
sns.scatterplot(data=connector_df, x="running", y="position", ax=ax, color=INK_SOFT, s=12, zorder=5, alpha=0.75)
ax.set_ylabel("")

# SHAP value labels beside bars
for yi, left, width, shap in zip(y_pos, bar_lefts, bar_widths, shap_btt, strict=True):
    if shap >= 0:
        ax.text(
            left + width,
            yi,
            f"  +{shap:.2f}",
            ha="left",
            va="center",
            color=COLOR_POS,
            fontsize=8,
            fontweight="bold",
            zorder=4,
        )
    else:
        ax.text(
            left, yi, f"{shap:.2f}  ", ha="right", va="center", color=COLOR_NEG, fontsize=8, fontweight="bold", zorder=4
        )

# Reference lines for the base value and the final prediction
ax.axvline(base_value, color=INK_SOFT, linewidth=0.75, linestyle="--", zorder=1, alpha=0.85)
ax.axvline(final_value, color=INK, linewidth=1.0, linestyle="-", zorder=1, alpha=0.90)
ax.text(base_value, -0.75, f"E[f(x)] = {base_value:.2f}", ha="center", va="center", fontsize=8, color=INK_SOFT)
ax.text(
    final_value,
    n - 0.5,
    f"  f(x) = {final_value:.2f}",
    ha="left",
    va="center",
    fontsize=8,
    color=INK,
    fontweight="bold",
)

# Axes: the dominant feature's label is bold
ax.set_yticks(y_pos)
ax.set_yticklabels(table[FEATURE], fontsize=8)
ax.get_yticklabels()[dominant].set_fontweight("bold")
ax.tick_params(axis="y", length=0)
ax.tick_params(axis="x", labelsize=8, colors=INK_SOFT)
ax.set_xlabel("Model Output (Default Probability)", fontsize=10, color=INK)

ax.xaxis.grid(True, alpha=0.10, linewidth=0.4, color=INK, zorder=0)
ax.set_axisbelow(True)

sns.despine(ax=ax, left=True, top=True, right=True)
ax.spines["bottom"].set_color(INK_SOFT)

ax.legend(
    handles=[
        mpatches.Patch(color=COLOR_POS, label="Positive SHAP  (↑ prediction)"),
        mpatches.Patch(color=COLOR_NEG, label="Negative SHAP  (↓ prediction)"),
    ],
    loc="lower right",
    fontsize=8,
    framealpha=0.9,
    facecolor=ELEVATED_BG,
    edgecolor=INK_SOFT,
)

x_all = running
ax.set_xlim(np.nanmin(x_all) - 0.06, np.nanmax(x_all) + 0.16)
ax.set_ylim(-1.0, n)

title = "Credit Default Prediction · shap-waterfall · python · seaborn · anyplot.ai"
title_fontsize = round(12 * (67 / len(title) if len(title) > 67 else 1.0))
ax.set_title(title, fontsize=title_fontsize, fontweight="medium", color=INK, pad=8)

fig.subplots_adjust(left=0.17, right=0.97, top=0.92, bottom=0.14)
plt.savefig(f"plot-{THEME}.png", dpi=400, facecolor=PAGE_BG)
