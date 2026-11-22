""" anyplot.ai
violin-grouped-swarm: Grouped Violin Plot with Swarm Overlay
Library: matplotlib 3.11.2 | Python 3.14.10
Quality: 83/100 | Updated: 2026-11-22
"""

import os

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Imprint palette: all eight positions, one per group in order
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

# Columns: set these to your table's column names
COMPLEXITY = "Task complexity"  # role: category
EXPERTISE = "Expertise"  # role: group
RESPONSE = "Response time (seconds)"  # role: value

# Data: replace this block with your own table, for example df = pd.read_csv("response_times.csv")
np.random.seed(42)
tasks = ["Simple", "Moderate", "Complex"]
levels = ["Novice", "Expert"]
loc_scale = {
    ("Simple", "Novice"): (1.2, 0.3),
    ("Moderate", "Novice"): (2.5, 0.5),
    ("Complex", "Novice"): (4.5, 0.8),
    ("Simple", "Expert"): (0.8, 0.2),
    ("Moderate", "Expert"): (1.5, 0.3),
    ("Complex", "Expert"): (2.5, 0.5),
}
rows = []
for task in tasks:
    for level in levels:
        loc, scale = loc_scale[(task, level)]
        draws = np.maximum(np.random.normal(loc=loc, scale=scale, size=40), 0.1)
        rows.append(pd.DataFrame({COMPLEXITY: task, EXPERTISE: level, RESPONSE: draws}))
df = pd.concat(rows, ignore_index=True)

# Plot: reads only df and the constants above
categories = list(df[COMPLEXITY].unique())
groups = list(df[EXPERTISE].unique())
width = 0.7 / len(groups)
step = 0.015 * 0.5 * width / 0.35  # sideways swarm step, scaled to the violin slot


def group_offset(j):
    return (j - (len(groups) - 1) / 2) * width


fig, ax = plt.subplots(figsize=(8, 4.5), dpi=400, facecolor=PAGE_BG)
ax.set_facecolor(PAGE_BG)

# Translucent violins with median lines, one dodged set per group
for j, grp in enumerate(groups):
    sub = df[df[EXPERTISE] == grp]
    pos, series = [], []
    for i, cat in enumerate(categories):
        vals = sub.loc[sub[COMPLEXITY] == cat, RESPONSE].dropna().to_numpy()
        if len(vals) > 1:
            pos.append(i + group_offset(j))
            series.append(vals)
    parts = ax.violinplot(
        series, positions=pos, widths=width * 0.9, showmeans=False, showmedians=True, showextrema=False
    )
    for body in parts["bodies"]:
        body.set_facecolor(IMPRINT_PALETTE[j])
        body.set_edgecolor(INK_SOFT)
        body.set_alpha(0.5)
        body.set_linewidth(0.8)
    parts["cmedians"].set_color(INK)
    parts["cmedians"].set_linewidth(1.2)

# Swarm points: sideways offsets only, every point stays at its value
for i, cat in enumerate(categories):
    for j, grp in enumerate(groups):
        vals = df.loc[(df[COMPLEXITY] == cat) & (df[EXPERTISE] == grp), RESPONSE].dropna().to_numpy()
        if len(vals) == 0:
            continue
        bin_width = (vals.max() - vals.min()) / 20
        jitter = np.zeros(len(vals))
        for idx in np.argsort(vals):
            nearby = np.abs(vals - vals[idx]) < bin_width
            count = np.sum(nearby & (np.arange(len(vals)) <= idx))
            if count % 2 == 0:
                jitter[idx] = (count // 2) * step
            else:
                jitter[idx] = -((count + 1) // 2) * step
        ax.scatter(
            i + group_offset(j) + jitter,
            vals,
            s=14,
            color=IMPRINT_PALETTE[j],
            edgecolors=PAGE_BG,
            linewidths=0.3,
            alpha=0.9,
            zorder=3,
        )

# Style
ax.set_xticks(range(len(categories)), categories)
ax.set_xlabel(COMPLEXITY, fontsize=10, color=INK)
ax.set_ylabel(RESPONSE, fontsize=10, color=INK)
ax.set_title("violin-grouped-swarm · python · matplotlib · anyplot.ai", fontsize=12, fontweight="medium", color=INK)
ax.tick_params(axis="both", labelsize=8, colors=INK_SOFT, labelcolor=INK_SOFT)
for s in ("left", "bottom"):
    ax.spines[s].set_color(INK_SOFT)
ax.spines["top"].set_visible(False)
ax.spines["right"].set_visible(False)
ax.yaxis.grid(True, alpha=0.15, linewidth=0.8, color=INK)
ax.set_axisbelow(True)

legend_handles = [
    plt.Rectangle((0, 0), 1, 1, facecolor=IMPRINT_PALETTE[j], edgecolor=INK_SOFT, alpha=0.5, label=grp)
    for j, grp in enumerate(groups)
]
leg = ax.legend(handles=legend_handles, fontsize=8, title=EXPERTISE, title_fontsize=8, loc="upper left")
leg.get_frame().set_facecolor(ELEVATED_BG)
leg.get_frame().set_edgecolor(INK_SOFT)
plt.setp(leg.get_texts(), color=INK_SOFT)
plt.setp(leg.get_title(), color=INK)

fig.tight_layout()
plt.savefig(f"plot-{THEME}.png", dpi=400, facecolor=PAGE_BG)
