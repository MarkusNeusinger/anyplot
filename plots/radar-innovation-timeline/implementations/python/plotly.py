"""anyplot.ai
radar-innovation-timeline: Innovation Radar with Time-Horizon Rings
Library: plotly 7.1.0 | Python 3.14.10
Quality: 82/100 | Updated: 2026-11-27
"""

import os
import sys


sys.path = sys.path[1:]  # prevent this file from shadowing the installed plotly package

import numpy as np
import pandas as pd
import plotly.graph_objects as go


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
INK_MUTED = "#6B6A63" if THEME == "light" else "#A8A79F"

# Imprint palette: one color per sector in canonical order
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

# Constants
SECTOR_SYMBOLS = ["circle", "diamond", "square", "triangle-up", "star", "cross", "hexagon", "pentagon"]
ARC_DEGREES = 270  # three-quarter layout: the open quadrant holds the ring labels

# Columns: set these to your table's column names
NAME = "Innovation"  # role: name
RING = "Time horizon ring"  # role: ring
SECTOR = "Sector"  # role: sector
HORIZON = "Expected adoption"  # role: extra

# Data: replace this block with your own table, for example df = pd.read_csv("radar.csv")
_horizon = {"Adopt": "now", "Trial": "0–1 yr", "Assess": "1–3 yr", "Hold": "3+ yr"}
_items = [
    ("LLM Agents", "Adopt", "AI & ML"),
    ("RAG Pipelines", "Adopt", "AI & ML"),
    ("Multimodal Models", "Trial", "AI & ML"),
    ("AI Code Review", "Trial", "AI & ML"),
    ("Neuromorphic Chips", "Assess", "AI & ML"),
    ("Autonomous Research", "Hold", "AI & ML"),
    ("Quantum ML", "Hold", "AI & ML"),
    ("Platform Engineering", "Adopt", "Cloud & Infra"),
    ("FinOps", "Adopt", "Cloud & Infra"),
    ("WebAssembly", "Trial", "Cloud & Infra"),
    ("Edge Computing", "Trial", "Cloud & Infra"),
    ("Confidential Computing", "Assess", "Cloud & Infra"),
    ("Serverless GPUs", "Assess", "Cloud & Infra"),
    ("Decentralized Cloud", "Hold", "Cloud & Infra"),
    ("Carbon Tracking APIs", "Adopt", "Sustainability"),
    ("Green Software", "Trial", "Sustainability"),
    ("Digital Product Passports", "Trial", "Sustainability"),
    ("Circular Economy Platforms", "Assess", "Sustainability"),
    ("Climate AI", "Assess", "Sustainability"),
    ("Fusion Energy Tech", "Hold", "Sustainability"),
    ("mRNA Therapeutics", "Adopt", "Biotech"),
    ("CRISPR Diagnostics", "Trial", "Biotech"),
    ("Digital Twins (Health)", "Assess", "Biotech"),
    ("Synthetic Biology", "Assess", "Biotech"),
    ("Brain-Computer Interfaces", "Hold", "Biotech"),
    ("Longevity Engineering", "Hold", "Biotech"),
]
df = pd.DataFrame(
    {
        NAME: [n for n, _, _ in _items],
        RING: [r for _, r, _ in _items],
        SECTOR: [s for _, _, s in _items],
        HORIZON: [_horizon[r] for _, r, _ in _items],
    }
)

# Plot: reads only df and the constants above
sectors = list(df[SECTOR].unique())
rings = list(df[RING].unique())
horizon_of = df.drop_duplicates(RING).set_index(RING)[HORIZON]
sector_span = ARC_DEGREES / len(sectors)

HOLE = 1.3  # empty radius at the centre: gives the inner ring room for its labels
RING_W = 0.85
R_MAX = HOLE + RING_W * len(rings)
edges = [HOLE + RING_W * i for i in range(len(rings) + 1)]
marker_sizes = [max(8, 19 - 3 * i) for i in range(len(rings))]


def xy(radius, deg):
    """Compass angle (clockwise from north) and radius to cartesian coordinates."""
    rad = np.radians(deg)
    return radius * np.sin(rad), radius * np.cos(rad)


# Positions: items of one cell spread evenly across its sector, alternating radially inside the ring
rows = []
for si, sector in enumerate(sectors):
    start = si * sector_span
    for ri, ring in enumerate(rings):
        cell = df[(df[SECTOR] == sector) & (df[RING] == ring)]
        n = len(cell)
        for k, name in enumerate(cell[NAME]):
            if n == 1:
                deg = start + sector_span * (0.3 if ri % 2 else 0.7)  # lone items alternate sides
            else:
                deg = start + sector_span * (0.2 + 0.6 * k / (n - 1))
            radius = edges[ri] + RING_W * (0.5 + (0.2 if k % 2 else -0.2) * (n > 1))
            x, y = xy(radius, deg)
            rows.append({"name": name, "sector": sector, "ring": ring, "ri": ri, "x": x, "y": y, "deg": deg})
pos = pd.DataFrame(rows)

# Label placement: per item pick the side (right, left, above, below) whose text box overlaps least
# with the markers and the labels already placed; widths are estimated from the 11 px font
CHAR_W, TEXT_H = 0.16, 0.36  # text box size in radial units per character / per line
half = pos["ri"].map(lambda i: marker_sizes[i]) / 36 / 2
sides = {
    "middle right": lambda x, y, w, m: (x + m + 0.05, x + m + 0.05 + w, y - TEXT_H / 2, y + TEXT_H / 2),
    "middle left": lambda x, y, w, m: (x - m - 0.05 - w, x - m - 0.05, y - TEXT_H / 2, y + TEXT_H / 2),
    "top center": lambda x, y, w, m: (x - w / 2, x + w / 2, y + m, y + m + TEXT_H),
    "bottom center": lambda x, y, w, m: (x - w / 2, x + w / 2, y - m - TEXT_H, y - m),
}


def overlap(a, b):
    return max(0, min(a[1], b[1]) - max(a[0], b[0])) * max(0, min(a[3], b[3]) - max(a[2], b[2]))


marker_boxes = [(x - m, x + m, y - m, y + m) for x, y, m in zip(pos["x"], pos["y"], half, strict=True)]
# Ring names stand left of the north divider in the open quadrant, one per ring, two lines each (12 px font)
ring_xy = [(-0.12, edges[ri] + RING_W / 2) for ri in range(len(rings))]
ring_boxes = []
for ring, (rx, ry) in zip(rings, ring_xy, strict=True):
    rw = CHAR_W * 1.4 * max(len(ring), len(f"({horizon_of[ring]})"))
    ring_boxes.append((rx - rw, rx, ry - TEXT_H, ry + TEXT_H))
placed = []


def outside_cell(box, ri, si):
    """Share of sample points of a text box that lie outside its item's ring and sector cell."""
    gx = np.linspace(box[0], box[1], 7)
    gy = np.linspace(box[2], box[3], 3)
    px, py = np.meshgrid(gx, gy)
    radius = np.hypot(px, py)
    deg = np.degrees(np.arctan2(px, py)) % 360
    inside = (
        (radius >= edges[ri]) & (radius <= edges[ri + 1]) & (deg >= si * sector_span) & (deg <= (si + 1) * sector_span)
    )
    return 1 - inside.mean()


textpos = []
for i, row in pos.iterrows():
    w = CHAR_W * len(str(row["name"]))
    order = ["middle right", "middle left"] if row["x"] >= 0 else ["middle left", "middle right"]
    best = None
    for side in order + ["top center", "bottom center"]:
        box = sides[side](row["x"], row["y"], w, half[i])
        cost = (
            sum(overlap(box, b) for b in placed)
            + 6 * sum(overlap(box, b) for b in ring_boxes)
            + 4 * sum(overlap(box, b) for j, b in enumerate(marker_boxes) if j != i)
            + 0.15 * outside_cell(box, row["ri"], sectors.index(row["sector"]))
        )
        if best is None or cost < best[0] - 1e-9:
            best = (cost, side, box)
    textpos.append(best[1])
    placed.append(best[2])
pos["textpos"] = textpos

ring_fill_alpha = [0.10, 0.07, 0.045, 0.025] if THEME == "light" else [0.18, 0.11, 0.07, 0.04]
ring_line = "rgba(26,26,23,0.22)" if THEME == "light" else "rgba(240,239,232,0.25)"
sector_line = "rgba(26,26,23,0.35)" if THEME == "light" else "rgba(240,239,232,0.38)"

fig = go.Figure()

# Ring fills: annular bands over the drawn arc
arc = np.linspace(0, ARC_DEGREES, 160)
for ri in range(len(rings)):
    outer = xy(edges[ri + 1], arc)
    inner = xy(edges[ri], arc[::-1])
    fig.add_trace(
        go.Scatter(
            x=np.concatenate([outer[0], inner[0]]),
            y=np.concatenate([outer[1], inner[1]]),
            fill="toself",
            fillcolor=f"rgba(0,158,115,{ring_fill_alpha[min(ri, len(ring_fill_alpha) - 1)]})",
            mode="none",
            showlegend=False,
            hoverinfo="skip",
        )
    )

# Ring boundaries
for edge in edges:
    bx, by = xy(edge, arc)
    fig.add_trace(
        go.Scatter(
            x=bx, y=by, mode="lines", line={"color": ring_line, "width": 1.2}, showlegend=False, hoverinfo="skip"
        )
    )

# Sector dividers
for si in range(len(sectors) + 1):
    d0 = xy(HOLE, si * sector_span)
    d1 = xy(R_MAX, si * sector_span)
    fig.add_trace(
        go.Scatter(
            x=[d0[0], d1[0]],
            y=[d0[1], d1[1]],
            mode="lines",
            line={"color": sector_line, "width": 1, "dash": "dot"},
            showlegend=False,
            hoverinfo="skip",
        )
    )

# Items: one trace per sector
for si, sector in enumerate(sectors):
    cell = pos[pos["sector"] == sector]
    fig.add_trace(
        go.Scatter(
            x=cell["x"],
            y=cell["y"],
            mode="markers+text",
            opacity=1,
            marker={
                "size": [marker_sizes[i] for i in cell["ri"]],
                "color": IMPRINT_PALETTE[si % len(IMPRINT_PALETTE)],
                "symbol": SECTOR_SYMBOLS[si % len(SECTOR_SYMBOLS)],
                "opacity": 1,
                "line": {"color": PAGE_BG, "width": 1.5},
            },
            text=cell["name"],
            textposition=cell["textpos"],
            textfont={"size": 11, "color": INK},
            name=sector,
            customdata=cell["ring"],
            hovertemplate="%{text}<br>Ring: %{customdata}<extra>" + sector + "</extra>",
        )
    )

annotations = []
# Sector headers along the outer edge
for si, sector in enumerate(sectors):
    mid = si * sector_span + sector_span / 2
    if np.sin(np.radians(mid)) < -0.3:  # west-side header moves to the sector's lower end, clear of the item labels
        mid = si * sector_span + sector_span * 0.25
    hx, hy = xy(R_MAX + 0.3, mid)
    sx, sy = np.sin(np.radians(mid)), np.cos(np.radians(mid))
    xanchor = "left" if sx > 0.3 else "right" if sx < -0.3 else "center"
    yanchor = "bottom" if sy > 0.7 else "top" if sy < -0.7 else "middle"
    annotations.append(
        {
            "text": f"<b>{sector}</b>",
            "x": hx,
            "y": hy,
            "xanchor": xanchor,
            "yanchor": yanchor,
            "showarrow": False,
            "font": {"size": 17, "color": IMPRINT_PALETTE[si % len(IMPRINT_PALETTE)]},
        }
    )
# Ring names in the open quadrant, right-aligned against the north divider
for ri, ring in enumerate(rings):
    lx, ly = ring_xy[ri]
    annotations.append(
        {
            "text": f"<b>{ring}</b><br>({horizon_of[ring]})",
            "x": lx,
            "y": ly,
            "xanchor": "right",
            "yanchor": "middle",
            "showarrow": False,
            "font": {"size": 12, "color": INK_SOFT},
        }
    )

title_text = "radar-innovation-timeline · python · plotly · anyplot.ai"
title_fontsize = max(11, round(16 * 67 / len(title_text))) if len(title_text) > 67 else 16
MARGIN = {"l": 30, "r": 30, "t": 40, "b": 10}
y_lo, y_hi = -R_MAX - 0.85, R_MAX + 0.3
unit_px = (450 - MARGIN["t"] - MARGIN["b"]) / (y_hi - y_lo)  # pixels per radial unit
x_span = (800 - MARGIN["l"] - MARGIN["r"]) / unit_px
x_lo = -x_span / 2

fig.update_layout(
    autosize=False,
    title={
        "text": title_text,
        "font": {"size": title_fontsize, "color": INK},
        "x": 0.5,
        "xanchor": "center",
        "y": 0.97,
    },
    xaxis={"visible": False, "range": [x_lo, x_lo + x_span]},
    yaxis={"visible": False, "range": [y_lo, y_hi], "scaleanchor": "x", "scaleratio": 1},
    paper_bgcolor=PAGE_BG,
    plot_bgcolor=PAGE_BG,
    font={"color": INK},
    legend={
        "font": {"size": 13, "color": INK_SOFT},
        "x": (-R_MAX - x_lo) / x_span,  # in the open quadrant, left of the ring names
        "y": (0.15 - y_lo) / (y_hi - y_lo),
        "xanchor": "left",
        "yanchor": "bottom",
        "bgcolor": ELEVATED_BG,
        "bordercolor": INK_SOFT,
        "borderwidth": 1,
        "title": {"text": f"<b>{SECTOR}</b>", "font": {"size": 14, "color": INK}},
    },
    margin=MARGIN,
    annotations=annotations,
)

fig.write_image(f"plot-{THEME}.png", width=800, height=450, scale=4)
fig.write_html(f"plot-{THEME}.html", include_plotlyjs="cdn")
