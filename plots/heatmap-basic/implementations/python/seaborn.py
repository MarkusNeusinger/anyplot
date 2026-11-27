"""anyplot.ai
heatmap-basic: Basic Heatmap
Library: seaborn 0.13.2 | Python 3.13.13
Quality: pending | Updated: 2026-05-28
"""

import os

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
from matplotlib.colors import LinearSegmentedColormap, to_rgb


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Imprint palette: all eight positions in canonical order
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

# Imprint diverging field ramp (matte-red <-> page <-> blue); the midpoint is the page color
imprint_div = LinearSegmentedColormap.from_list("imprint_div", ["#AE3030", PAGE_BG, "#4467A3"])

# Constants
SCORE_MIN, SCORE_MAX, SCORE_CENTER = 0, 100, 50  # fixed domain of a performance score

# Columns: set these to your table's column names
MONTH = "Month"  # role: x
DEPARTMENT = "Department"  # role: y
SCORE = "Performance score"  # role: value

# Data: replace this block with your own table, for example df = pd.read_csv("scores.csv")
np.random.seed(42)
departments = ["Sales", "Marketing", "Engineering", "Support", "Finance", "HR", "Operations"]
months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]

values = np.random.randn(len(departments), len(months)) * 20 + 50
values[0, :6] += 20  # Sales surge first half
values[2, 6:] += 25  # Engineering ramp second half
values[4, :] = values[4, :] * 0.3 + 70  # Finance steady high
values[5, 3:9] -= 15  # HR mid-year dip
values[3, 10:] -= 22  # Support year-end slump
values = np.clip(values, 5, 95)

df = pd.DataFrame(
    {MONTH: np.tile(months, len(departments)), DEPARTMENT: np.repeat(departments, len(months)), SCORE: values.ravel()}
)

# Plot: reads only df and the constants above
table = df.pivot_table(index=DEPARTMENT, columns=MONTH, values=SCORE, sort=False)
table = table.loc[table.mean(axis=1).sort_values(ascending=False).index]  # rows by overall level

title = "heatmap-basic · python · seaborn · anyplot.ai"
title_fontsize = max(8, round(12 * min(1.0, 67 / len(title))))

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
    },
)

fig, ax = plt.subplots(figsize=(6, 6), dpi=400, facecolor=PAGE_BG)
sns.heatmap(
    table,
    ax=ax,
    annot=True,
    fmt=".0f",
    cmap=imprint_div,
    center=SCORE_CENTER,
    vmin=SCORE_MIN,
    vmax=SCORE_MAX,
    linewidths=1.0,
    linecolor=PAGE_BG,
    square=False,
    annot_kws={"fontsize": 9, "fontweight": "medium"},
    cbar_kws={"ticks": np.linspace(SCORE_MIN, SCORE_MAX, 5), "shrink": 0.8, "pad": 0.03},
)

# In-cell numbers switch with the darkness of their cell, so they stay legible in both themes
shown = table.to_numpy().ravel()
shown = shown[~np.isnan(shown)]  # masked (missing) cells carry no text
for text, value in zip(ax.texts, shown, strict=True):
    r, g, b = to_rgb(imprint_div((value - SCORE_MIN) / (SCORE_MAX - SCORE_MIN)))
    luminance = 0.2126 * r + 0.7152 * g + 0.0722 * b
    text.set_color("#1A1A17" if luminance > 0.4 else "#F0EFE8")

# Colorbar
cbar = ax.collections[0].colorbar
cbar.set_label(SCORE, fontsize=10, color=INK)
cbar.ax.tick_params(labelsize=8, colors=INK_SOFT)
cbar.outline.set_visible(False)

# Chrome
ax.set_xlabel(MONTH, fontsize=10, labelpad=8)
ax.set_ylabel(DEPARTMENT, fontsize=10, labelpad=8)
ax.tick_params(axis="both", labelsize=9, length=0)
ax.tick_params(axis="y", rotation=0)
for spine in ax.spines.values():
    spine.set_visible(False)
ax.set_title(title, fontsize=title_fontsize, fontweight="medium", color=INK, pad=12)

plt.tight_layout()
plt.savefig(f"plot-{THEME}.png", dpi=400, facecolor=PAGE_BG)
