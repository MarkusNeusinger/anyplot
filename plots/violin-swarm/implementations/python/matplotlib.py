"""anyplot.ai
violin-swarm: Violin Plot with Overlaid Swarm Points
Library: matplotlib 3.10.9 | Python 3.13.13
Quality: pending | Updated: 2026-05-18
"""

import os

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy.stats import gaussian_kde


# Theme tokens (read from environment)
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Imprint palette: violin fill takes position 1, swarm points position 2
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

# Constants
VIOLIN_WIDTH = 0.5  # full width of the widest violin, in category units
SWARM_SHARE = 0.8  # share of the local violin half-width the swarm may use
SWARM_BINS = 18  # value bins used to stack swarm points sideways

# Columns: set these to your table's column names
CONDITION = "Experimental condition"  # role: category
REACTION = "Reaction time (ms)"  # role: value

# Data: replace this block with your own table, for example df = pd.read_csv("reactions.csv")
np.random.seed(42)
n_per_group = 50
samples = {
    "Control": np.random.normal(450, 60, n_per_group),
    "Treatment A": np.random.normal(380, 45, n_per_group),
    "Treatment B": np.random.normal(420, 80, n_per_group),
    "Treatment C": np.concatenate(
        [np.random.normal(350, 30, n_per_group // 2), np.random.normal(450, 30, n_per_group // 2)]
    ),
}
df = pd.DataFrame(
    {
        CONDITION: np.repeat(list(samples), [len(v) for v in samples.values()]),
        REACTION: np.concatenate(list(samples.values())),
    }
)

# Plot: reads only df and the constants above
groups = list(df[CONDITION].drop_duplicates())
values = [df.loc[df[CONDITION] == g, REACTION].dropna().to_numpy() for g in groups]
positions = np.arange(len(groups))

fig, ax = plt.subplots(figsize=(8, 4.5), dpi=400, facecolor=PAGE_BG)
ax.set_facecolor(PAGE_BG)

# Translucent violins
parts = ax.violinplot(
    values, positions=positions, widths=VIOLIN_WIDTH, showmeans=False, showmedians=False, showextrema=False
)
for body in parts["bodies"]:
    body.set_facecolor(IMPRINT_PALETTE[0])
    body.set_edgecolor(INK_SOFT)
    body.set_alpha(0.4)
    body.set_linewidth(1.0)

# Swarm: x offsets are layout only; each point stays at its value and inside the violin outline
for i, (pos, y) in enumerate(zip(positions, values, strict=False)):
    kde = gaussian_kde(y)
    grid = np.linspace(y.min(), y.max(), 200)
    peak = kde(grid).max()
    half = VIOLIN_WIDTH / 2 * kde(y) / peak * SWARM_SHARE
    edges = np.linspace(y.min(), y.max(), SWARM_BINS + 1)
    bin_id = np.clip(np.digitize(y, edges) - 1, 0, SWARM_BINS - 1)
    offset = np.zeros(len(y))
    for b in np.unique(bin_id):
        idx = np.where(bin_id == b)[0]
        idx = idx[np.argsort(y[idx])]
        k = len(idx)
        slots = (np.arange(k) + 0.5) / k * 2 - 1  # evenly spaced in -1..1
        slots = np.concatenate([slots[::2], slots[1::2]]) if k > 1 else slots
        offset[idx] = slots * half[idx]
    ax.scatter(
        pos + offset,
        y,
        s=22,
        alpha=0.9,
        color=IMPRINT_PALETTE[1],
        edgecolor=INK_SOFT,
        linewidth=0.4,
        zorder=3,
        label="Individual observations" if i == 0 else None,
    )
    ax.hlines(
        np.median(y), pos - 0.2, pos + 0.2, color=INK, linewidth=1.8, zorder=4, label="Median" if i == 0 else None
    )

# Style
title = "violin-swarm · python · matplotlib · anyplot.ai"
ax.set_title(title, fontsize=12, fontweight="medium", color=INK)
ax.set_xticks(positions, groups)
ax.set_xlabel(CONDITION, fontsize=10, color=INK)
ax.set_ylabel(REACTION, fontsize=10, color=INK)
ax.tick_params(axis="both", labelsize=8, colors=INK_SOFT, labelcolor=INK_SOFT)
ax.yaxis.grid(True, alpha=0.15, linewidth=0.8, color=INK)
ax.set_axisbelow(True)
ax.spines["top"].set_visible(False)
ax.spines["right"].set_visible(False)
for side in ("left", "bottom"):
    ax.spines[side].set_color(INK_SOFT)

lo, hi = df[REACTION].min(), df[REACTION].max()
pad = (hi - lo) * 0.08
ax.set_ylim(lo - pad, hi + pad)

leg = ax.legend(loc="upper right", fontsize=8, frameon=True)
leg.get_frame().set_facecolor(ELEVATED_BG)
leg.get_frame().set_edgecolor(INK_SOFT)
plt.setp(leg.get_texts(), color=INK_SOFT)

fig.subplots_adjust(left=0.09, right=0.97, top=0.92, bottom=0.12)
plt.savefig(f"plot-{THEME}.png", dpi=400, facecolor=PAGE_BG)
