"""anyplot.ai
cat-box-strip: Box Plot with Strip Overlay
Library: matplotlib 3.10.9 | Python 3.13.13
Quality: pending | Updated: 2026-05-13
"""

import os

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Imprint palette: all eight positions, canonical order
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]
BRAND = IMPRINT_PALETTE[0]

# Constants
MEDIAN_COLOR = "#AE3030"  # Imprint position 5, a red accent that separates the median from the green boxes
JITTER = 0.08  # standard deviation of the sideways jitter, in category-width units

# Columns: set these to your table's column names
GROUP = "Treatment group"  # role: category
RESPONSE = "Response value (score)"  # role: value

# Data: replace this block with your own table, for example df = pd.read_csv("responses.csv")
np.random.seed(42)
control = np.random.normal(50, 8, 35)
treatment_a = np.random.normal(65, 12, 40)  # higher mean, more spread
treatment_b = np.concatenate([np.random.normal(45, 5, 27), np.array([15, 80, 82])])  # tight core with outliers
treatment_c = np.random.normal(55, 6, 45)
df = pd.DataFrame(
    {
        GROUP: ["Control"] * 35 + ["Treatment A"] * 40 + ["Treatment B"] * 30 + ["Treatment C"] * 45,
        RESPONSE: np.concatenate([control, treatment_a, treatment_b, treatment_c]),
    }
)

# Plot: reads only df and the constants above
groups = list(df[GROUP].drop_duplicates())
positions = np.arange(len(groups)) + 1
values = [df.loc[df[GROUP] == g, RESPONSE].dropna().to_numpy() for g in groups]

fig, ax = plt.subplots(figsize=(8, 4.5), dpi=400, facecolor=PAGE_BG)
ax.set_facecolor(PAGE_BG)

ax.boxplot(
    values,
    positions=positions,
    tick_labels=groups,
    widths=0.5,
    patch_artist=True,
    boxprops={"facecolor": BRAND, "alpha": 0.4, "linewidth": 1.2, "edgecolor": INK_SOFT},
    medianprops={"color": MEDIAN_COLOR, "linewidth": 2},
    whiskerprops={"color": INK_SOFT, "linewidth": 1.2},
    capprops={"color": INK_SOFT, "linewidth": 1.2},
    flierprops={
        "marker": "o",
        "markerfacecolor": BRAND,
        "markersize": 5,
        "alpha": 0.7,
        "markeredgecolor": INK_SOFT,
        "markeredgewidth": 0.5,
    },
)

# Strip overlay: every observation at its value, jittered sideways only
for pos, y in zip(positions, values, strict=False):
    x = np.random.normal(pos, JITTER, len(y))
    ax.scatter(x, y, s=22, alpha=0.6, color=BRAND, edgecolor=PAGE_BG, linewidth=0.5, zorder=3)

# Style
ax.set_title("cat-box-strip · python · matplotlib · anyplot.ai", fontsize=12, fontweight="medium", color=INK)
ax.set_xlabel(GROUP, fontsize=10, color=INK)
ax.set_ylabel(RESPONSE, fontsize=10, color=INK)
ax.tick_params(axis="both", labelsize=8, colors=INK_SOFT, labelcolor=INK_SOFT)

low, high = df[RESPONSE].min(), df[RESPONSE].max()
pad = (high - low) * 0.06
ax.set_ylim(low - pad, high + pad)

for side in ("top", "right"):
    ax.spines[side].set_visible(False)
for side in ("left", "bottom"):
    ax.spines[side].set_color(INK_SOFT)

ax.yaxis.grid(True, alpha=0.15, linewidth=0.8, color=INK)
ax.set_axisbelow(True)

plt.tight_layout()
plt.savefig(f"plot-{THEME}.png", dpi=400, facecolor=PAGE_BG)
