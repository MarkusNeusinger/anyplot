"""anyplot.ai
violin-split: Split Violin Plot
Library: matplotlib 3.10.9 | Python 3.13.13
Quality: 88/100 | Updated: 2026-05-08
"""

import os

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.patches import Patch
from scipy.stats import gaussian_kde


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Imprint palette: all eight positions, one per split group in order
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

# Constants
HALF_WIDTH = 0.42  # widest half violin, in x-axis units (a full violin stays inside its 1-unit slot)

# Columns: set these to your table's column names
SCHOOL_LEVEL = "School level"  # role: category
TEST_SCORE = "Test score (points)"  # role: value
STUDY_GROUP = "Study group"  # role: split_group

# Data: replace this block with your own table, for example df = pd.read_csv("scores.csv")
np.random.seed(42)
levels = ["Elementary", "Middle School", "High School", "College"]
level_params = {
    "Elementary": {"Control": (72, 12), "Treatment": (76, 11)},
    "Middle School": {"Control": (68, 14), "Treatment": (73, 13)},
    "High School": {"Control": (65, 16), "Treatment": (71, 14)},
    "College": {"Control": (70, 11), "Treatment": (75, 10)},
}
n_per_group = 180
rows = []
for level in levels:
    for group, (mean, std) in level_params[level].items():
        scores = np.clip(np.random.normal(mean, std, n_per_group), 20, 100)
        rows.extend({SCHOOL_LEVEL: level, TEST_SCORE: s, STUDY_GROUP: group} for s in scores)
df = pd.DataFrame(rows)

# Plot: reads only df and the constants above
df = df.dropna(subset=[SCHOOL_LEVEL, TEST_SCORE, STUDY_GROUP])  # a missing value is skipped, never drawn as zero
categories = list(df[SCHOOL_LEVEL].unique())
groups = list(df[STUDY_GROUP].unique())
colors = dict(zip(groups, IMPRINT_PALETTE, strict=False))
sides = {group: (-1 if i % 2 == 0 else 1) for i, group in enumerate(groups)}  # first group left, second right

# One KDE per half, evaluated only across its own data range so tails stop at the data
densities = {}
for (level, group), values in df.groupby([SCHOOL_LEVEL, STUDY_GROUP], sort=False)[TEST_SCORE]:
    grid = np.linspace(values.min(), values.max(), 200)
    densities[(level, group)] = (grid, gaussian_kde(values)(grid))
peak = max(dens.max() for _, dens in densities.values())  # shared scale: widths are comparable across halves

fig, ax = plt.subplots(figsize=(8, 4.5), dpi=400, facecolor=PAGE_BG)
ax.set_facecolor(PAGE_BG)

for i, level in enumerate(categories):
    for group in groups:
        grid, dens = densities[(level, group)]
        side = sides[group]
        edge = i + side * dens / peak * HALF_WIDTH
        ax.fill_betweenx(grid, i, edge, facecolor=colors[group], edgecolor=INK_SOFT, linewidth=0.8, alpha=0.85)

        # Quartile markers on the half they describe: median long and bold, quartiles short
        q1, med, q3 = np.percentile(
            df[(df[SCHOOL_LEVEL] == level) & (df[STUDY_GROUP] == group)][TEST_SCORE], [25, 50, 75]
        )
        ax.plot([i, i + side * 0.30], [med, med], color=INK, linewidth=2.4, solid_capstyle="butt", zorder=3)
        for q in (q1, q3):
            ax.plot([i, i + side * 0.17], [q, q], color=INK, linewidth=1.2, solid_capstyle="butt", zorder=3)

    ax.axvline(i, color=INK_SOFT, linewidth=0.6, alpha=0.5, zorder=2)

title = "violin-split · python · matplotlib · anyplot.ai"
ax.set_title(title, fontsize=12, fontweight="medium", color=INK)
ax.set_xticks(range(len(categories)), categories)
ax.set_xlabel(SCHOOL_LEVEL, fontsize=10, color=INK)
ax.set_ylabel(TEST_SCORE, fontsize=10, color=INK)
ax.set_xlim(-0.6, len(categories) - 0.4)
ax.tick_params(axis="both", labelsize=8, colors=INK_SOFT, labelcolor=INK_SOFT)

for s in ("top", "right"):
    ax.spines[s].set_visible(False)
for s in ("left", "bottom"):
    ax.spines[s].set_color(INK_SOFT)

ax.yaxis.grid(True, alpha=0.15, linewidth=0.8, color=INK)
ax.set_axisbelow(True)

handles = [Patch(facecolor=colors[g], edgecolor=INK_SOFT, alpha=0.85, label=g) for g in groups]
leg = ax.legend(handles=handles, title=STUDY_GROUP, fontsize=8, title_fontsize=8, loc="lower left")
leg.get_frame().set_facecolor(ELEVATED_BG)
leg.get_frame().set_edgecolor(INK_SOFT)
leg.get_title().set_color(INK)
plt.setp(leg.get_texts(), color=INK_SOFT)

fig.subplots_adjust(left=0.08, right=0.97, top=0.92, bottom=0.12)
plt.savefig(f"plot-{THEME}.png", dpi=400, facecolor=PAGE_BG)
