""" anyplot.ai
network-weighted: Weighted Network Graph with Edge Thickness
Library: matplotlib 3.11.2 | Python 3.14.10
Quality: 82/100 | Updated: 2026-11-22
"""

import os

import matplotlib.patheffects as pe
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.lines import Line2D


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Imprint palette: all eight positions, one per group in order
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

# Constants
LINE_RANGE = (1.2, 9.0)  # edge width in points for the lightest and the heaviest link
NODE_RANGE = (130, 800)  # node area in points squared for the lowest and the highest weighted degree

# Columns: set these to your table's column names
ENDPOINTS = ["Institute A", "Institute B"]  # role: edges
PAPERS = "Co-authored papers"  # role: weight
INSTITUTE = "Institute"  # role: nodes
FOCUS = "Research focus"  # role: extra

# Data: replace this block with your own edge list and node table, for example df = pd.read_csv("links.csv")
focus_of = {
    "CERN": "Particle physics",
    "DESY": "Particle physics",
    "FNAL": "Particle physics",
    "KEK": "Particle physics",
    "EMBL": "Life sciences",
    "Broad": "Life sciences",
    "Pasteur": "Life sciences",
    "Sanger": "Life sciences",
    "PIK": "Climate science",
    "NCAR": "Climate science",
    "AWI": "Climate science",
    "MILA": "Computing",
    "CSAIL": "Computing",
    "ETH AI": "Computing",
}
nodes = pd.DataFrame({INSTITUTE: list(focus_of), FOCUS: list(focus_of.values())})
links = [
    ("CERN", "DESY", 410),
    ("CERN", "FNAL", 380),
    ("CERN", "KEK", 190),
    ("DESY", "FNAL", 120),
    ("DESY", "KEK", 85),
    ("FNAL", "KEK", 60),
    ("CERN", "ETH AI", 70),
    ("FNAL", "CSAIL", 45),
    ("EMBL", "Broad", 300),
    ("EMBL", "Sanger", 340),
    ("EMBL", "Pasteur", 210),
    ("Broad", "Sanger", 180),
    ("Broad", "Pasteur", 95),
    ("Sanger", "Pasteur", 110),
    ("Broad", "CSAIL", 130),
    ("EMBL", "ETH AI", 55),
    ("Pasteur", "MILA", 25),
    ("PIK", "NCAR", 230),
    ("PIK", "AWI", 270),
    ("NCAR", "AWI", 90),
    ("AWI", "EMBL", 35),
    ("NCAR", "CSAIL", 40),
    ("PIK", "ETH AI", 65),
    ("MILA", "CSAIL", 240),
    ("MILA", "ETH AI", 150),
    ("CSAIL", "ETH AI", 100),
    ("DESY", "ETH AI", 50),
    ("KEK", "MILA", 20),
]
df = pd.DataFrame(links, columns=[*ENDPOINTS, PAPERS])

# Plot: reads only df, nodes and the constants above
names = list(nodes[INSTITUTE])
index = {name: i for i, name in enumerate(names)}
src = df[ENDPOINTS[0]].map(index).to_numpy()
tgt = df[ENDPOINTS[1]].map(index).to_numpy()
papers = df[PAPERS].to_numpy(dtype=float)
span = papers.max() - papers.min()
share = (papers - papers.min()) / span if span > 0 else np.full(len(papers), 0.5)
widths = LINE_RANGE[0] + share * (LINE_RANGE[1] - LINE_RANGE[0])


def line_width(count):
    """Edge width in points for a paper count, the same mapping the edges use."""
    frac = (count - papers.min()) / span if span > 0 else 0.5
    return LINE_RANGE[0] + frac * (LINE_RANGE[1] - LINE_RANGE[0])


# Weighted degree: total papers on all links of an institute
degree = np.bincount(src, weights=papers, minlength=len(names)) + np.bincount(tgt, weights=papers, minlength=len(names))
sizes = NODE_RANGE[0] + degree / degree.max() * (NODE_RANGE[1] - NODE_RANGE[0])

# Force-directed layout (Fruchterman-Reingold): heavier links pull harder
rng = np.random.default_rng(19)
pos = rng.random((len(names), 2))
k = 1 / np.sqrt(len(names))
step = 0.1
for _ in range(400):
    delta = pos[:, None, :] - pos[None, :, :]
    dist = np.maximum(np.linalg.norm(delta, axis=2), 1e-3)
    move = (delta / dist[..., None] * (5 * k * k / dist)[..., None]).sum(axis=1)
    for a, b, w in zip(src, tgt, papers / papers.max(), strict=True):
        d = pos[a] - pos[b]
        length = max(np.linalg.norm(d), 1e-3)
        pull = d / length * length * length / k * (0.2 + 0.5 * w)
        move[a] -= pull
        move[b] += pull
    norm = np.maximum(np.linalg.norm(move, axis=1), 1e-3)
    pos += move / norm[:, None] * np.minimum(norm, step)[:, None]
    step *= 0.98
unit = (pos - pos.min(axis=0)) / (pos.max(axis=0) - pos.min(axis=0))
pos = np.array([0.27, 0.10]) + unit * np.array([0.69, 0.76])  # left column stays free for the legends

groups = list(dict.fromkeys(nodes[FOCUS]))
colors = [IMPRINT_PALETTE[groups.index(g)] for g in nodes[FOCUS]]

fig, ax = plt.subplots(figsize=(8, 4.5), dpi=400, facecolor=PAGE_BG)
ax.set_facecolor(PAGE_BG)

# Edges first, nodes and labels on top
for a, b, w in zip(src, tgt, widths, strict=True):
    ax.plot(
        [pos[a, 0], pos[b, 0]],
        [pos[a, 1], pos[b, 1]],
        color=INK_SOFT,
        linewidth=w,
        alpha=0.55,
        solid_capstyle="round",
        zorder=1,
    )
ax.scatter(pos[:, 0], pos[:, 1], s=sizes, c=colors, edgecolors=PAGE_BG, linewidths=1.2, zorder=2)
for i, name in enumerate(names):
    ax.annotate(
        name,
        pos[i],
        xytext=(0, np.sqrt(sizes[i]) / 2 + 3),
        textcoords="offset points",
        ha="center",
        va="bottom",
        fontsize=7,
        fontweight="bold",
        color=INK,
        path_effects=[pe.withStroke(linewidth=2.2, foreground=PAGE_BG)],
        zorder=3,
    )

# Legend 1: node color = research focus
focus_handles = [
    Line2D(
        [],
        [],
        marker="o",
        linestyle="",
        markersize=8,
        markerfacecolor=IMPRINT_PALETTE[i],
        markeredgecolor=PAGE_BG,
        label=g,
    )
    for i, g in enumerate(groups)
]
focus_legend = ax.legend(
    handles=focus_handles, title=FOCUS, loc="upper left", fontsize=7, title_fontsize=8, framealpha=0.95, borderpad=0.8
)
ax.add_artist(focus_legend)

# Legend 2: edge thickness = co-authored papers, sample widths labeled with their counts
samples = np.unique(np.round(np.linspace(papers.min(), papers.max(), len(LINE_RANGE) + 1), -1)).astype(int)
weight_handles = [
    Line2D([], [], color=INK_SOFT, alpha=0.55, linewidth=line_width(s), solid_capstyle="round", label=f"{s} papers")
    for s in samples
]
weight_legend = ax.legend(
    handles=weight_handles,
    title="Edge thickness",
    loc="lower left",
    fontsize=7,
    title_fontsize=8,
    framealpha=0.95,
    borderpad=0.8,
    labelspacing=0.9,
    handlelength=3,
)
for leg in (focus_legend, weight_legend):
    leg.get_frame().set_facecolor(ELEVATED_BG)
    leg.get_frame().set_edgecolor(INK_SOFT)
    plt.setp(leg.get_texts(), color=INK_SOFT)
    plt.setp(leg.get_title(), color=INK_SOFT)

# Node size caption
ax.annotate(
    "Node size: total co-authored papers",
    xy=(0.99, 0.02),
    xycoords="axes fraction",
    ha="right",
    va="bottom",
    fontsize=7,
    color=INK_SOFT,
    style="italic",
)

# Style
ax.set_title(
    "Research collaboration · network-weighted · python · matplotlib · anyplot.ai",
    fontsize=10,
    fontweight="medium",
    color=INK,
)
ax.set_xlim(0, 1)
ax.set_ylim(0, 1)
ax.axis("off")
plt.savefig(f"plot-{THEME}.png", dpi=400, facecolor=PAGE_BG)
