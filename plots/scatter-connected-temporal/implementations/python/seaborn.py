""" anyplot.ai
scatter-connected-temporal: Connected Scatter Plot with Temporal Path
Library: seaborn 0.13.2 | Python 3.13.16
Quality: 86/100 | Updated: 2026-10-08
"""

import os

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
from matplotlib.collections import LineCollection
from matplotlib.colors import LinearSegmentedColormap


# Theme-adaptive chrome tokens (Imprint palette)
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Imprint sequential colormap: brand green (early) → blue (recent)
imprint_seq = LinearSegmentedColormap.from_list("imprint_seq", ["#009E73", "#4467A3"])

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
        "grid.alpha": 0.15,
        "legend.facecolor": ELEVATED_BG,
        "legend.edgecolor": INK_SOFT,
    },
)

# Monthly closing price vs. average daily trading volume for a fictional stock, Jan 2023 – Dec 2024
months = pd.period_range("2023-01", periods=24, freq="M")
t = np.arange(len(months), dtype=float)
n = len(months)

price = np.array(
    [
        102,
        108,
        115,
        121,
        118,
        109,
        98,
        92,
        95,
        104,
        113,
        125,
        134,
        129,
        121,
        117,
        124,
        136,
        148,
        155,
        149,
        141,
        146,
        158,
    ],
    dtype=float,
)
volume = np.array(
    [
        4.1,
        4.6,
        5.8,
        6.4,
        5.9,
        7.8,
        9.6,
        10.4,
        8.2,
        6.1,
        5.3,
        5.9,
        7.1,
        6.3,
        5.5,
        5.0,
        5.4,
        6.8,
        8.1,
        9.0,
        7.4,
        6.2,
        5.8,
        7.5,
    ]
)

X_LABEL = "Average Daily Volume (million shares)"
Y_LABEL = "Closing Price (USD)"
df = pd.DataFrame({X_LABEL: volume, Y_LABEL: price, "Month": t})

# Canvas: landscape 16:9 → exactly 3200×1800 px
fig, ax = plt.subplots(figsize=(8, 4.5), dpi=400)
fig.subplots_adjust(left=0.11, bottom=0.13, right=0.88, top=0.82)

# Background: seaborn KDE contours showing where price/volume spent most of the two years
sns.kdeplot(data=df, x=X_LABEL, y=Y_LABEL, levels=3, color=INK_SOFT, alpha=0.2, linewidths=0.7, bw_adjust=1.2, ax=ax)

# Temporal path: LineCollection with Imprint sequential gradient
norm = plt.Normalize(t[0], t[-1])
points = np.column_stack([volume, price])
segments = np.array([[points[i], points[i + 1]] for i in range(n - 1)])
lc = LineCollection(segments, cmap=imprint_seq, norm=norm, linewidths=1.8, zorder=2, alpha=0.85)
lc.set_array(t[:-1])
ax.add_collection(lc)

# Scatter markers with temporal hue encoding via seaborn continuous palette
sns.scatterplot(
    data=df,
    x=X_LABEL,
    y=Y_LABEL,
    hue="Month",
    hue_norm=(t[0], t[-1]),
    palette=imprint_seq,
    s=120,
    edgecolor=PAGE_BG,
    linewidth=0.6,
    legend=False,
    zorder=3,
    ax=ax,
)

# Directional arrow on temporal path (Jun→Jul 2023 segment makes time direction explicit)
i_dir = 5
ax.annotate(
    "",
    xy=(volume[i_dir + 1], price[i_dir + 1]),
    xytext=(volume[i_dir], price[i_dir]),
    arrowprops={"arrowstyle": "-|>", "color": INK, "lw": 1.4, "mutation_scale": 14},
    zorder=4,
)

# Key time-point annotations: start, volume spike, rally peak, end
key_points = {0: (-8, -22), 7: (-6, -24), 11: (-34, 14), 19: (6, 14), n - 1: (14, 8)}
for idx, offset in key_points.items():
    ax.annotate(
        months[idx].strftime("%b %Y"),
        (volume[idx], price[idx]),
        textcoords="offset points",
        xytext=offset,
        fontsize=9,
        fontweight="bold",
        color=INK,
        arrowprops={"arrowstyle": "->", "color": INK_SOFT, "lw": 0.9, "connectionstyle": "arc3,rad=0.2"},
    )

# Narrative subtitle
ax.text(
    0.5,
    1.03,
    "Fictional stock: how price and trading volume moved together, Jan 2023 – Dec 2024",
    transform=ax.transAxes,
    fontsize=8,
    color=INK_SOFT,
    ha="center",
    va="bottom",
    style="italic",
)

ax.set_xlabel(X_LABEL, fontsize=10)
ax.set_ylabel(Y_LABEL, fontsize=10)
ax.set_title(
    "scatter-connected-temporal · python · seaborn · anyplot.ai", fontsize=12, fontweight="medium", pad=22, color=INK
)
ax.tick_params(axis="both", labelsize=8)
sns.despine(ax=ax)
ax.yaxis.grid(True, alpha=0.15, linewidth=0.6, color=INK)

ax.set_xlim(volume.min() - 0.8, volume.max() + 0.8)
ax.set_ylim(price.min() - 10, price.max() + 10)

# Colorbar for temporal scale
sm = plt.cm.ScalarMappable(cmap=imprint_seq, norm=norm)
sm.set_array([])
cbar = fig.colorbar(sm, ax=ax, pad=0.02, aspect=30, shrink=0.85)
cbar.set_ticks([0, 6, 12, 18, 23])
cbar.set_ticklabels([months[i].strftime("%b %Y") for i in (0, 6, 12, 18, 23)])
cbar.set_label("Month", fontsize=8, color=INK)
cbar.ax.tick_params(labelsize=7, colors=INK_SOFT)
cbar.outline.set_edgecolor(INK_SOFT)

plt.savefig(f"plot-{THEME}.png", dpi=400, facecolor=PAGE_BG)
