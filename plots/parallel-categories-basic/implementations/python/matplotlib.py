"""anyplot.ai
parallel-categories-basic: Basic Parallel Categories Plot
Library: matplotlib 3.10.9 | Python 3.13.13
Quality: 94/100 | Updated: 2026-05-13
"""

import os

import matplotlib.patches as mpatches
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.path import Path


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Imprint palette: all eight positions, one per category of the colored dimension in order
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

# Columns: set these to your table's column names (one per axis, left to right)
DIMENSIONS = ["Applicant segment", "Loan purpose", "Decision"]  # role: dimension_

# Data: replace this block with your own table, for example df = pd.read_csv("applications.csv")
rng = np.random.default_rng(42)
segments = ["Salaried", "Self-employed", "Student", "Retired"]
purposes = ["Mortgage", "Auto", "Personal", "Education"]
decisions = ["Approved", "Referred", "Declined"]
n_applications = 700
segment_draw = rng.choice(len(segments), size=n_applications, p=[0.42, 0.24, 0.18, 0.16])
purpose_by_segment = np.array(
    [[0.45, 0.30, 0.20, 0.05], [0.25, 0.25, 0.45, 0.05], [0.00, 0.20, 0.30, 0.50], [0.30, 0.15, 0.50, 0.05]]
)
purpose_draw = np.array([rng.choice(len(purposes), p=purpose_by_segment[s]) for s in segment_draw])
decision_by_purpose = np.array([[0.70, 0.20, 0.10], [0.62, 0.18, 0.20], [0.40, 0.25, 0.35], [0.50, 0.20, 0.30]])
decision_draw = np.array([rng.choice(len(decisions), p=decision_by_purpose[p]) for p in purpose_draw])
df = (
    pd.DataFrame(
        {
            DIMENSIONS[0]: np.array(segments)[segment_draw],
            DIMENSIONS[1]: np.array(purposes)[purpose_draw],
            DIMENSIONS[2]: np.array(decisions)[decision_draw],
        }
    )
    .assign(_s=segment_draw, _p=purpose_draw, _d=decision_draw)
    .sort_values(["_s", "_p", "_d"])
    .drop(columns=["_s", "_p", "_d"])
    .reset_index(drop=True)
)

# Plot: reads only df and the constants above
dims = list(DIMENSIONS)
df = df.dropna(subset=dims)  # a row with a missing category has no ribbon
order = {dim: list(df[dim].unique()) for dim in dims}  # layout order: first appearance in df
color_of = {cat: IMPRINT_PALETTE[i % len(IMPRINT_PALETTE)] for i, cat in enumerate(order[dims[0]])}
n_rows = len(df)
n_dims = len(dims)
xs = np.linspace(0, 1, n_dims)
half_w = 0.075
y_lo, y_hi, gap = 0.02, 0.92, 0.025

# Segment geometry: length proportional to the category's share of the observations
seg_y = {}
for dim in dims:
    counts = df[dim].value_counts()
    usable = (y_hi - y_lo) - gap * (len(order[dim]) - 1)
    cursor = y_lo
    for cat in order[dim]:
        length = counts[cat] / n_rows * usable
        seg_y[(dim, cat)] = (cursor, cursor + length)
        cursor += length + gap
unit = (y_hi - y_lo - gap * (max(len(v) for v in order.values()) - 1)) / n_rows


def ribbon_path(x0, x1, left, right):
    """Closed bezier band from [left] on the x0 side to [right] on the x1 side."""
    xm0, xm1 = x0 + (x1 - x0) * 0.4, x0 + (x1 - x0) * 0.6
    verts = [
        (x0, left[0]),
        (xm0, left[0]),
        (xm1, right[0]),
        (x1, right[0]),
        (x1, right[1]),
        (xm1, right[1]),
        (xm0, left[1]),
        (x0, left[1]),
        (x0, left[0]),
    ]
    codes = [Path.MOVETO] + [Path.CURVE4] * 3 + [Path.LINETO] + [Path.CURVE4] * 3 + [Path.CLOSEPOLY]
    return Path(verts, codes)


fig, ax = plt.subplots(figsize=(8, 4.5), dpi=400, facecolor=PAGE_BG)
ax.set_facecolor(PAGE_BG)

# Ribbons: one per (first-dimension category, left category, right category), colored by the first dimension
for i in range(n_dims - 1):
    a, b = dims[i], dims[i + 1]
    pair = pd.DataFrame({"src": df[dims[0]], "left": df[a], "right": df[b]})
    flows = pair.groupby(["src", "left", "right"], sort=False).size().reset_index(name="n")
    flows["ks"] = flows["src"].map(order[dims[0]].index)
    flows["kl"] = flows["left"].map(order[a].index)
    flows["kr"] = flows["right"].map(order[b].index)
    left_cursor = {cat: seg_y[(a, cat)][0] for cat in order[a]}
    right_cursor = {cat: seg_y[(b, cat)][0] for cat in order[b]}
    left_pos, right_pos = {}, {}
    for row in flows.sort_values(["kl", "kr", "ks"]).itertuples():
        left_pos[row.Index] = left_cursor[row.left]
        left_cursor[row.left] += row.n * unit
    for row in flows.sort_values(["kr", "kl", "ks"]).itertuples():
        right_pos[row.Index] = right_cursor[row.right]
        right_cursor[row.right] += row.n * unit
    for row in flows.itertuples():
        thickness = row.n * unit
        path = ribbon_path(
            xs[i] + half_w,
            xs[i + 1] - half_w,
            (left_pos[row.Index], left_pos[row.Index] + thickness),
            (right_pos[row.Index], right_pos[row.Index] + thickness),
        )
        ax.add_patch(mpatches.PathPatch(path, facecolor=color_of[row.src], edgecolor=PAGE_BG, linewidth=0.3, alpha=0.6))

# Category segments with their labels
for x, dim in zip(xs, dims, strict=True):
    for cat in order[dim]:
        lo, hi = seg_y[(dim, cat)]
        ax.add_patch(
            mpatches.Rectangle(
                (x - half_w, lo), 2 * half_w, hi - lo, facecolor=ELEVATED_BG, edgecolor=INK_SOFT, linewidth=1.0
            )
        )
        ax.text(x, (lo + hi) / 2, cat, ha="center", va="center", fontsize=7.5, fontweight="bold", color=INK)
    ax.text(x, y_hi + 0.03, dim, ha="center", va="bottom", fontsize=10, fontweight="bold", color=INK)

# Legend names the dimension that colors the ribbons
handles = [mpatches.Patch(facecolor=color_of[cat], alpha=0.6, label=cat) for cat in order[dims[0]]]
leg = ax.legend(
    handles=handles,
    title=dims[0],
    fontsize=8,
    title_fontsize=8,
    loc="lower center",
    bbox_to_anchor=(0.5, 0),
    ncol=len(handles),
)
leg.get_frame().set_facecolor(ELEVATED_BG)
leg.get_frame().set_edgecolor(INK_SOFT)
plt.setp(leg.get_texts(), color=INK_SOFT)
leg.get_title().set_color(INK)

# Style
ax.set_xlim(-half_w - 0.02, 1 + half_w + 0.02)
ax.set_ylim(-0.1, 1.02)
ax.axis("off")
ax.set_title(
    "parallel-categories-basic · python · matplotlib · anyplot.ai", fontsize=12, fontweight="medium", color=INK
)
fig.subplots_adjust(left=0.03, right=0.97, top=0.92, bottom=0.03)
plt.savefig(f"plot-{THEME}.png", dpi=400, facecolor=PAGE_BG)
