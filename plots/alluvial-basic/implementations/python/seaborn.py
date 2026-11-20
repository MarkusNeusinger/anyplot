""" anyplot.ai
alluvial-basic: Basic Alluvial Diagram
Library: seaborn 0.13.2 | Python 3.14.10
Quality: 84/100 | Updated: 2026-11-20
"""

import os

import matplotlib.patches as mpatches
import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Imprint palette: all eight positions, one per category in order
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

sns.set_theme(
    style="white",
    rc={"figure.facecolor": PAGE_BG, "axes.facecolor": PAGE_BG, "text.color": INK, "font.family": "sans-serif"},
)

# Columns: set these to your table's column names
YEAR = "Year"  # role: time_point
SECTOR = "Sector"  # role: category
NEXT_YEAR = "Next year"  # role: extra
NEXT_SECTOR = "Next sector"  # role: extra
VALUE = "Sector employees (thousands)"  # role: value
FLOW = "Employees moving (thousands)"  # role: flow

# Data: replace this block with your own table, for example df = pd.read_csv("flows.csv")
# One row per flow: how many employees moved from SECTOR in YEAR to NEXT_SECTOR in NEXT_YEAR.
sectors = ["Technology", "Finance", "Healthcare", "Manufacturing"]
transitions = {
    ("2021", "2022"): [[400, 25, 15, 10], [20, 250, 5, 5], [10, 5, 300, 5], [70, 10, 40, 130]],
    ("2022", "2023"): [[450, 15, 25, 10], [25, 240, 15, 10], [30, 10, 310, 10], [30, 5, 15, 100]],
    ("2023", "2024"): [[490, 15, 20, 10], [30, 225, 10, 5], [45, 10, 300, 10], [25, 5, 20, 80]],
}
df = pd.DataFrame(
    [
        {YEAR: year, SECTOR: src, NEXT_YEAR: next_year, NEXT_SECTOR: dst, VALUE: sum(row), FLOW: flow}
        for (year, next_year), matrix in transitions.items()
        for src, row in zip(sectors, matrix, strict=True)
        for dst, flow in zip(sectors, row, strict=True)
    ]
)

# Plot: reads only df and the constants above
periods = list(pd.unique(df[YEAR])) + [df[NEXT_YEAR].iloc[-1]]
categories = list(pd.unique(pd.concat([df[SECTOR], df[NEXT_SECTOR]])))
colors = {category: IMPRINT_PALETTE[i % len(IMPRINT_PALETTE)] for i, category in enumerate(categories)}

# Block size of each category per column: what leaves it, and in the last column what enters it
outflow = df.groupby([YEAR, SECTOR], sort=False)[VALUE].first().to_dict()
inflow = df.groupby([NEXT_YEAR, NEXT_SECTOR], sort=False)[FLOW].sum().to_dict()
sizes = [
    {c: outflow.get((p, c), 0.0) for c in categories}
    if k < len(periods) - 1
    else {c: inflow.get((p, c), 0.0) for c in categories}
    for k, p in enumerate(periods)
]

HEIGHT = 100  # the tallest column spans this many y units
scale = HEIGHT / max(sum(s.values()) for s in sizes)
bar_width = 0.44

fig, ax = plt.subplots(figsize=(8, 4.5), dpi=400, facecolor=PAGE_BG)
ax.set_facecolor(PAGE_BG)

# Blocks: one stack per time point, bottom to top in category order
blocks = []
for k, period in enumerate(periods):
    bottoms = {}
    y = 0.0
    for category in categories:
        height = sizes[k][category] * scale
        bottoms[category] = y
        if height > 0:
            ax.add_patch(
                mpatches.Rectangle(
                    (k - bar_width / 2, y),
                    bar_width,
                    height,
                    facecolor=colors[category],
                    edgecolor=PAGE_BG,
                    linewidth=0.8,
                )
            )
            ax.text(
                k,
                y + height / 2,
                category,
                ha="center",
                va="center",
                fontsize=7.5,
                color=INK,
                bbox={"boxstyle": "round,pad=0.15", "facecolor": ELEVATED_BG, "edgecolor": "none", "alpha": 0.9},
            )
        y += height
    blocks.append(bottoms)
    ax.text(k, y + 2, str(period), ha="center", va="bottom", fontsize=10, fontweight="bold", color=INK)

# Bands: width proportional to flow, stacked inside the source and target blocks
source_next = [dict(b) for b in blocks]
target_next = [dict(b) for b in blocks]
for period, src, _, dst, _, flow in df.itertuples(index=False):
    if not flow > 0:
        continue
    k = periods.index(period)
    width = flow * scale
    y0 = source_next[k][src]
    y1 = target_next[k + 1][dst]
    source_next[k][src] += width
    target_next[k + 1][dst] += width

    xa = k + bar_width / 2
    xb = k + 1 - bar_width / 2
    xm = (xa + xb) / 2
    verts = [
        (xa, y0),
        (xm, y0),
        (xm, y1),
        (xb, y1),
        (xb, y1 + width),
        (xm, y1 + width),
        (xm, y0 + width),
        (xa, y0 + width),
    ]
    codes = [
        mpatches.Path.MOVETO,
        mpatches.Path.CURVE4,
        mpatches.Path.CURVE4,
        mpatches.Path.CURVE4,
        mpatches.Path.LINETO,
        mpatches.Path.CURVE4,
        mpatches.Path.CURVE4,
        mpatches.Path.CURVE4,
    ]
    ax.add_patch(
        mpatches.PathPatch(
            mpatches.Path(verts + [verts[0]], codes + [mpatches.Path.CLOSEPOLY]),
            facecolor=colors[src],
            edgecolor=colors[src],
            linewidth=0.3,
            alpha=0.4,
        )
    )

# Style
ax.set_xlim(-0.4, len(periods) - 1 + 0.4)
ax.set_ylim(-1, HEIGHT * 1.1)
ax.set_xticks([])
ax.set_yticks([])
sns.despine(ax=ax, left=True, bottom=True)

ax.set_title("alluvial-basic · python · seaborn · anyplot.ai", fontsize=12, fontweight="medium", color=INK, pad=10)
fig.text(
    0.5,
    0.03,
    f"{VALUE}: block height and band width are proportional to the number of employees",
    ha="center",
    va="center",
    fontsize=8,
    color=INK_SOFT,
)
fig.subplots_adjust(left=0.03, right=0.97, top=0.9, bottom=0.08)
plt.savefig(f"plot-{THEME}.png", dpi=400, facecolor=PAGE_BG)
