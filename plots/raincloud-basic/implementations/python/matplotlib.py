"""anyplot.ai
raincloud-basic: Basic Raincloud Plot
Library: matplotlib 3.10.9 | Python 3.13.13
Quality: pending | Updated: 2026-05-26
"""

import os

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy.stats import gaussian_kde


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Imprint palette: all eight positions, one per category in order
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

# Columns: set these to your table's column names
CONDITION = "Experimental Condition"  # role: category
REACTION_TIME = "Reaction Time (ms)"  # role: value

# Data: replace this block with your own table, for example df = pd.read_csv("reaction_times.csv")
np.random.seed(42)

# Control: roughly normal around 350 ms
control = np.random.normal(350, 50, 80)
# Treatment A: clearly bimodal, two response strategies
treatment_a = np.concatenate([np.random.normal(250, 25, 45), np.random.normal(340, 25, 35)])
# Treatment B: mostly central with a slow tail and a few outliers
treatment_b = np.concatenate([np.random.normal(300, 40, 60), np.random.normal(400, 25, 15), np.array([500, 520, 480])])

groups = {"Control": control, "Treatment A": treatment_a, "Treatment B": treatment_b}
df = pd.DataFrame(
    {
        CONDITION: np.repeat(list(groups), [len(v) for v in groups.values()]),
        REACTION_TIME: np.concatenate(list(groups.values())),
    }
)

# Plot: reads only df and the constants above
rng = np.random.default_rng(42)
values_all = df[REACTION_TIME]
span = values_all.max() - values_all.min()

# Raincloud layout: cloud above baseline, boxplot on baseline, rain below
cloud_offset = 0.05
cloud_height = 0.32
rain_offset = -0.22
box_width = 0.08
jitter_width = 0.07

fig, ax = plt.subplots(figsize=(8, 4.5), dpi=400, facecolor=PAGE_BG)
ax.set_facecolor(PAGE_BG)

categories = list(df[CONDITION].unique())
for i, (_, rows) in enumerate(df.groupby(CONDITION, sort=False)):
    pos = i + 1
    color = IMPRINT_PALETTE[i % len(IMPRINT_PALETTE)]
    d = rows[REACTION_TIME].dropna().to_numpy()

    # Cloud: half-violin via scipy KDE, Silverman's rule
    kde = gaussian_kde(d, bw_method="silverman")
    x_vals = np.linspace(d.min() - 0.09 * span, d.max() + 0.09 * span, 256)
    density = kde(x_vals)
    density_scaled = density / density.max() * cloud_height

    ax.fill_between(
        x_vals,
        pos + cloud_offset,
        pos + cloud_offset + density_scaled,
        color=color,
        alpha=0.75,
        edgecolor=color,
        linewidth=0.8,
        zorder=1,
    )

    # Boxplot: sits on the category baseline
    bp = ax.boxplot(
        [d], positions=[pos], widths=box_width, orientation="horizontal", patch_artist=True, showfliers=False, zorder=3
    )
    bp["boxes"][0].set_facecolor(ELEVATED_BG)
    bp["boxes"][0].set_edgecolor(INK_SOFT)
    bp["boxes"][0].set_linewidth(1.2)
    bp["medians"][0].set_color(INK)
    bp["medians"][0].set_linewidth(1.6)
    for whisker in bp["whiskers"]:
        whisker.set_color(INK_SOFT)
        whisker.set_linewidth(1.0)
    for cap in bp["caps"]:
        cap.set_color(INK_SOFT)
        cap.set_linewidth(1.0)

    # Rain: jittered points below the baseline
    jitter = rng.uniform(-jitter_width, jitter_width, len(d))
    ax.scatter(
        d,
        np.full(len(d), pos + rain_offset) + jitter,
        s=28,
        alpha=0.6,
        color=color,
        edgecolor=PAGE_BG,
        linewidth=0.4,
        zorder=2,
    )

# Axes & ticks
ax.set_yticks(range(1, len(categories) + 1))
ax.set_yticklabels(categories, fontsize=10, color=INK_SOFT)
ax.set_xlabel(REACTION_TIME, fontsize=10, color=INK)
ax.set_ylabel(CONDITION, fontsize=10, color=INK)

title = "raincloud-basic · python · matplotlib · anyplot.ai"
ax.set_title(title, fontsize=12, fontweight="medium", color=INK, pad=10)

ax.tick_params(axis="both", labelsize=8, colors=INK_SOFT, labelcolor=INK_SOFT)

# Range with breathing room
ax.set_xlim(values_all.min() - 0.12 * span, values_all.max() + 0.12 * span)
ax.set_ylim(0.45, len(categories) + 0.55)

# Subtle x-axis grid only
ax.xaxis.grid(True, alpha=0.15, color=INK, linewidth=0.8)
ax.set_axisbelow(True)

# L-frame: keep left + bottom
ax.spines["top"].set_visible(False)
ax.spines["right"].set_visible(False)
ax.spines["left"].set_color(INK_SOFT)
ax.spines["bottom"].set_color(INK_SOFT)
ax.spines["left"].set_linewidth(0.8)
ax.spines["bottom"].set_linewidth(0.8)

fig.subplots_adjust(left=0.12, right=0.97, top=0.90, bottom=0.13)
plt.savefig(f"plot-{THEME}.png", dpi=400, facecolor=PAGE_BG)
