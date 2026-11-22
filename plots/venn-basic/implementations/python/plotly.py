"""anyplot.ai
venn-basic: Venn Diagram
Library: plotly | Python 3.13
"""

import os
from itertools import combinations

import numpy as np
import pandas as pd
import plotly.graph_objects as go


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Imprint palette: all eight positions, one per set in order
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

# Constants
SEPARATOR = " & "  # joins set names in the name of an overlap
FILL_ALPHA = 0.45  # translucency of each circle, so overlaps read as blends

# Columns: set these to your table's column names
SETS = "Sets"  # role: set_labels
SIZE = "Set size"  # role: set_sizes
OVERLAP = "Overlap size"  # role: intersections

# Data: replace this block with your own table, for example df = pd.read_csv("sets.csv")
# One row per set (its size) or per overlap (its size, inclusive: AWS & Azure also counts the triple overlap).
# Cloud platforms used by 100, 80 and 60 companies in a survey of engineering teams.
df = pd.DataFrame(
    {
        SETS: ["AWS", "Azure", "GCP", "AWS & Azure", "AWS & GCP", "Azure & GCP", "AWS & Azure & GCP"],
        SIZE: [100, 80, 60, None, None, None, None],
        OVERLAP: [None, None, None, 30, 20, 25, 10],
    }
)

# Plot: reads only df and the constants above
sizes = pd.to_numeric(df[SIZE].fillna(df[OVERLAP]), errors="coerce")
members = [tuple(str(name).split(SEPARATOR)) for name in df[SETS]]
inclusive = {frozenset(m): float(s) for m, s in zip(members, sizes, strict=True) if pd.notna(s)}
names = list(dict.fromkeys(m[0] for m in members if len(m) == 1 and frozenset(m) in inclusive))
n = len(names)
size_of = {name: inclusive[frozenset([name])] for name in names}
radii = np.sqrt(np.array([size_of[name] for name in names]) / np.pi)

# Exclusive count of each region by inclusion-exclusion over the inclusive sizes
exclusive = {}
for k in range(1, n + 1):
    for region in combinations(range(n), k):
        total = 0.0
        for j in range(k, n + 1):
            for sup in combinations(range(n), j):
                if set(region) <= set(sup):
                    total += (-1) ** (j - k) * inclusive.get(frozenset(names[i] for i in sup), 0.0)
        exclusive[region] = total


def lens_area(r1, r2, d):
    """Overlap area of two circles whose centres are d apart."""
    if d >= r1 + r2:
        return 0.0
    if d <= abs(r1 - r2):
        return np.pi * min(r1, r2) ** 2
    a1 = r1**2 * np.arccos((d**2 + r1**2 - r2**2) / (2 * d * r1))
    a2 = r2**2 * np.arccos((d**2 + r2**2 - r1**2) / (2 * d * r2))
    return a1 + a2 - 0.5 * np.sqrt((-d + r1 + r2) * (d + r1 - r2) * (d - r1 + r2) * (d + r1 + r2))


def centre_distance(i, j):
    """Distance at which circles i and j overlap by their pairwise intersection (bisection)."""
    target = inclusive.get(frozenset([names[i], names[j]]), 0.0) / np.pi
    low, high = abs(radii[i] - radii[j]), radii[i] + radii[j]
    for _ in range(60):
        mid = (low + high) / 2
        low, high = (mid, high) if lens_area(radii[i], radii[j], mid) > target else (low, mid)
    return (low + high) / 2


# Circle centres: set 0 at the origin, set 1 on the x axis, set 2 from the two remaining distances
centres = np.zeros((n, 2))
if n > 1:
    centres[1] = [centre_distance(0, 1), 0.0]
if n > 2:
    d01, d02, d12 = centre_distance(0, 1), centre_distance(0, 2), centre_distance(1, 2)
    x2 = (d02**2 - d12**2 + d01**2) / (2 * d01)
    centres[2] = [x2, -np.sqrt(max(d02**2 - x2**2, 0.0))]

# Region masks on a fine grid give each region's label position (its centroid)
pad = 1.15
lo = (centres - radii[:, None]).min(axis=0) - pad
hi = (centres + radii[:, None]).max(axis=0) + pad
gx, gy = np.meshgrid(np.linspace(lo[0], hi[0], 900), np.linspace(lo[1], hi[1], 900))
inside = [(gx - cx) ** 2 + (gy - cy) ** 2 <= r**2 for (cx, cy), r in zip(centres, radii, strict=True)]

fig = go.Figure()
theta = np.linspace(0, 2 * np.pi, 240)
for i, name in enumerate(names):
    color = IMPRINT_PALETTE[i]
    rgb = ", ".join(str(int(color[k : k + 2], 16)) for k in (1, 3, 5))
    others = [f"{other}: {inclusive.get(frozenset([name, other]), 0):.0f}" for other in names if other != name]
    fig.add_trace(
        go.Scatter(
            x=centres[i, 0] + radii[i] * np.cos(theta),
            y=centres[i, 1] + radii[i] * np.sin(theta),
            mode="lines",
            fill="toself",
            fillcolor=f"rgba({rgb}, {FILL_ALPHA})",
            line={"color": color, "width": 2.5},
            hoverinfo="text",
            hovertext=f"<b>{name}</b><br>{SIZE}: {size_of[name]:.0f}<br>Shared with " + ", ".join(others),
            showlegend=False,
        )
    )

# Exclusive count inside each region
for region, count in exclusive.items():
    mask = np.ones_like(gx, dtype=bool)
    for i in range(n):
        mask &= inside[i] if i in region else ~inside[i]
    if mask.any():
        fig.add_annotation(
            x=gx[mask].mean(),
            y=gy[mask].mean(),
            text=f"<b>{count:.0f}</b>",
            showarrow=False,
            font={"size": 17, "color": INK},
        )

# Set names just outside each circle, pointing away from the middle of the diagram
middle = centres.mean(axis=0)
for i, name in enumerate(names):
    away = centres[i] - middle
    away = away / np.linalg.norm(away) if np.linalg.norm(away) > 1e-9 else np.array([0.0, 1.0])
    x, y = centres[i] + away * (radii[i] + 0.8)
    fig.add_annotation(
        x=x, y=y, text=f"<b>{name}</b><br>{size_of[name]:.0f}", showarrow=False, font={"size": 16, "color": INK}
    )

# Style
fig.update_layout(
    autosize=False,
    width=600,
    height=600,
    title={
        "text": "venn-basic · python · plotly · anyplot.ai",
        "font": {"size": 18, "color": INK},
        "x": 0.5,
        "xanchor": "center",
    },
    paper_bgcolor=PAGE_BG,
    plot_bgcolor=PAGE_BG,
    font={"color": INK},
    showlegend=False,
    margin={"l": 30, "r": 30, "t": 70, "b": 30},
    xaxis={"visible": False, "range": [lo[0], hi[0]], "scaleanchor": "y", "scaleratio": 1},
    yaxis={"visible": False, "range": [lo[1], hi[1]]},
)

fig.write_image(f"plot-{THEME}.png", width=600, height=600, scale=4)
fig.write_html(f"plot-{THEME}.html", include_plotlyjs="cdn")
