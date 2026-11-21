"""anyplot.ai
cat-box-strip: Box Plot with Strip Overlay
Library: seaborn 0.13.2 | Python 3.13.13
Quality: 92/100 | Updated: 2026-05-13
"""

import os

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

# Imprint palette - first series green for the boxes, second position for the strip points
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]
BRAND = IMPRINT_PALETTE[0]
ACCENT = IMPRINT_PALETTE[1]

# Columns
BATCH = "Batch"  # role: category
SCORE = "Quality Score (points)"  # role: value

# Data
# Product quality scores across manufacturing batches
np.random.seed(42)
batch_a = np.random.normal(75, 8, 40)  # Centered, moderate spread
batch_b = np.random.normal(82, 5, 35)  # Higher center, tight spread
batch_c = np.concatenate([np.random.normal(68, 6, 30), [45, 48, 95, 97]])  # Main distribution + outliers
batch_d = np.random.normal(70, 12, 45)  # Wide spread
groups = {"Batch A": batch_a, "Batch B": batch_b, "Batch C": batch_c, "Batch D": batch_d}
df = pd.DataFrame(
    {BATCH: [name for name, values in groups.items() for _ in values], SCORE: np.concatenate(list(groups.values()))}
)

# Plot
# Configure seaborn theme
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

fig, ax = plt.subplots(figsize=(8, 4.5), dpi=400, facecolor=PAGE_BG)
ax.set_facecolor(PAGE_BG)

sns.boxplot(data=df, x=BATCH, y=SCORE, color=BRAND, width=0.5, linewidth=1, linecolor=INK_SOFT, fliersize=0, ax=ax)
sns.stripplot(
    data=df, x=BATCH, y=SCORE, color=ACCENT, size=5, alpha=0.7, jitter=0.2, edgecolor=PAGE_BG, linewidth=0.3, ax=ax
)

# Style
ax.set_title("cat-box-strip · python · seaborn · anyplot.ai", fontsize=12, color=INK)
ax.set_xlabel("Manufacturing Batch", fontsize=10, color=INK)
ax.tick_params(axis="both", labelsize=8, colors=INK_SOFT)
ax.yaxis.grid(True, alpha=0.10, linewidth=0.8, color=INK)
sns.despine(ax=ax)
for spine in ("left", "bottom"):
    ax.spines[spine].set_color(INK_SOFT)

# Shared value axis with padding, not forced to zero
pad = 0.05 * (df[SCORE].max() - df[SCORE].min())
ax.set_ylim(df[SCORE].min() - pad, df[SCORE].max() + pad)

fig.tight_layout()
plt.savefig(f"plot-{THEME}.png", dpi=400, facecolor=PAGE_BG)
