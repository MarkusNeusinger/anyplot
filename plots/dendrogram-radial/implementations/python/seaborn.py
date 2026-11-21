"""anyplot.ai
dendrogram-radial: Radial Dendrogram
Library: seaborn 0.13.2 | Python 3.13.13
Quality: 81/100 | Updated: 2026-11-21
"""

import os

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
from scipy.cluster.hierarchy import dendrogram, linkage
from scipy.spatial.distance import pdist


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
INK_MUTED = "#6B6A63" if THEME == "light" else "#A8A79F"

# Imprint palette: all eight positions, one per instrument family in order
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

sns.set_theme(
    style="white",
    rc={
        "figure.facecolor": PAGE_BG,
        "axes.facecolor": PAGE_BG,
        "axes.edgecolor": INK_SOFT,
        "text.color": INK,
        "xtick.color": INK_SOFT,
        "ytick.color": INK_SOFT,
    },
)

# Columns: set these to your table's column names
INSTRUMENT = "Instrument"  # role: labels
FAMILY = "Instrument family"  # role: clusters

# Data: replace this block with your own table, for example df = pd.read_csv("instruments.csv");
# every column other than the two above is read as a numeric feature the tree is built from
feature_names = [f"Acoustic feature {i}" for i in range(1, 13)]
rng = np.random.default_rng(7)
families = {
    "Strings": ["Violin", "Viola", "Cello", "Double Bass", "Harp", "Guitar"],
    "Woodwinds": ["Flute", "Oboe", "Clarinet", "Bassoon", "Piccolo", "Saxophone"],
    "Brass": ["Trumpet", "French Horn", "Trombone", "Tuba", "Cornet", "Euphonium"],
    "Percussion": ["Timpani", "Snare Drum", "Cymbals", "Xylophone", "Triangle", "Marimba"],
    "Keyboards": ["Piano", "Organ", "Harpsichord", "Celesta", "Accordion", "Synthesizer"],
}
centers = rng.normal(0, 4, size=(len(families), len(feature_names)))
rows = []
for center, (family, names) in zip(centers, families.items(), strict=False):
    for name in names:
        rows.append(
            {
                INSTRUMENT: name,
                FAMILY: family,
                **dict(zip(feature_names, center + rng.normal(0, 0.8, len(feature_names)), strict=False)),
            }
        )
df = pd.DataFrame(rows)

# Plot: reads only df and the constants above
n_leaves = len(df)
family_names = list(pd.unique(df[FAMILY]))
family_code = df[FAMILY].map({name: i for i, name in enumerate(family_names)}).to_numpy()
fam_colors = dict(zip(family_names, IMPRINT_PALETTE, strict=False)) if len(family_names) <= len(IMPRINT_PALETTE) else {}
features = df.drop(columns=[INSTRUMENT, FAMILY]).apply(lambda col: col.fillna(col.mean()))

# Ward linkage on the feature profiles; leaf order and U-shapes come from the tree
Z = linkage(pdist(features.to_numpy(), metric="euclidean"), method="ward")
dend = dendrogram(Z, no_plot=True)
icoord = np.array(dend["icoord"])
dcoord = np.array(dend["dcoord"])
leaf_order = dend["leaves"]

# Node colors: a subtree inside one family takes its color, a mixed one stays neutral
members = [{int(c)} for c in family_code]
for a, b in Z[:, :2].astype(int):
    members.append(members[a] | members[b])
node_color = [IMPRINT_PALETTE[next(iter(m))] if len(m) == 1 else INK_SOFT for m in members]

# Radial mapping: merge distance -> radius (root inside, leaves outside), leaf position -> angle
R_LEAF, R_ROOT = 0.74, 0.10
x_max = 10.0 * n_leaves
y_max = float(dcoord.max())
theta_of = lambda x: x / x_max * 2 * np.pi  # noqa: E731
radius_of = lambda y: R_LEAF - (y / y_max) * (R_LEAF - R_ROOT)  # noqa: E731

fig = plt.figure(figsize=(6, 6), dpi=400, facecolor=PAGE_BG)
ax = fig.add_subplot(111, projection="polar")
ax.set_theta_zero_location("N")
ax.set_theta_direction(-1)

# Each U-shape: two radial bars plus one arc at the merge radius; U-shapes come in merge order
merge_row = np.argsort(np.argsort(dcoord[:, 1], kind="stable"), kind="stable")
for (ic, dc), row in zip(zip(icoord, dcoord, strict=False), merge_row, strict=False):
    left, right = int(Z[row, 0]), int(Z[row, 1])
    t_left, t_right = theta_of(ic[0]), theta_of(ic[3])
    r_top = radius_of(dc[1])
    ax.plot([t_left, t_left], [radius_of(dc[0]), r_top], color=node_color[left], lw=1.4, solid_capstyle="round")
    ax.plot([t_right, t_right], [radius_of(dc[3]), r_top], color=node_color[right], lw=1.4, solid_capstyle="round")
    n_pts = max(3, int(abs(t_right - t_left) * 40 / np.pi))
    ax.plot(
        np.linspace(t_left, t_right, n_pts),
        np.full(n_pts, r_top),
        color=node_color[n_leaves + row],
        lw=1.4,
        solid_capstyle="round",
    )

# Leaf dots through seaborn, hue = instrument family
leaf_angle = theta_of(10.0 * np.arange(n_leaves) + 5)
leaves = pd.DataFrame({"angle": leaf_angle, "radius": R_LEAF, FAMILY: df[FAMILY].to_numpy()[leaf_order]})
sns.scatterplot(
    data=leaves,
    x="angle",
    y="radius",
    hue=FAMILY,
    hue_order=family_names,
    palette=IMPRINT_PALETTE[: len(family_names)],
    s=26,
    linewidth=0,
    legend=False,
    zorder=5,
    ax=ax,
)

# Instrument names just outside the rim, rotated along their branch
for angle, leaf in zip(leaf_angle, leaf_order, strict=False):
    deg = np.degrees(angle) % 360
    right_half = deg < 180
    ax.text(
        angle,
        R_LEAF + 0.04,
        df[INSTRUMENT].iloc[leaf],
        ha="left" if right_half else "right",
        va="center",
        fontsize=8,
        color=IMPRINT_PALETTE[family_code[leaf]],
        rotation=90 - deg if right_half else 270 - deg,
        rotation_mode="anchor",
    )

# Family names on the outer ring, at the angular centre of each family's leaves
for code, name in enumerate(family_names):
    positions = np.flatnonzero(family_code[leaf_order] == code)
    angle = theta_of(10.0 * positions.mean() + 5)
    deg = np.degrees(angle) % 360
    ax.text(
        angle,
        R_LEAF + 0.38,
        name,
        ha="center",
        va="center",
        fontsize=11,
        fontweight="bold",
        color=IMPRINT_PALETTE[code],
        rotation=-deg if (deg <= 90 or deg >= 270) else 180 - deg,
        rotation_mode="anchor",
    )

# Style
ax.set_ylim(0, R_LEAF + 0.52)
ax.set_xlabel("")
ax.set_ylabel("")
ax.set_xticks([])
ax.set_yticks([])
ax.spines["polar"].set_visible(False)
ax.grid(False)
fig.subplots_adjust(left=0.02, right=0.98, bottom=0.07, top=0.93)

title = "dendrogram-radial · python · seaborn · anyplot.ai"
fig.text(0.5, 0.975, title, ha="center", va="top", fontsize=12, fontweight="medium", color=INK)
fig.text(
    0.5,
    0.02,
    f"Ward linkage · {n_leaves} instruments × {len(family_names)} families · Euclidean distance on {features.shape[1]} acoustic features",
    ha="center",
    va="bottom",
    fontsize=8,
    color=INK_MUTED,
)

plt.savefig(f"plot-{THEME}.png", dpi=400, facecolor=PAGE_BG)
