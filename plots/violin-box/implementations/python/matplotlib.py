"""anyplot.ai
violin-box: Violin Plot with Embedded Box Plot
Library: matplotlib 3.10.9 | Python 3.13.13
Quality: pending | Updated: 2026-05-12
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

# Imprint palette: a single-series violin plot uses position 1 alone
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]
BRAND = IMPRINT_PALETTE[0]

# Columns: set these to your table's column names
GROUP = "Experimental group"  # role: group
VALUE = "Response value (units)"  # role: value

# Data: replace this block with your own table, for example df = pd.read_csv("responses.csv")
np.random.seed(42)
group_a = np.random.normal(65, 8, 80)  # symmetric
group_b = np.concatenate([np.random.normal(45, 5, 40), np.random.normal(60, 5, 40)])  # bimodal
group_c = np.random.exponential(10, 80) + 30  # right-skewed
group_d = np.random.normal(55, 12, 80)  # wide spread
group_d = np.append(group_d, [95, 100, 15, 10])  # plus outliers
samples = {"Control": group_a, "Treatment A": group_b, "Treatment B": group_c, "Treatment C": group_d}
df = pd.DataFrame(
    {GROUP: np.repeat(list(samples), [len(v) for v in samples.values()]), VALUE: np.concatenate(list(samples.values()))}
)

# Plot: reads only df and the constants above
groups = df[GROUP].unique()
data = [df.loc[df[GROUP] == g, VALUE].dropna().to_numpy() for g in groups]
positions = np.arange(1, len(groups) + 1)

fig, ax = plt.subplots(figsize=(8, 4.5), dpi=400, facecolor=PAGE_BG)
ax.set_facecolor(PAGE_BG)

violin_parts = ax.violinplot(data, positions=positions, showmeans=False, showmedians=False, showextrema=False)
for body in violin_parts["bodies"]:
    body.set_facecolor(BRAND)
    body.set_edgecolor(INK_SOFT)
    body.set_alpha(0.6)
    body.set_linewidth(1.0)

# Box plot centered on each violin's axis
box_parts = ax.boxplot(
    data, positions=positions, widths=0.15, patch_artist=True, tick_labels=list(groups), showfliers=True, zorder=3
)
for patch in box_parts["boxes"]:
    patch.set_facecolor(INK_SOFT)
    patch.set_edgecolor(INK)
    patch.set_linewidth(1.0)
    patch.set_alpha(0.8)
for part in ("whiskers", "caps"):
    for line in box_parts[part]:
        line.set_color(INK)
        line.set_linewidth(1.0)
for median in box_parts["medians"]:
    median.set_color(INK)
    median.set_linewidth(1.6)
for flier in box_parts["fliers"]:
    flier.set(marker="o", markerfacecolor=BRAND, markeredgecolor=INK, markersize=3.5, alpha=0.7)

# Style
ax.set_xlabel(GROUP, fontsize=10, color=INK)
ax.set_ylabel(VALUE, fontsize=10, color=INK)
ax.set_title("violin-box · python · matplotlib · anyplot.ai", fontsize=12, fontweight="medium", color=INK)
ax.tick_params(axis="both", labelsize=8, colors=INK_SOFT)
ax.spines["top"].set_visible(False)
ax.spines["right"].set_visible(False)
for s in ("left", "bottom"):
    ax.spines[s].set_color(INK_SOFT)
    ax.spines[s].set_linewidth(0.8)
ax.yaxis.grid(True, alpha=0.15, linewidth=0.6, color=INK)

# Shared value axis fitted to the data, not forced to zero
lo, hi = df[VALUE].min(), df[VALUE].max()
pad = (hi - lo) * 0.08
ax.set_ylim(lo - pad, hi + pad)

plt.tight_layout()
plt.savefig(f"plot-{THEME}.png", dpi=400, facecolor=PAGE_BG)
