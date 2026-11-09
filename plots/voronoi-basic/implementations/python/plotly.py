""" anyplot.ai
voronoi-basic: Voronoi Diagram for Spatial Partitioning
Library: plotly 7.1.0 | Python 3.14.10
Quality: 83/100 | Updated: 2026-11-09
"""

import os

import numpy as np
import pandas as pd
import plotly.graph_objects as go
from scipy.spatial import Voronoi


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
GRID = "rgba(26,26,23,0.15)" if THEME == "light" else "rgba(240,239,232,0.15)"

# Imprint palette: all eight positions, assigned so that neighbouring cells differ
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

# Constants
BOX_PAD = 0.125  # bounding-box margin around the seeds, as a share of their span
FILL_ALPHA = 0.6

# Columns: set these to your table's column names
STORE = "Store"  # role: label
LONGITUDE = "Longitude (°)"  # role: x
LATITUDE = "Latitude (°)"  # role: y

# Data: replace this block with your own table, for example df = pd.read_csv("stores.csv")
np.random.seed(42)
n_stores = 20
df = pd.DataFrame(
    {
        STORE: [f"Store {i}" for i in range(n_stores)],
        LONGITUDE: np.random.uniform(10, 90, n_stores),
        LATITUDE: np.random.uniform(10, 90, n_stores),
    }
)

# Plot: reads only df and the constants above
seeds = df.dropna(subset=[LONGITUDE, LATITUDE]).reset_index(drop=True)
points = seeds[[LONGITUDE, LATITUDE]].to_numpy(dtype=float)
n_seeds = len(points)

# Bounding box around the seeds
lo, hi = points.min(axis=0), points.max(axis=0)
pad = np.maximum(hi - lo, 1.0) * BOX_PAD
x_min, y_min = lo - pad
x_max, y_max = hi + pad

# Far-away guard points make every seed's region finite
cx, cy = (x_min + x_max) / 2, (y_min + y_max) / 2
far = 10 * max(x_max - x_min, y_max - y_min)
guards = np.array([[cx + dx * far, cy + dy * far] for dx in (-1, 0, 1) for dy in (-1, 0, 1) if dx or dy])
vor = Voronoi(np.vstack([points, guards]))


def clip_to_box(polygon):
    """Sutherland-Hodgman clipping of a convex polygon to the bounding box."""
    edges = [(0, x_min, 1), (0, x_max, -1), (1, y_min, 1), (1, y_max, -1)]
    for axis, bound, sign in edges:
        clipped = []
        for i, curr in enumerate(polygon):
            nxt = polygon[(i + 1) % len(polygon)]
            curr_in = sign * (curr[axis] - bound) >= 0
            next_in = sign * (nxt[axis] - bound) >= 0
            if curr_in:
                clipped.append(curr)
            if curr_in != next_in:
                t = (bound - curr[axis]) / (nxt[axis] - curr[axis])
                clipped.append(curr + t * (nxt - curr))
        polygon = clipped
        if not polygon:
            break
    return polygon


# Neighbouring cells share a Voronoi ridge; colour them greedily in smallest-last order
neighbours = {i: set() for i in range(n_seeds)}
for a, b in vor.ridge_points:
    if a < n_seeds and b < n_seeds:
        neighbours[a].add(b)
        neighbours[b].add(a)
order, remaining = [], set(range(n_seeds))
while remaining:
    node = min(remaining, key=lambda n: (len(neighbours[n] & remaining), n))
    order.append(node)
    remaining.remove(node)
color_index = {}
for node in reversed(order):
    taken = {color_index[n] for n in neighbours[node] if n in color_index}
    color_index[node] = min(c for c in range(len(IMPRINT_PALETTE)) if c not in taken)

fig = go.Figure()

# Voronoi cells (service areas)
for idx in range(n_seeds):
    region = vor.regions[vor.point_region[idx]]
    polygon = clip_to_box([vor.vertices[v] for v in region])
    if len(polygon) < 3:
        continue
    poly = np.array(polygon + [polygon[0]])
    color = IMPRINT_PALETTE[color_index[idx]]
    r, g, b = (int(color[k : k + 2], 16) for k in (1, 3, 5))
    fig.add_trace(
        go.Scatter(
            x=poly[:, 0],
            y=poly[:, 1],
            fill="toself",
            fillcolor=f"rgba({r},{g},{b},{FILL_ALPHA})",
            line={"color": INK_SOFT, "width": 1.5},
            mode="lines",
            hoverinfo="skip",
            showlegend=False,
        )
    )

# Seed points (store locations) on top
fig.add_trace(
    go.Scatter(
        x=seeds[LONGITUDE],
        y=seeds[LATITUDE],
        mode="markers",
        marker={"size": 10, "color": INK, "line": {"color": ELEVATED_BG, "width": 2}, "symbol": "circle"},
        name=STORE,
        customdata=seeds[[STORE]].astype(str),
        hovertemplate=f"%{{customdata[0]}}<br>{LONGITUDE}: %{{x:.1f}}<br>{LATITUDE}: %{{y:.1f}}<extra></extra>",
    )
)

axis_style = {
    "showgrid": True,
    "gridwidth": 1,
    "gridcolor": GRID,
    "zeroline": False,
    "linecolor": INK_SOFT,
    "tickfont": {"size": 10, "color": INK_SOFT},
}
fig.update_layout(
    autosize=False,
    width=600,
    height=600,
    title={
        "text": "voronoi-basic · python · plotly · anyplot.ai",
        "font": {"size": 16, "color": INK},
        "x": 0.5,
        "xanchor": "center",
    },
    xaxis={
        **axis_style,
        "title": {"text": LONGITUDE, "font": {"size": 12, "color": INK}},
        "range": [x_min, x_max],
        "constrain": "domain",
    },
    yaxis={
        **axis_style,
        "title": {"text": LATITUDE, "font": {"size": 12, "color": INK}},
        "range": [y_min, y_max],
        "scaleanchor": "x",
        "scaleratio": 1,
        "constrain": "domain",
    },
    paper_bgcolor=PAGE_BG,
    plot_bgcolor=PAGE_BG,
    font={"color": INK},
    showlegend=True,
    legend={
        "font": {"size": 10, "color": INK_SOFT},
        "x": 1,
        "y": 1.02,
        "xanchor": "right",
        "yanchor": "bottom",
        "orientation": "h",
        "bgcolor": ELEVATED_BG,
        "bordercolor": INK_SOFT,
        "borderwidth": 1,
    },
    margin={"l": 70, "r": 30, "t": 80, "b": 60},
)

# Save as PNG and HTML (square format for the Voronoi diagram)
fig.write_image(f"plot-{THEME}.png", width=600, height=600, scale=4)
fig.write_html(f"plot-{THEME}.html", include_plotlyjs="cdn")
