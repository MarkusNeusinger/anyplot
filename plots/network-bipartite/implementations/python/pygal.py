"""anyplot.ai
network-bipartite: Bipartite Network Graph
Library: pygal 3.1.0 | Python 3.13.13
Quality: pending | Updated: 2026-11-21
"""

import os

import numpy as np
import pandas as pd
import pygal
from pygal.style import Style


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_MUTED = "#6B6A63" if THEME == "light" else "#A8A79F"
EDGE = "#8A897F" if THEME == "light" else "#7C7B73"

# Imprint palette: all eight positions, one per node set in order
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

# Constants
MIN_RADIUS = 14  # node radius (px) of a node with a single connection
RADIUS_PER_LINK = 9  # extra radius (px) for each further connection

# Columns: set these to your table's column names
AUTHOR = "Author"  # role: source
PAPER = "Paper"  # role: target

# Data: replace this block with your own edge list, for example df = pd.read_csv("collaborations.csv")
df = pd.DataFrame(
    [
        (author, paper)
        for author, papers in {
            "Smith": ["P01", "P02", "P05", "P07", "P09"],
            "Zhang": ["P01", "P03", "P07"],
            "Patel": ["P02", "P04", "P06", "P08", "P09", "P10"],
            "Mueller": ["P03", "P05", "P09"],
            "Garcia": ["P04", "P06", "P10"],
            "Kim": ["P07", "P08", "P09"],
            "Okonkwo": ["P01", "P05", "P10"],
            "Novak": ["P06", "P09", "P10"],
        }.items()
        for paper in papers
    ],
    columns=[AUTHOR, PAPER],
)

# Plot: layout and node sizes derived from the edge list
authors = list(dict.fromkeys(df[AUTHOR]))
papers = sorted(dict.fromkeys(df[PAPER]))
degree = {**df[AUTHOR].value_counts().to_dict(), **df[PAPER].value_counts().to_dict()}


def column(nodes):
    """Spread a column of nodes evenly over 0..1, first node on top."""
    return dict(zip(nodes, np.linspace(1, 0, len(nodes)), strict=True))


author_y, paper_y = column(authors), column(papers)
LEFT_X, RIGHT_X = 0.0, 1.0
LABEL_GAP = 0.27  # left labels start this far left of the authors


LABEL_LIFT = 0.03


def radius(node):
    return MIN_RADIUS + RADIUS_PER_LINK * (degree[node] - 1)


def node_points(nodes, x, y):
    return [{"value": (x, y[n]), "node": {"r": radius(n)}} for n in nodes]


def label_points(nodes, x, y):
    return [{"value": (x, y[n] + LABEL_LIFT), "label": f"{n} ({degree[n]})", "node": {"r": 0}} for n in nodes]


edge_points = []
for author, paper in zip(df[AUTHOR], df[PAPER], strict=True):
    edge_points += [(LEFT_X, author_y[author]), (RIGHT_X, paper_y[paper]), None]

title = "network-bipartite · python · pygal · anyplot.ai"
style = Style(
    background=PAGE_BG,
    plot_background=PAGE_BG,
    foreground=INK,
    foreground_strong=INK,
    foreground_subtle=INK_MUTED,
    colors=(EDGE, IMPRINT_PALETTE[0], IMPRINT_PALETTE[1], PAGE_BG),
    title_font_size=66,
    label_font_size=44,
    major_label_font_size=44,
    legend_font_size=44,
    value_font_size=44,
    value_label_font_size=44,
    stroke_width=2,
    opacity=0.55,
    opacity_hover=0.9,
)

chart = pygal.XY(
    style=style,
    width=3200,
    height=1800,
    title=title,
    show_x_guides=False,
    show_y_guides=False,
    show_x_labels=False,
    show_y_labels=False,
    xrange=(-0.55, 1.4),
    range=(-0.06, 1.14),
    print_labels=True,
    show_legend=False,
    margin=40,
)

# Edges first so the nodes sit on top; dots hidden on this series
chart.add("Collaboration link", edge_points, show_dots=False, stroke_style={"width": 4})
chart.add("Authors", node_points(authors, LEFT_X, author_y), stroke=False, dots_size=1)
chart.add("Papers", node_points(papers, RIGHT_X, paper_y), stroke=False, dots_size=1)

# Invisible label carriers: pygal prints a label starting at its point and just below it,
# so the points sit left of the authors and right of the papers, lifted by half a text line
chart.add(
    "Labels",
    label_points(authors, LEFT_X - LABEL_GAP, author_y)
    + label_points(papers, RIGHT_X + 0.05, paper_y)
    + [
        {"value": (LEFT_X - LABEL_GAP - 0.06, 1.1), "label": "AUTHORS (size = papers)", "node": {"r": 0}},
        {"value": (RIGHT_X + 0.05 - 0.06, 1.1), "label": "PAPERS (size = authors)", "node": {"r": 0}},
    ],
    stroke=False,
    dots_size=0,
)

# Save
chart.render_to_png(f"plot-{THEME}.png")
with open(f"plot-{THEME}.html", "wb") as f:
    f.write(chart.render())
