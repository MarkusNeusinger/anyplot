""" anyplot.ai
venn-labeled-items: Chartgeist-Style Venn Diagram with Labeled Items
Library: plotly 6.7.0 | Python 3.14.4
Quality: 85/100 | Created: 2026-04-25
"""

import os

import numpy as np
import plotly.graph_objects as go


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
INK_MUTED = "#6B6A63" if THEME == "light" else "#A8A79F"

# Okabe-Ito categorical palette: first series is brand green
CIRCLE_COLORS = ["#009E73", "#D55E00", "#0072B2"]
CIRCLE_FILLS = ["rgba(0,158,115,0.26)", "rgba(213,94,0,0.26)", "rgba(0,114,178,0.26)"]

# Data: editorial Chartgeist-style commentary on tech/culture
circles = [{"name": "Overhyped"}, {"name": "Actually Useful"}, {"name": "Secretly Loved"}]

items = [
    {"label": "NFTs", "zone": "A"},
    {"label": "Crypto Bros", "zone": "A"},
    {"label": "Metaverse", "zone": "A"},
    {"label": "Google Maps", "zone": "B"},
    {"label": "VS Code", "zone": "B"},
    {"label": "Dishwasher", "zone": "B"},
    {"label": "ABBA", "zone": "C"},
    {"label": "Slippers", "zone": "C"},
    {"label": "Crocs", "zone": "C"},
    {"label": "ChatGPT", "zone": "AB"},
    {"label": "Slack", "zone": "AB"},
    {"label": "Vinyl Records", "zone": "AC"},
    {"label": "Dolly Parton", "zone": "BC"},
    {"label": "Sourdough", "zone": "ABC"},
    {"label": "Beige Walls", "zone": "outside"},
]

# Three-circle symmetric Venn layout
radius = 1.0
angles = [np.pi / 2, np.pi / 2 + 2 * np.pi / 3, np.pi / 2 + 4 * np.pi / 3]
center_dist = 0.55
cx = [center_dist * np.cos(a) for a in angles]
cy = [center_dist * np.sin(a) for a in angles]

# Per-zone anchor (x, y, default text-position) — placed using exact circle geometry
zone_anchors = {
    "A": (0.0, 1.07, "middle right"),
    "B": (-0.95, -0.30, "middle right"),
    "C": (0.95, -0.30, "middle right"),
    "AB": (-0.50, 0.30, "middle right"),
    "AC": (0.50, 0.30, "middle right"),
    "BC": (0.0, -0.55, "middle right"),
    "ABC": (0.0, 0.0, "middle right"),
    "outside": (-2.20, 1.55, "middle right"),
}

# Spread offsets when multiple items share a zone (relative to anchor)
zone_offsets = {1: [(0.0, 0.0)], 2: [(0.0, 0.10), (0.0, -0.10)], 3: [(0.0, 0.30), (0.0, 0.0), (0.0, -0.30)]}

# Group items by zone, compute final coords
zones_grouped = {}
for it in items:
    zones_grouped.setdefault(it["zone"], []).append(it["label"])

placed = []
for zone, labels in zones_grouped.items():
    ax, ay, tpos = zone_anchors[zone]
    offsets = zone_offsets[len(labels)]
    for label, (dx, dy) in zip(labels, offsets, strict=False):
        placed.append((ax + dx, ay + dy, label, zone, tpos))

# Build figure
fig = go.Figure()

# Filled circles
theta = np.linspace(0, 2 * np.pi, 240)
for i in range(3):
    fig.add_trace(
        go.Scatter(
            x=cx[i] + radius * np.cos(theta),
            y=cy[i] + radius * np.sin(theta),
            fill="toself",
            fillcolor=CIRCLE_FILLS[i],
            line={"color": CIRCLE_COLORS[i], "width": 4},
            mode="lines",
            name=circles[i]["name"],
            showlegend=False,
            hoverinfo="skip",
        )
    )

# Item markers + labels — one trace per text position to mix alignments
positions = sorted({p[4] for p in placed})
for tpos in positions:
    pts = [p for p in placed if p[4] == tpos]
    fig.add_trace(
        go.Scatter(
            x=[p[0] for p in pts],
            y=[p[1] for p in pts],
            mode="markers+text",
            marker={"size": 10, "color": INK, "line": {"width": 0}},
            text=[f" {p[2]}" for p in pts],
            textposition=tpos,
            textfont={"family": "Georgia, 'Times New Roman', serif", "size": 19, "color": INK},
            hovertext=[f"{p[2]} — {p[3]}" for p in pts],
            hoverinfo="text",
            showlegend=False,
        )
    )

# Category labels outside each circle, on the outer side, kept inside the canvas
category_label_positions = [
    (cx[0], cy[0] + radius + 0.32, "center", "bottom"),
    (cx[1] - radius * 0.55, cy[1] - radius - 0.05, "right", "top"),
    (cx[2] + radius * 0.55, cy[2] - radius - 0.05, "left", "top"),
]

for i, (lx, ly, xa, ya) in enumerate(category_label_positions):
    fig.add_annotation(
        x=lx,
        y=ly,
        text=f"<b>{circles[i]['name'].upper()}</b>",
        showarrow=False,
        font={"family": "Georgia, 'Times New Roman', serif", "size": 28, "color": CIRCLE_COLORS[i]},
        xanchor=xa,
        yanchor=ya,
    )

# Subtle hint label for the "outside" cluster
fig.add_annotation(
    x=-2.20,
    y=1.85,
    text="<i>Neither here nor there</i>",
    showarrow=False,
    font={"family": "Georgia, 'Times New Roman', serif", "size": 16, "color": INK_MUTED},
    xanchor="left",
    yanchor="bottom",
)

# Editorial subtitle / kicker
fig.add_annotation(
    xref="paper",
    yref="paper",
    x=0.5,
    y=1.005,
    text="<i>An entirely subjective taxonomy of things, ranked by vibe.</i>",
    showarrow=False,
    font={"family": "Georgia, 'Times New Roman', serif", "size": 18, "color": INK_SOFT},
    xanchor="center",
    yanchor="bottom",
)

fig.update_layout(
    title={
        "text": "<b>CHARTGEIST</b>  ·  venn-labeled-items · plotly · anyplot.ai",
        "font": {"family": "Georgia, 'Times New Roman', serif", "size": 30, "color": INK},
        "x": 0.5,
        "xanchor": "center",
        "y": 0.965,
    },
    paper_bgcolor=PAGE_BG,
    plot_bgcolor=PAGE_BG,
    showlegend=False,
    xaxis={"visible": False, "range": [-2.7, 2.7], "scaleanchor": "y", "scaleratio": 1},
    yaxis={"visible": False, "range": [-2.3, 2.3]},
    margin={"l": 50, "r": 50, "t": 140, "b": 50},
    font={"family": "Georgia, 'Times New Roman', serif", "color": INK},
)

fig.write_image(f"plot-{THEME}.png", width=1200, height=1200, scale=3)
fig.write_html(f"plot-{THEME}.html", include_plotlyjs="cdn")
