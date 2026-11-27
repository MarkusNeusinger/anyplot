"""anyplot.ai
line-impurity-comparison: Gini Impurity vs Entropy Comparison
Library: seaborn 0.13.2 | Python 3.13.13
Quality: pending | Updated: 2026-05-29
"""

import os

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns


# Theme tokens (see prompts/default-style-guide.md "Theme-adaptive Chrome")
THEME = os.getenv("ANYPLOT_THEME", "light")

PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
INK_MUTED = "#6B6A63" if THEME == "light" else "#A8A79F"

# Imprint palette — first series always #009E73
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

# Columns: set these to your table's column names
PROBABILITY = "Probability (p)"  # role: p
IMPURITY = "Impurity (normalized)"  # role: extra
CRITERION = "Splitting criterion"  # role: extra

# Data: replace this block with your own table, for example df = pd.read_csv("impurity.csv")
p = np.linspace(0, 1, 500)

gini = 2 * p * (1 - p)

# Entropy with edge-case handling (0 * log2(0) → 0 by convention)
entropy = np.zeros_like(p)
inner = (p > 0) & (p < 1)
entropy[inner] = -p[inner] * np.log2(p[inner]) - (1 - p[inner]) * np.log2(1 - p[inner])

df = pd.DataFrame(
    {
        PROBABILITY: np.concatenate([p, p]),
        IMPURITY: np.concatenate([gini / gini.max(), entropy / entropy.max()]),
        CRITERION: ["Gini: 2p(1−p)"] * len(p) + ["Entropy: −p log₂p − (1−p) log₂(1−p)"] * len(p),
    }
)

# Plot: reads only df and the constants above
table = df.pivot_table(index=PROBABILITY, columns=CRITERION, values=IMPURITY, sort=False)
gini_curve, entropy_curve = table.iloc[:, 0], table.iloc[:, 1]
gap = entropy_curve - gini_curve
top = df[IMPURITY].max()

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
        "grid.color": INK_MUTED,
        "grid.alpha": 0.12,
        "legend.facecolor": ELEVATED_BG,
        "legend.edgecolor": INK_SOFT,
    },
)

# Canvas: landscape 3200×1800 px; no bbox_inches="tight" at save
fig, (ax, ax_gap) = plt.subplots(
    2, 1, figsize=(8, 4.5), dpi=400, sharex=True, gridspec_kw={"height_ratios": [4, 1.3], "hspace": 0.12}
)

n_criteria = df[CRITERION].nunique()
sns.lineplot(
    data=df,
    x=PROBABILITY,
    y=IMPURITY,
    hue=CRITERION,
    style=CRITERION,
    palette=IMPRINT_PALETTE[:n_criteria],
    linewidth=2.5,
    ax=ax,
)

# Max-impurity marker at the peak of the curves
peak = df.loc[df[IMPURITY].idxmax()]
ax.plot(peak[PROBABILITY], peak[IMPURITY], "o", color=INK, markersize=5, zorder=5)
ax.annotate(
    f"Max impurity\np = {peak[PROBABILITY]:.1f}",
    xy=(peak[PROBABILITY], peak[IMPURITY]),
    xytext=(-80, -38),
    textcoords="offset points",
    fontsize=9,
    color=INK,
    arrowprops={"arrowstyle": "->", "color": INK_MUTED, "lw": 1.2, "connectionstyle": "arc3,rad=0.15"},
    bbox={"boxstyle": "round,pad=0.4", "facecolor": ELEVATED_BG, "edgecolor": INK_SOFT, "alpha": 0.92, "lw": 0.8},
)

ax.yaxis.grid(True, linewidth=0.8)
ax.set_ylim(-0.03 * top, top * 1.34)
ax.set_ylabel(IMPURITY, fontsize=10, labelpad=8)
ax.set_xlabel("")
ax.tick_params(axis="both", labelsize=8)
ax.tick_params(axis="x", labelbottom=False)
ax.set_title("line-impurity-comparison · python · seaborn · anyplot.ai", fontsize=12, fontweight="medium", pad=14)
ax.legend(
    title=CRITERION, title_fontsize=8, fontsize=8, loc="upper right", framealpha=0.95, fancybox=False, borderpad=0.8
).get_frame().set_linewidth(0.8)

# Lower strip: the difference between the two curves
ax_gap.plot(gap.index, gap.values, color=INK_SOFT, linewidth=1.5)
widest = gap.idxmax()
ax_gap.plot(widest, gap.max(), "o", color=INK_SOFT, markersize=4, zorder=5)
ax_gap.annotate(
    f"Max gap {gap.max():.2f} at p = {widest:.2f}",
    xy=(widest, gap.max()),
    xytext=(10, 9),
    textcoords="offset points",
    fontsize=8,
    fontstyle="italic",
    color=INK_SOFT,
    va="bottom",
)
ax_gap.yaxis.grid(True, linewidth=0.8)
ax_gap.set_ylim(0, gap.max() * 1.7)
ax_gap.set_ylabel("Entropy − Gini", fontsize=8, labelpad=8)
ax_gap.set_xlabel(PROBABILITY, fontsize=10, labelpad=8)
ax_gap.tick_params(axis="both", labelsize=8)
ax_gap.set_xlim(df[PROBABILITY].min(), df[PROBABILITY].max())

sns.despine(fig=fig, top=True, right=True)

plt.tight_layout()
plt.savefig(f"plot-{THEME}.png", dpi=400, facecolor=PAGE_BG)
