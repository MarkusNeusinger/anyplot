""" anyplot.ai
circlepacking-basic: Circle Packing Chart
Library: plotly 7.1.0 | Python 3.14.10
Quality: 81/100 | Updated: 2026-11-21
"""

import os

import numpy as np
import pandas as pd
import plotly.graph_objects as go


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Imprint palette: all eight positions, one per top-level group in order
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

# Canvas (square, 600 x 600 CSS px at scale 4 = 2400 x 2400) and the layout margins
SIZE = 600
MARGIN = {"l": 30, "r": 30, "t": 70, "b": 80}

# Columns: set these to your table's column names
NODE = "Node"  # role: id
HABITAT = "Habitat"  # role: parent
TAXON = "Taxon group"  # role: label
SPECIES = "Species count"  # role: value

# Data: replace this block with your own table, for example df = pd.read_csv("species.csv")
# One row per leaf circle: the group it sits in, its name and the value that sets its area.
habitats = {
    "Wetland": {"Birds": 118, "Amphibians": 24, "Fish": 46, "Dragonflies": 31, "Mammals": 12},
    "Forest": {"Birds": 96, "Mammals": 42, "Beetles": 150, "Fungi": 88, "Reptiles": 14},
    "Grassland": {"Butterflies": 64, "Birds": 52, "Reptiles": 18, "Bees": 71},
    "Coastal": {"Seabirds": 38, "Crustaceans": 55, "Fish": 83, "Mammals": 9},
    "Alpine": {"Birds": 27, "Mammals": 16, "Beetles": 44},
}
df = pd.DataFrame(
    [
        (f"{habitat}/{taxon}", habitat, taxon, count)
        for habitat, groups in habitats.items()
        for taxon, count in groups.items()
    ],
    columns=[NODE, HABITAT, TAXON, SPECIES],
)

# Plot: reads only df and the constants above
leaves = df.dropna(subset=[HABITAT, SPECIES]).reset_index(drop=True)
tops = list(dict.fromkeys(leaves[HABITAT]))


def enclose(circles):
    """Center and radius of a circle enclosing all given (x, y, r) circles (iterative approximation)."""
    pts = np.array(circles)
    center = (pts[:, :2] * pts[:, 2:3] ** 2).sum(axis=0) / (pts[:, 2] ** 2).sum()
    for step in range(1, 400):
        far = np.argmax(np.hypot(*(pts[:, :2] - center).T) + pts[:, 2])
        center = center + (pts[far, :2] - center) / (step + 1) * 0.5
    return center, float((np.hypot(*(pts[:, :2] - center).T) + pts[:, 2]).max())


def pack(radii, gap):
    """Place circles of the given radii close together without overlap; returns centered (x, y, r) rows."""
    order = np.argsort(radii)[::-1]
    placed = []
    for idx in order:
        r = radii[idx]
        if not placed:
            placed.append([0.0, 0.0, r])
            continue
        if len(placed) == 1:
            placed.append([placed[0][2] + r + gap, 0.0, r])
            continue
        best, best_d = None, np.inf
        for i, a in enumerate(placed):
            for b in placed[i + 1 :]:
                da, db = a[2] + r + gap, b[2] + r + gap
                dx, dy = b[0] - a[0], b[1] - a[1]
                d = np.hypot(dx, dy)
                if d > da + db or d < abs(da - db) or d == 0:
                    continue
                t = (da**2 - db**2 + d**2) / (2 * d)
                h = np.sqrt(max(da**2 - t**2, 0.0))
                for sign in (1, -1):
                    cx = a[0] + (t * dx - sign * h * dy) / d
                    cy = a[1] + (t * dy + sign * h * dx) / d
                    if all(np.hypot(cx - o[0], cy - o[1]) >= o[2] + r + gap - 1e-9 for o in placed):
                        cost = np.hypot(cx, cy) + r
                        if cost < best_d:
                            best, best_d = (cx, cy), cost
        placed.append([best[0], best[1], r])
    center, radius = enclose(placed)
    out = np.zeros((len(radii), 3))
    for idx, (x, y, r) in zip(order, placed, strict=True):
        out[idx] = (x - center[0], y - center[1], r)
    return out, radius


# Bottom-up: leaf area is proportional to its value, each habitat encloses its packed leaves,
# and the root encloses the habitats
GAP = 1.2
leaf_r = np.sqrt(leaves[SPECIES].to_numpy(dtype=float))
members = {top: np.flatnonzero((leaves[HABITAT] == top).to_numpy()) for top in tops}
packs = {top: pack(leaf_r[idx], GAP) for top, idx in members.items()}
top_r = np.array([packs[top][1] + GAP * 2 for top in tops])
top_layout, root_r = pack(top_r, GAP * 3)
root_r += GAP * 4

limit = root_r * 1.04
plot_px = min(SIZE - MARGIN["l"] - MARGIN["r"], SIZE - MARGIN["t"] - MARGIN["b"])
px_per_unit = plot_px / (2 * limit)

fig = go.Figure()
fig.add_shape(
    type="circle",
    x0=-root_r,
    x1=root_r,
    y0=-root_r,
    y1=root_r,
    fillcolor=INK_SOFT,
    opacity=0.07,
    line={"color": INK_SOFT, "width": 1.2},
    layer="below",
)

leaf_marks = []  # (x, y, r, row, color)
for i, top in enumerate(tops):
    hx, hy, _ = top_layout[i]
    color = IMPRINT_PALETTE[i % len(IMPRINT_PALETTE)]
    fig.add_shape(
        type="circle",
        x0=hx - top_r[i],
        x1=hx + top_r[i],
        y0=hy - top_r[i],
        y1=hy + top_r[i],
        fillcolor=color,
        opacity=0.22,
        line={"color": color, "width": 1.5},
        layer="below",
    )
    for row, (lx, ly, lr) in zip(members[top], packs[top][0], strict=True):
        leaf_marks.append((hx + lx, hy + ly, lr, row, color))
for x, y, r, _, color in leaf_marks:
    fig.add_shape(
        type="circle",
        x0=x - r,
        x1=x + r,
        y0=y - r,
        y1=y + r,
        fillcolor=color,
        opacity=0.9,
        line={"color": PAGE_BG, "width": 0.8},
        layer="below",
    )

# Labels for the leaves whose circle is large enough to hold the text
LEAF_FONT = 8
for x, y, r, row, _ in leaf_marks:
    diameter_px = 2 * r * px_per_unit
    name = str(leaves.loc[row, TAXON])
    if diameter_px < len(name) * LEAF_FONT * 0.66 + 2:
        continue
    text = f"<b>{name}</b><br>{leaves.loc[row, SPECIES]:,.0f}" if diameter_px > 34 else f"<b>{name}</b>"
    fig.add_annotation(x=x, y=y, text=text, showarrow=False, font={"size": LEAF_FONT, "color": "#1A1A17"})

# Invisible hover targets for every leaf
fig.add_trace(
    go.Scatter(
        x=[m[0] for m in leaf_marks],
        y=[m[1] for m in leaf_marks],
        mode="markers",
        marker={"size": [2 * m[2] * px_per_unit for m in leaf_marks], "opacity": 0},
        customdata=[
            [leaves.loc[m[3], TAXON], leaves.loc[m[3], HABITAT], leaves.loc[m[3], SPECIES]] for m in leaf_marks
        ],
        hovertemplate="<b>%{customdata[0]}</b><br>%{customdata[1]}: %{customdata[2]:,.0f} species<extra></extra>",
        showlegend=False,
    )
)

# Legend entries for the habitats
for i, top in enumerate(tops):
    fig.add_trace(
        go.Scatter(
            x=[None],
            y=[None],
            mode="markers",
            marker={
                "size": 10,
                "color": IMPRINT_PALETTE[i % len(IMPRINT_PALETTE)],
                "line": {"color": INK_SOFT, "width": 0.8},
            },
            name=str(top),
        )
    )

# Style
title = "circlepacking-basic · python · plotly · anyplot.ai"
fig.update_layout(
    autosize=False,
    width=SIZE,
    height=SIZE,
    margin=MARGIN,
    title={"text": title, "font": {"size": 16, "color": INK}, "x": 0.5, "xanchor": "center"},
    paper_bgcolor=PAGE_BG,
    plot_bgcolor=PAGE_BG,
    font={"color": INK},
    xaxis={"visible": False, "range": [-limit, limit], "scaleanchor": "y", "scaleratio": 1},
    yaxis={"visible": False, "range": [-limit, limit]},
    legend={
        "orientation": "h",
        "x": 0.5,
        "xanchor": "center",
        "y": -0.02,
        "yanchor": "top",
        "bgcolor": ELEVATED_BG,
        "bordercolor": INK_SOFT,
        "borderwidth": 1,
        "font": {"size": 11, "color": INK_SOFT},
        "title": {"text": HABITAT, "font": {"size": 11, "color": INK}},
    },
)

fig.write_image(f"plot-{THEME}.png", width=SIZE, height=SIZE, scale=4)
fig.write_html(f"plot-{THEME}.html", include_plotlyjs="cdn")
