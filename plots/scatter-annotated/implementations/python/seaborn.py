"""anyplot.ai
scatter-annotated: Annotated Scatter Plot with Text Labels
Library: seaborn 0.13.2 | Python 3.13.13
Quality: 90/100 | Updated: 2026-05-13
"""

import os

import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Imprint palette: position 1 is always the first series
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

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

# Columns: set these to your table's column names
GDP = "GDP per capita (thousand USD)"  # role: x
LIFE_EXPECTANCY = "Life expectancy (years)"  # role: y
COUNTRY = "Country"  # role: label

# Data: replace this block with your own table, for example df = pd.read_csv("countries.csv")
df = pd.DataFrame(
    {
        COUNTRY: [
            "Norway",
            "United States",
            "Germany",
            "Australia",
            "Japan",
            "Saudi Arabia",
            "Turkey",
            "China",
            "Russia",
            "Brazil",
            "Mexico",
            "South Africa",
            "Indonesia",
            "India",
            "Nigeria",
            "Rwanda",
        ],
        GDP: [82.0, 76.3, 51.4, 64.8, 34.0, 30.4, 12.8, 12.7, 12.2, 8.9, 11.1, 6.7, 4.8, 2.4, 2.2, 0.9],
        LIFE_EXPECTANCY: [
            83.2,
            78.5,
            81.0,
            83.3,
            84.5,
            77.6,
            76.0,
            78.2,
            73.2,
            75.5,
            75.1,
            64.4,
            68.0,
            70.2,
            53.6,
            69.0,
        ],
    }
)

# Plot: reads only df and the constants above
fig, ax = plt.subplots(figsize=(8, 4.5), dpi=400, facecolor=PAGE_BG)

sns.scatterplot(
    data=df,
    x=GDP,
    y=LIFE_EXPECTANCY,
    s=110,
    alpha=0.7,
    color=IMPRINT_PALETTE[0],
    edgecolor=PAGE_BG,
    linewidth=0.8,
    ax=ax,
)
ax.set_xscale("log")
ax.margins(x=0.12, y=0.16)

# Each label tries eight positions around its marker and keeps the one that overlaps the
# fewest markers, earlier labels and axes edges; only text moves, markers stay at their values
LABEL_SIZE = 8
GAP = 7  # distance between marker center and label anchor, in points
CANDIDATES = [  # (dx, dy, ha, va) in points, in order of preference
    (GAP, 0, "left", "center"),
    (-GAP, 0, "right", "center"),
    (0, GAP, "center", "bottom"),
    (0, -GAP, "center", "top"),
    (GAP, GAP, "left", "bottom"),
    (-GAP, GAP, "right", "bottom"),
    (GAP, -GAP, "left", "top"),
    (-GAP, -GAP, "right", "top"),
    (2 * GAP, 2 * GAP, "left", "bottom"),
    (-2 * GAP, 2 * GAP, "right", "bottom"),
    (2 * GAP, -2 * GAP, "left", "top"),
    (-2 * GAP, -2 * GAP, "right", "top"),
]
fig.canvas.draw()
renderer = fig.canvas.get_renderer()
marker_px = 6 * fig.dpi / 72  # marker radius plus a little air, in pixels
centers = ax.transData.transform(df[[GDP, LIFE_EXPECTANCY]].to_numpy())
axes_box = ax.get_window_extent()


def overlap(a, b):
    w = min(a.x1, b.x1) - max(a.x0, b.x0)
    h = min(a.y1, b.y1) - max(a.y0, b.y0)
    return w * h if w > 0 and h > 0 else 0.0


boxes = []
for idx in df[LIFE_EXPECTANCY].sort_values(ascending=False).index:
    best = None
    for rank, (dx, dy, ha, va) in enumerate(CANDIDATES):
        label = ax.annotate(
            df.loc[idx, COUNTRY],
            xy=(df.loc[idx, GDP], df.loc[idx, LIFE_EXPECTANCY]),
            xytext=(dx, dy),
            textcoords="offset points",
            fontsize=LABEL_SIZE,
            color=INK_SOFT,
            ha=ha,
            va=va,
            arrowprops={"arrowstyle": "-", "color": INK_SOFT, "alpha": 0.5, "lw": 0.6, "shrinkA": 1, "shrinkB": 4},
        )
        box = label.get_window_extent(renderer)
        cost = rank * 0.01 + sum(overlap(box, other) for other in boxes) * 10
        for cx, cy in centers:
            cost += overlap(box, type(box)([[cx - marker_px, cy - marker_px], [cx + marker_px, cy + marker_px]])) * 10
        cost += (box.width * box.height - overlap(box, axes_box)) * 50
        if best is None or cost < best[0]:
            if best is not None:
                best[1].remove()
            best = (cost, label, box)
        else:
            label.remove()
    boxes.append(best[2])

# Style
title = "scatter-annotated · python · seaborn · anyplot.ai"
ax.set_title(title, fontsize=12, fontweight="medium", color=INK)
ax.set_xlabel(GDP, fontsize=10)
ax.set_ylabel(LIFE_EXPECTANCY, fontsize=10)
ax.tick_params(axis="both", labelsize=8)
ax.set_xticks([1, 3, 10, 30, 100], ["1", "3", "10", "30", "100"])
ax.yaxis.grid(True, alpha=0.15, linewidth=0.6)
sns.despine(ax=ax)

plt.savefig(f"plot-{THEME}.png", dpi=400, facecolor=PAGE_BG)
