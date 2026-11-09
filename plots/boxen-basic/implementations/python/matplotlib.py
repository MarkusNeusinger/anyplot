"""anyplot.ai
boxen-basic: Basic Boxen Plot (Letter-Value Plot)
Library: matplotlib 3.10.9 | Python 3.13.13
Quality: pending | Updated: 2026-05-17
"""

import os

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.colors import LinearSegmentedColormap
from matplotlib.lines import Line2D
from matplotlib.patches import Patch


# Theme tokens (see prompts/default-style-guide.md "Background" + "Theme-adaptive Chrome")
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
INK_MUTED = "#6B6A63" if THEME == "light" else "#A8A79F"

# Imprint palette: quantile levels are ordered, so they take discrete steps of imprint_seq
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]
imprint_seq = LinearSegmentedColormap.from_list("imprint_seq", [IMPRINT_PALETTE[0], IMPRINT_PALETTE[2]])

# Constants
N_LEVELS = 6  # letter-value depth: quartiles, eighths, sixteenths, ... out to 1/128
BASE_WIDTH = 0.75  # width of the quartile box in category units
WIDTH_DECAY = 0.82  # each deeper level is 82 % as wide as the one inside it

# Columns: set these to your table's column names
ENDPOINT = "API Endpoint"  # role: category
RESPONSE_TIME = "Response Time (ms)"  # role: value

# Data: replace this block with your own table, for example df = pd.read_csv("response_times.csv")
# Right-skewed response times: each endpoint is a mix of fast, slow and very slow requests
np.random.seed(42)
n_points = 2000
mixtures = {
    "Fast API": [(50, 0.85), (200, 0.12), (500, 0.03)],
    "DB Query": [(120, 0.7), (350, 0.25), (800, 0.05)],
    "File Upload": [(200, 0.6), (500, 0.3), (1000, 0.1)],
    "Report Gen": [(300, 0.5), (700, 0.35), (1500, 0.15)],
}
frames = []
for endpoint, components in mixtures.items():
    times = np.concatenate([np.random.exponential(scale=s, size=int(n_points * f)) for s, f in components])
    frames.append(pd.DataFrame({ENDPOINT: endpoint, RESPONSE_TIME: times}))
df = pd.concat(frames, ignore_index=True)

# Plot: reads only df and the constants above
groups = df.groupby(ENDPOINT, sort=False)[RESPONSE_TIME]
names = list(groups.groups)
positions = np.arange(len(names))
tail_shares = 0.5 ** (np.arange(N_LEVELS) + 2)  # 0.25, 0.125, 0.0625, ... below each lower edge
level_colors = imprint_seq(np.linspace(0, 1, N_LEVELS))

fig, ax = plt.subplots(figsize=(8, 4.5), dpi=400, facecolor=PAGE_BG)
ax.set_facecolor(PAGE_BG)

for pos, (_, values) in zip(positions, groups, strict=True):
    values = values.dropna().to_numpy()
    lower = np.quantile(values, tail_shares)
    upper = np.quantile(values, 1 - tail_shares)

    # Nested letter-value boxes, widest (quartiles) drawn last so it sits on top of the deeper slivers
    for level in range(N_LEVELS - 1, -1, -1):
        ax.bar(
            pos,
            upper[level] - lower[level],
            width=BASE_WIDTH * WIDTH_DECAY**level,
            bottom=lower[level],
            color=level_colors[level],
            edgecolor=PAGE_BG,
            linewidth=0.8,
            zorder=3 + N_LEVELS - level,
        )

    ax.hlines(
        np.median(values), pos - BASE_WIDTH / 2, pos + BASE_WIDTH / 2, colors=INK, linewidth=2.2, zorder=4 + N_LEVELS
    )

    outliers = values[(values < lower[-1]) | (values > upper[-1])]
    ax.scatter(np.full(outliers.size, pos), outliers, s=14, color=INK_MUTED, alpha=0.6, edgecolors="none", zorder=2)

# Style
title = "boxen-basic · python · matplotlib · anyplot.ai"
ax.set_title(title, fontsize=12, fontweight="medium", color=INK)
ax.set_xlabel(ENDPOINT, fontsize=10, color=INK)
ax.set_ylabel(RESPONSE_TIME, fontsize=10, color=INK)
ax.set_xticks(positions, names)
ax.set_ylim(bottom=min(0, df[RESPONSE_TIME].min()))
ax.tick_params(axis="both", labelsize=8, colors=INK_SOFT, labelcolor=INK_SOFT)
ax.tick_params(axis="x", length=0)
ax.spines["top"].set_visible(False)
ax.spines["right"].set_visible(False)
for side in ("left", "bottom"):
    ax.spines[side].set_color(INK_SOFT)
ax.yaxis.grid(True, alpha=0.15, linewidth=0.8, color=INK)
ax.set_axisbelow(True)

# Legend: one entry per quantile level, plus the median and outlier marks
handles = [Line2D([0], [0], color=INK, linewidth=2.2, label="Median")]
handles += [
    Patch(facecolor=level_colors[level], edgecolor=PAGE_BG, label=f"{100 * share:.3g}–{100 * (1 - share):.4g} %")
    for level, share in enumerate(tail_shares)
]
handles.append(
    Line2D(
        [0],
        [0],
        marker="o",
        linestyle="None",
        markersize=4,
        markerfacecolor=INK_MUTED,
        markeredgecolor="none",
        alpha=0.6,
        label="Outliers",
    )
)
leg = ax.legend(handles=handles, loc="upper left", fontsize=8, title="Letter values", title_fontsize=8)
leg.get_frame().set_facecolor(ELEVATED_BG)
leg.get_frame().set_edgecolor(INK_SOFT)
plt.setp(leg.get_texts(), color=INK_SOFT)
leg.get_title().set_color(INK)

plt.tight_layout()
plt.savefig(f"plot-{THEME}.png", dpi=400, facecolor=PAGE_BG)
