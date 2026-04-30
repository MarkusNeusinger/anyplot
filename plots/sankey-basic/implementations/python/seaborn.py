"""anyplot.ai
sankey-basic: Basic Sankey Diagram
Library: seaborn | Python 3.13
Quality: 78/100 | Created: 2025-12-23
"""

import os

import matplotlib.patches as mpatches
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"

OKABE_ITO = ["#009E73", "#D55E00", "#0072B2", "#CC79A7", "#E69F00", "#56B4E9"]

sns.set_theme(style="white", rc={"figure.facecolor": PAGE_BG, "axes.facecolor": PAGE_BG, "text.color": INK})

# Data — energy flows in TWh (varied magnitudes for clear proportional scaling)
source_names = ["Gas", "Coal", "Nuclear"]
target_names = ["Residential", "Industrial", "Commercial"]
flows = [
    ("Gas", "Residential", 50),
    ("Gas", "Industrial", 30),
    ("Gas", "Commercial", 40),
    ("Coal", "Industrial", 45),
    ("Coal", "Residential", 20),
    ("Coal", "Commercial", 15),
    ("Nuclear", "Residential", 25),
    ("Nuclear", "Industrial", 10),
    ("Nuclear", "Commercial", 10),
]
df = pd.DataFrame(flows, columns=["source", "target", "value"])

source_colors = dict(zip(source_names, OKABE_ITO[:3], strict=True))
target_colors = dict(zip(target_names, OKABE_ITO[3:6], strict=True))

sources = df.groupby("source")["value"].sum().loc[source_names]
targets = df.groupby("target")["value"].sum().loc[target_names]

# Layout
NODE_W = 0.055
X_LEFT, X_RIGHT = 0.13, 0.87
GAP = 0.022
TOTAL_H = 0.70
Y_START = 0.93

source_pos = {}
y = Y_START
for name in source_names:
    h = (sources[name] / sources.sum()) * TOTAL_H
    source_pos[name] = {"y": y - h, "h": h}
    y -= h + GAP

target_pos = {}
y = Y_START
for name in target_names:
    h = (targets[name] / targets.sum()) * TOTAL_H
    target_pos[name] = {"y": y - h, "h": h}
    y -= h + GAP

src_y = {n: source_pos[n]["y"] + source_pos[n]["h"] for n in source_names}
tgt_y = {n: target_pos[n]["y"] + target_pos[n]["h"] for n in target_names}

# Figure
fig, ax = plt.subplots(figsize=(16, 9), facecolor=PAGE_BG)
ax.set_facecolor(PAGE_BG)

t = np.linspace(0, 1, 120)
s = t**2 * (3 - 2 * t)  # smoothstep: zero tangents at both endpoints

# Sort flows by source order then target order to minimise crossings
src_ord = {n: i for i, n in enumerate(source_names)}
tgt_ord = {n: i for i, n in enumerate(target_names)}
df["_si"] = df["source"].map(src_ord)
df["_ti"] = df["target"].map(tgt_ord)
df_sorted = df.sort_values(["_si", "_ti"])

# Draw flows
for _, row in df_sorted.iterrows():
    src, tgt, val = row["source"], row["target"], row["value"]
    bh_src = (val / sources[src]) * source_pos[src]["h"]
    bh_tgt = (val / targets[tgt]) * target_pos[tgt]["h"]

    y0t, y0b = src_y[src], src_y[src] - bh_src
    src_y[src] = y0b
    y1t, y1b = tgt_y[tgt], tgt_y[tgt] - bh_tgt
    tgt_y[tgt] = y1b

    x0, x1 = X_LEFT + NODE_W, X_RIGHT
    cx0, cx1 = x0 + (x1 - x0) * 0.35, x0 + (x1 - x0) * 0.65
    xs = (1 - t) ** 3 * x0 + 3 * (1 - t) ** 2 * t * cx0 + 3 * (1 - t) * t**2 * cx1 + t**3 * x1

    ax.fill_between(xs, y0b + (y1b - y0b) * s, y0t + (y1t - y0t) * s, color=source_colors[src], alpha=0.55, linewidth=0)

# Draw source nodes and labels
for name in source_names:
    pos = source_pos[name]
    ax.add_patch(
        mpatches.FancyBboxPatch(
            (X_LEFT, pos["y"]),
            NODE_W,
            pos["h"],
            boxstyle="round,pad=0.005,rounding_size=0.015",
            facecolor=source_colors[name],
            edgecolor=PAGE_BG,
            linewidth=2,
        )
    )
    ax.text(
        X_LEFT - 0.015,
        pos["y"] + pos["h"] / 2,
        f"{name}\n{sources[name]:.0f} TWh",
        ha="right",
        va="center",
        fontsize=18,
        fontweight="bold",
        color=INK,
    )

# Draw target nodes and labels
for name in target_names:
    pos = target_pos[name]
    ax.add_patch(
        mpatches.FancyBboxPatch(
            (X_RIGHT, pos["y"]),
            NODE_W,
            pos["h"],
            boxstyle="round,pad=0.005,rounding_size=0.015",
            facecolor=target_colors[name],
            edgecolor=PAGE_BG,
            linewidth=2,
        )
    )
    ax.text(
        X_RIGHT + NODE_W + 0.015,
        pos["y"] + pos["h"] / 2,
        f"{name}\n{targets[name]:.0f} TWh",
        ha="left",
        va="center",
        fontsize=18,
        fontweight="bold",
        color=INK,
    )

ax.set_title("sankey-basic · seaborn · anyplot.ai", fontsize=24, fontweight="medium", color=INK, pad=20)
ax.set_xlim(0, 1)
ax.set_ylim(0, 1)
ax.axis("off")

plt.tight_layout()
plt.savefig(f"plot-{THEME}.png", dpi=300, bbox_inches="tight", facecolor=PAGE_BG)
