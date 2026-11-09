""" anyplot.ai
parallel-categories-basic: Basic Parallel Categories Plot
Library: seaborn 0.13.2 | Python 3.14.10
Quality: 87/100 | Updated: 2026-11-09
"""

import os

import matplotlib.patheffects as patheffects
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
from matplotlib.colors import LinearSegmentedColormap
from matplotlib.patches import PathPatch
from matplotlib.path import Path


# Theme tokens (prompts/default-style-guide.md "Background" and "Theme-adaptive Chrome")
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Imprint sequential ramp: passenger class is an ordered category, so its levels take steps of one ramp
IMPRINT_SEQ = LinearSegmentedColormap.from_list("imprint_seq", ["#009E73", "#4467A3"])

sns.set_theme(style="white", rc={"figure.facecolor": PAGE_BG, "axes.facecolor": PAGE_BG, "text.color": INK})

# Constants
BAR_WIDTH = 0.06  # width of an axis bar, as a share of the spacing between two axes
RIBBON_ALPHA = 0.65 if THEME == "light" else 0.8  # the dark page needs denser ribbons to keep their hue

# Columns: set these to your table's column names; the first one colors the ribbons
DIMENSIONS = ["Class", "Sex", "Age group", "Embarked", "Outcome"]  # role: dimension_

# Data: replace this block with your own table, for example df = pd.read_csv("passengers.csv")
# Titanic-style passengers: survival chances rise with class, for women and for children.
np.random.seed(42)
n_passengers = 500
passenger_class = np.random.choice(["First", "Second", "Third"], n_passengers, p=[0.25, 0.25, 0.50])
sex = np.random.choice(["Male", "Female"], n_passengers, p=[0.55, 0.45])
age_group = np.random.choice(["Child", "Adult", "Senior"], n_passengers, p=[0.15, 0.70, 0.15])
port = np.random.choice(["Southampton", "Cherbourg", "Queenstown"], n_passengers, p=[0.70, 0.20, 0.10])
survival_chance = 0.3 + 0.35 * (passenger_class == "First") + 0.15 * (passenger_class == "Second")
survival_chance = np.minimum(survival_chance + 0.25 * (sex == "Female") + 0.15 * (age_group == "Child"), 0.95)
outcome = np.where(np.random.random(n_passengers) < survival_chance, "Survived", "Lost")
df = pd.DataFrame(dict(zip(DIMENSIONS, [passenger_class, sex, age_group, port, outcome], strict=True)))

# Plot: reads only df and the constants above
data = df[DIMENSIONS].dropna().astype(str)
total = len(data)
color_dim = DIMENSIONS[0]
pairs = list(zip(DIMENSIONS[:-1], DIMENSIONS[1:], strict=True))

# Category order per axis: the first axis sorted, every later one by the mean position its observations
# hold on the axis before it (the barycenter heuristic), which keeps ribbon crossings low
orders = {color_dim: sorted(data[color_dim].unique())}
for left, right in pairs:
    share = data[left].value_counts().reindex(orders[left])
    center = share.cumsum() - share / 2
    orders[right] = list(data[left].map(center).groupby(data[right]).mean().sort_values().index)
counts = {dim: data[dim].value_counts().reindex(orders[dim]) for dim in DIMENSIONS}
above = {dim: counts[dim].cumsum() - counts[dim] for dim in DIMENSIONS}  # observations above each segment
rank = {dim: pd.Series(range(len(orders[dim])), index=orders[dim]) for dim in DIMENSIONS}

levels = orders[color_dim]
ribbon_colors = dict(zip(levels, IMPRINT_SEQ(np.linspace(0, 1, len(levels))), strict=True))

fig, ax = plt.subplots(figsize=(8, 4.5), dpi=400)

# Axis bars: one stacked count bar per dimension, one segment per category, top to bottom in layout order;
# the first dimension's segments carry the ribbon colors and so name them
segments = data.melt(value_vars=DIMENSIONS, var_name="dimension", value_name="category")
segments["segment"] = segments["dimension"] + " · " + segments["category"]
segment_colors = {
    f"{dim} · {cat}": ribbon_colors[cat] if dim == color_dim else INK_SOFT for dim in DIMENSIONS for cat in orders[dim]
}
sns.histplot(
    data=segments,
    x="dimension",
    hue="segment",
    hue_order=list(segment_colors),
    palette=segment_colors,
    multiple="stack",
    shrink=BAR_WIDTH,
    alpha=1,
    edgecolor=PAGE_BG,
    linewidth=1.2,
    legend=False,
    zorder=2,
    ax=ax,
)

# Ribbons: one closed band per combination of neighboring categories and ribbon color, its width the
# number of observations it carries, stacked inside each segment by color so every color keeps its place
codes = [Path.MOVETO, *[Path.CURVE4] * 3, Path.LINETO, *[Path.CURVE4] * 3, Path.CLOSEPOLY]
for i, (left, right) in enumerate(pairs):
    keys = list(dict.fromkeys([color_dim, left, right]))
    flows = data.groupby(keys).size().rename("n").reset_index()
    for dim in keys:
        flows[f"rank {dim}"] = flows[dim].map(rank[dim])
    flows = flows.sort_values([f"rank {left}", f"rank {color_dim}", f"rank {right}"])
    flows["start"] = flows[left].map(above[left]) + flows.groupby(left)["n"].cumsum() - flows["n"]
    flows = flows.sort_values([f"rank {right}", f"rank {color_dim}", f"rank {left}"])
    flows["end"] = flows[right].map(above[right]) + flows.groupby(right)["n"].cumsum() - flows["n"]
    x0, x1 = i + BAR_WIDTH / 2, i + 1 - BAR_WIDTH / 2
    mid = (x0 + x1) / 2
    for start, end, n, level in zip(flows["start"], flows["end"], flows["n"], flows[color_dim], strict=True):
        top0, top1 = total - start, total - end
        vertices = [(x0, top0), (mid, top0), (mid, top1), (x1, top1)]
        vertices += [(x1, top1 - n), (mid, top1 - n), (mid, top0 - n), (x0, top0 - n), (x0, top0)]
        band = PathPatch(Path(vertices, codes), facecolor=ribbon_colors[level], edgecolor="none", alpha=RIBBON_ALPHA)
        ax.add_patch(band)

# Category labels beside their segments, above the ribbons with a page-colored halo;
# the first axis is labeled on its left, where no ribbon runs
halo = [patheffects.withStroke(linewidth=2.8, foreground=PAGE_BG)]
for i, dim in enumerate(DIMENSIONS):
    side = -1 if i == 0 else 1
    for cat, y in (total - above[dim] - counts[dim] / 2).items():
        ax.annotate(
            cat,
            (i + side * BAR_WIDTH / 2, y),
            xytext=(side * 4, 0),
            textcoords="offset points",
            ha="right" if side < 0 else "left",
            va="center",
            fontsize=8,
            color=INK,
            path_effects=halo,
            zorder=5,
        )

# Style: dimension names head their axes; only segment lengths and ribbon widths carry counts
ax.set_title("parallel-categories-basic · python · seaborn · anyplot.ai", fontsize=12, fontweight="medium", pad=10)
ax.xaxis.set_ticks_position("top")
ax.tick_params(axis="x", length=0, labelsize=10, labelcolor=INK, pad=4)
ax.set_xlabel("")
ax.set_yticks([])
ax.set_ylabel("")
ax.set_xlim(-0.5 - BAR_WIDTH, len(DIMENSIONS) - 0.5 + BAR_WIDTH)
ax.set_ylim(0, total)
sns.despine(ax=ax, left=True, bottom=True)

fig.tight_layout()
plt.savefig(f"plot-{THEME}.png", dpi=400, facecolor=PAGE_BG)
