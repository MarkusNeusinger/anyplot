""" anyplot.ai
network-bipartite: Bipartite Network Graph
Library: matplotlib 3.11.2 | Python 3.14.10
Quality: 85/100 | Updated: 2026-11-21
"""

import os

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

# Imprint palette: all eight positions, one per node set in order
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

# Columns: set these to your table's column names
AUTHOR = "Researcher"  # role: source
PAPER = "Paper"  # role: target

# Data: replace this block with your own edge list, for example df = pd.read_csv("links.csv")
# Researcher-paper affiliation network (bibliometrics): one row per authorship
authorship = {
    "Chen, L.": ["Deep Learning", "Vision Models", "Attention Mech.", "Robustness"],
    "Smith, A.": ["NLP Survey", "RL Methods", "Explainability"],
    "Patel, R.": ["Graph Neural Nets", "Transfer Learning", "Recommenders"],
    "Kim, J.": ["Deep Learning", "Vision Models", "AutoML", "Optimization"],
    "Müller, K.": ["Transfer Learning", "Attention Mech.", "Federated Learn.", "Fairness in ML"],
    "Johnson, E.": ["NLP Survey", "Explainability", "Causal Inference", "Fairness in ML", "Time Series ML"],
    "Santos, M.": ["Generative AI", "Recommenders", "Multi-modal"],
    "Tanaka, H.": ["RL Methods", "Attention Mech.", "AutoML", "Robustness"],
    "Williams, P.": ["RL Methods", "Optimization", "Time Series ML"],
    "Okonkwo, F.": ["Vision Models", "Generative AI", "Multi-modal"],
    "Larsson, B.": ["Graph Neural Nets", "Federated Learn.", "Time Series ML"],
    "Ahmed, S.": ["Deep Learning", "NLP Survey", "Transfer Learning", "Causal Inference"],
}
df = pd.DataFrame(
    [(author, paper) for author, titles in authorship.items() for paper in titles], columns=[AUTHOR, PAPER]
)

# Plot: reads only df and the constants above
authors = df[AUTHOR].unique()
papers = df[PAPER].unique()
author_degree = df.groupby(AUTHOR)[PAPER].count().reindex(authors).to_numpy()
paper_degree = df.groupby(PAPER)[AUTHOR].count().reindex(papers).to_numpy()

# Layout: two columns, nodes evenly spaced from top to bottom
author_y = dict(zip(authors, np.linspace(0.90, 0.05, len(authors)), strict=True))
paper_y = dict(zip(papers, np.linspace(0.90, 0.05, len(papers)), strict=True))
top = max(max(author_y.values()), max(paper_y.values()))
bottom = min(min(author_y.values()), min(paper_y.values()))

fig, ax = plt.subplots(figsize=(8, 4.5), dpi=400, facecolor=PAGE_BG)
ax.set_facecolor(PAGE_BG)

# Edges: straight, thin and light
for author, paper in zip(df[AUTHOR], df[PAPER], strict=True):
    ax.plot([0.0, 1.0], [author_y[author], paper_y[paper]], color=INK_SOFT, alpha=0.3, linewidth=0.5, zorder=1)

# Nodes: size grows with degree
ax.scatter(
    np.zeros(len(authors)),
    list(author_y.values()),
    s=40 + author_degree * 24,
    c=IMPRINT_PALETTE[0],
    edgecolors=PAGE_BG,
    linewidth=0.8,
    zorder=3,
)
ax.scatter(
    np.ones(len(papers)),
    list(paper_y.values()),
    s=40 + paper_degree * 24,
    c=IMPRINT_PALETTE[1],
    marker="s",
    edgecolors=PAGE_BG,
    linewidth=0.8,
    zorder=3,
)

# Node labels on the outer side of each column
for author, y in author_y.items():
    ax.text(-0.03, y, author, ha="right", va="center", fontsize=8, color=INK_SOFT)
for paper, y in paper_y.items():
    ax.text(1.03, y, paper, ha="left", va="center", fontsize=8, color=INK_SOFT)

# Column headers
header_y = top + 0.05
ax.text(
    0.0, header_y, "Researchers", ha="center", va="bottom", fontsize=11, fontweight="bold", color=IMPRINT_PALETTE[0]
)
ax.text(1.0, header_y, "Papers", ha="center", va="bottom", fontsize=11, fontweight="bold", color=IMPRINT_PALETTE[1])

# Legend
handles = [
    Line2D(
        [0],
        [0],
        marker="o",
        linestyle="none",
        markerfacecolor=IMPRINT_PALETTE[0],
        markeredgecolor=PAGE_BG,
        markersize=7,
        label="Researcher (size = no. of papers)",
    ),
    Line2D(
        [0],
        [0],
        marker="s",
        linestyle="none",
        markerfacecolor=IMPRINT_PALETTE[1],
        markeredgecolor=PAGE_BG,
        markersize=7,
        label="Paper (size = no. of authors)",
    ),
    Line2D([0], [0], color=INK_SOFT, linewidth=1.2, alpha=0.6, label="Authorship link"),
]
leg = ax.legend(handles=handles, loc="lower center", ncol=3, fontsize=8, frameon=True, bbox_to_anchor=(0.5, -0.02))
leg.get_frame().set_facecolor(ELEVATED_BG)
leg.get_frame().set_edgecolor(INK_SOFT)
plt.setp(leg.get_texts(), color=INK_SOFT)

# Style
ax.set_title("network-bipartite · python · matplotlib · anyplot.ai", fontsize=12, fontweight="medium", color=INK, pad=8)
ax.set_xlim(-0.48, 1.48)
ax.set_ylim(bottom - 0.12, header_y + 0.1)
ax.axis("off")

fig.subplots_adjust(left=0.02, right=0.98, top=0.93, bottom=0.02)
plt.savefig(f"plot-{THEME}.png", dpi=400, facecolor=PAGE_BG)
