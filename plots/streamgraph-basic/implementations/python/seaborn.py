"""anyplot.ai
streamgraph-basic: Basic Stream Graph
Library: seaborn 0.13.2 | Python 3.13.13
Quality: 84/100 | Updated: 2026-05-05
"""

import os

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
from scipy.interpolate import make_interp_spline


THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

OKABE_ITO = ["#009E73", "#D55E00", "#0072B2", "#CC79A7", "#E69F00", "#56B4E9"]

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

# Data — monthly streaming hours by music genre over 2 years
np.random.seed(42)

months = pd.date_range("2023-01", periods=24, freq="ME")
genres = ["Pop", "Rock", "Hip-Hop", "Electronic", "Classical", "Jazz"]

data = {}
for i, genre in enumerate(genres):
    base = [40, 35, 50, 30, 15, 12][i]
    trend = np.linspace(0, [10, -5, 15, 8, 2, 5][i], 24)
    seasonal = 5 * np.sin(np.linspace(0, 4 * np.pi, 24) + i)
    noise = np.random.randn(24) * 3
    data[genre] = np.maximum(base + trend + seasonal + noise, 5)

df = pd.DataFrame(data, index=months)

# Streamgraph: centered baseline
values = df.values
cumsum = np.cumsum(values, axis=1)
total = cumsum[:, -1]
baseline = -total / 2

lowers = np.column_stack([baseline + cumsum[:, i] - values[:, i] for i in range(len(genres))])
uppers = np.column_stack([baseline + cumsum[:, i] for i in range(len(genres))])

# Smooth spline interpolation for flowing curves
x_numeric = np.arange(len(months), dtype=float)
x_smooth = np.linspace(0, len(months) - 1, 400)

# Plot
fig, ax = plt.subplots(figsize=(16, 9), facecolor=PAGE_BG)
ax.set_facecolor(PAGE_BG)

# Store splines to reuse for trend lines and annotations
splines = []
for i in range(len(genres)):
    spl_lower = make_interp_spline(x_numeric, lowers[:, i], k=3)
    spl_upper = make_interp_spline(x_numeric, uppers[:, i], k=3)
    splines.append((spl_lower, spl_upper))
    ax.fill_between(
        x_smooth,
        spl_lower(x_smooth),
        spl_upper(x_smooth),
        label=genres[i],
        color=OKABE_ITO[i],
        alpha=0.85,
        edgecolor=PAGE_BG,
        linewidth=0.5,
    )

# Seaborn-native center-line trend highlights for Hip-Hop and Rock
# sns.lineplot adds a genuine seaborn plotting element over the streams
for gname, linestyle in [("Hip-Hop", (0, (6, 3))), ("Rock", (0, (6, 3)))]:
    gi = genres.index(gname)
    spl_lo, spl_up = splines[gi]
    center_vals = (spl_lo(x_smooth) + spl_up(x_smooth)) / 2
    center_df = pd.DataFrame({"x": x_smooth, "y": center_vals})
    sns.lineplot(
        data=center_df,
        x="x",
        y="y",
        ax=ax,
        color=OKABE_ITO[gi],
        linewidth=2.5,
        linestyle=linestyle,
        alpha=0.85,
        legend=False,
    )

# Data storytelling: annotate the two dominant narrative threads
hip_hop_idx = genres.index("Hip-Hop")
rock_idx = genres.index("Rock")

# Hip-Hop center near month 20 (growth is visible by then)
hh_x = 20
hh_center = (splines[hip_hop_idx][0](hh_x) + splines[hip_hop_idx][1](hh_x)) / 2
ax.annotate(
    "Hip-Hop\nrising ↑",
    xy=(hh_x, hh_center),
    xytext=(hh_x - 4, hh_center + 28),
    fontsize=15,
    fontweight="bold",
    color=OKABE_ITO[hip_hop_idx],
    arrowprops={"arrowstyle": "->", "color": INK_SOFT, "lw": 1.5},
)

# Rock center near month 18 (decline well established)
rk_x = 18
rk_center = (splines[rock_idx][0](rk_x) + splines[rock_idx][1](rk_x)) / 2
ax.annotate(
    "Rock\ndeclining ↓",
    xy=(rk_x, rk_center),
    xytext=(rk_x - 5, rk_center - 32),
    fontsize=15,
    fontweight="bold",
    color=OKABE_ITO[rock_idx],
    arrowprops={"arrowstyle": "->", "color": INK_SOFT, "lw": 1.5},
)

# Style
tick_positions = [0, 4, 8, 12, 16, 20, 23]
tick_labels = [months[i].strftime("%b '%y") for i in tick_positions]
ax.set_xticks(tick_positions)
ax.set_xticklabels(tick_labels, fontsize=16, color=INK_SOFT)

ax.set_xlim(0, len(months) - 1)
ax.set_yticks([])
ax.set_ylabel("")
ax.set_xlabel("Month", fontsize=20, color=INK)
ax.set_title("streamgraph-basic · seaborn · anyplot.ai", fontsize=24, fontweight="medium", color=INK)

ax.legend(
    loc="upper left",
    fontsize=16,
    title="Genre",
    title_fontsize=16,
    facecolor=ELEVATED_BG,
    edgecolor=INK_SOFT,
    framealpha=0.9,
)

sns.despine(ax=ax, left=True, bottom=False)
ax.spines["bottom"].set_color(INK_SOFT)

plt.tight_layout()
plt.savefig(f"plot-{THEME}.png", dpi=300, bbox_inches="tight", facecolor=PAGE_BG)
