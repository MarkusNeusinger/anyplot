""" anyplot.ai
network-transport-static: Static Transport Network Diagram
Library: plotly 7.1.0 | Python 3.14.10
Quality: 81/100 | Updated: 2026-11-22
"""

import os

import numpy as np
import pandas as pd
import plotly.graph_objects as go


# Theme-adaptive tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Imprint palette (canonical order, first series is always brand green)
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

# Column constants
ROUTE_ID = "Route"  # role: routes
SOURCE = "From"  # role: extra
TARGET = "To"  # role: extra
DEPARTURE = "Departure"  # role: extra
ARRIVAL = "Arrival"  # role: extra
ROUTE_TYPE = "Route type"  # role: extra
SOURCE_X = "From x"  # role: stations
SOURCE_Y = "From y"  # role: extra
TARGET_X = "To x"  # role: extra
TARGET_Y = "To y"  # role: extra

# Data: replace this block with your own table, for example df = pd.read_csv("routes.csv")
# Regional rail network: one row per directed route, station coordinates attached to both ends
stations = {
    "Central Station": (0.5, 0.9),
    "North Park": (0.2, 0.7),
    "East Harbor": (0.8, 0.75),
    "West Gate": (0.1, 0.5),
    "Downtown": (0.5, 0.55),
    "Airport": (0.9, 0.5),
    "University": (0.3, 0.35),
    "Tech Campus": (0.7, 0.35),
    "South Valley": (0.2, 0.15),
    "Industrial Zone": (0.5, 0.1),
    "Beach Resort": (0.85, 0.15),
}
routes = [
    ("Central Station", "Downtown", "EX 01", "06:00", "06:12", "express"),
    ("Central Station", "North Park", "RE 10", "06:15", "06:32", "regional"),
    ("North Park", "Downtown", "LO 05", "07:00", "07:18", "local"),
    ("Central Station", "East Harbor", "RE 12", "06:20", "06:38", "regional"),
    ("North Park", "West Gate", "RE 10", "06:35", "06:52", "regional"),
    ("East Harbor", "Airport", "EX 02", "06:42", "06:55", "express"),
    ("East Harbor", "Downtown", "RE 12", "06:45", "07:02", "regional"),
    ("West Gate", "University", "RE 10", "06:55", "07:12", "regional"),
    ("Downtown", "University", "LO 05", "07:22", "07:38", "local"),
    ("Downtown", "Tech Campus", "RE 15", "07:10", "07:28", "regional"),
    ("Downtown", "Airport", "EX 01", "06:15", "06:35", "express"),
    ("Airport", "Tech Campus", "LO 08", "07:00", "07:20", "local"),
    ("Airport", "Beach Resort", "RE 18", "07:30", "07:55", "regional"),
    ("University", "South Valley", "RE 10", "07:15", "07:32", "regional"),
    ("University", "Industrial Zone", "LO 05", "07:42", "08:00", "local"),
    ("Tech Campus", "Industrial Zone", "RE 15", "07:32", "07:48", "regional"),
    ("Tech Campus", "Beach Resort", "LO 08", "07:25", "07:50", "local"),
    ("South Valley", "Industrial Zone", "LO 09", "07:40", "07:58", "local"),
    ("Industrial Zone", "Beach Resort", "RE 18", "08:05", "08:25", "regional"),
]
df = pd.DataFrame(routes, columns=[SOURCE, TARGET, ROUTE_ID, DEPARTURE, ARRIVAL, ROUTE_TYPE])
df[[SOURCE_X, SOURCE_Y]] = [stations[name] for name in df[SOURCE]]
df[[TARGET_X, TARGET_Y]] = [stations[name] for name in df[TARGET]]

# Plot: reads only df and the constants above
WIDTH, HEIGHT = 800, 450
MARGIN = dict(l=30, r=30, t=50, b=20)
x_range = [df[[SOURCE_X, TARGET_X]].min().min() - 0.15, df[[SOURCE_X, TARGET_X]].max().max() + 0.15]
y_range = [df[[SOURCE_Y, TARGET_Y]].min().min() - 0.12, df[[SOURCE_Y, TARGET_Y]].max().max() + 0.12]

# Pixel scale of the plot area, so offsets, label angles and arrow gaps are computed in screen space
sx = (WIDTH - MARGIN["l"] - MARGIN["r"]) / (x_range[1] - x_range[0])
sy = (HEIGHT - MARGIN["t"] - MARGIN["b"]) / (y_range[1] - y_range[0])

NODE_PX = 16  # marker diameter
GAP_PX = NODE_PX / 2 + 3  # edges stop just outside the node so arrowheads stay visible
OFFSET_PX = 9  # spacing between parallel routes of one station pair
LABEL_PX = 12  # route label distance from its edge

type_color = {t: IMPRINT_PALETTE[i] for i, t in enumerate(df[ROUTE_TYPE].unique())}

fig = go.Figure()
pair_count = {}
legend_done = set()

for _, r in df.iterrows():
    x0, y0 = r[SOURCE_X] * sx, r[SOURCE_Y] * sy
    x1, y1 = r[TARGET_X] * sx, r[TARGET_Y] * sy
    length = np.hypot(x1 - x0, y1 - y0)
    ux, uy = (x1 - x0) / length, (y1 - y0) / length
    px, py = -uy, ux

    # Parallel routes of the same station pair fan out to alternating sides
    pair = tuple(sorted([r[SOURCE], r[TARGET]]))
    k = pair_count.get(pair, 0)
    pair_count[pair] = k + 1
    off = 0 if k == 0 else (1 if k % 2 == 1 else -1) * ((k + 1) // 2) * OFFSET_PX

    ax0 = x0 + px * off + ux * GAP_PX
    ay0 = y0 + py * off + uy * GAP_PX
    ax1 = x1 + px * off - ux * GAP_PX
    ay1 = y1 + py * off - uy * GAP_PX
    color = type_color[r[ROUTE_TYPE]]

    fig.add_trace(
        go.Scatter(
            x=[ax0 / sx, ax1 / sx],
            y=[ay0 / sy, ay1 / sy],
            mode="lines",
            line=dict(color=color, width=1.6),
            hoverinfo="text",
            hovertext=f"{r[ROUTE_ID]}: {r[SOURCE]} → {r[TARGET]}<br>{r[DEPARTURE]} → {r[ARRIVAL]}",
            name=str(r[ROUTE_TYPE]).capitalize(),
            legendgroup=r[ROUTE_TYPE],
            showlegend=r[ROUTE_TYPE] not in legend_done,
        )
    )
    legend_done.add(r[ROUTE_TYPE])

    fig.add_annotation(
        x=ax1 / sx,
        y=ay1 / sy,
        ax=ax0 / sx,
        ay=ay0 / sy,
        xref="x",
        yref="y",
        axref="x",
        ayref="y",
        showarrow=True,
        arrowhead=2,
        arrowsize=1.4,
        arrowwidth=1.6,
        arrowcolor=color,
        standoff=0,
    )

    # Route label beside the middle of its own edge, text running along the edge
    mx, my = (ax0 + ax1) / 2 + px * LABEL_PX, (ay0 + ay1) / 2 + py * LABEL_PX
    angle = np.degrees(np.arctan2(uy, ux))  # direction in screen space (y up)
    if angle > 90:
        angle -= 180
    elif angle < -90:
        angle += 180
    fig.add_annotation(
        x=mx / sx,
        y=my / sy,
        text=f"<b>{r[ROUTE_ID]}</b><br>{r[DEPARTURE]}→{r[ARRIVAL]}",
        showarrow=False,
        font=dict(size=7.5, color=INK),
        bgcolor=ELEVATED_BG,
        bordercolor=color,
        borderwidth=0.6,
        borderpad=1.5,
        textangle=-angle,
    )

# Station nodes at their given coordinates
nodes = pd.concat(
    [
        df[[SOURCE, SOURCE_X, SOURCE_Y]].set_axis(["name", "x", "y"], axis=1),
        df[[TARGET, TARGET_X, TARGET_Y]].set_axis(["name", "x", "y"], axis=1),
    ]
).drop_duplicates("name")

fig.add_trace(
    go.Scatter(
        x=nodes["x"],
        y=nodes["y"],
        mode="markers",
        marker=dict(size=NODE_PX, color=ELEVATED_BG, line=dict(color=INK, width=1.8)),
        hoverinfo="text",
        hovertext=nodes["name"],
        showlegend=False,
    )
)


def label_shift(name):
    """Pixel shift of the name label: the side (below, above, right, left) whose direction the fewest edges leave toward."""
    vecs = []
    for _, r in df.iterrows():
        if r[SOURCE] == name:
            v = ((r[TARGET_X] - r[SOURCE_X]) * sx, (r[TARGET_Y] - r[SOURCE_Y]) * sy)
        elif r[TARGET] == name:
            v = ((r[SOURCE_X] - r[TARGET_X]) * sx, (r[SOURCE_Y] - r[TARGET_Y]) * sy)
        else:
            continue
        vecs.append((v[0] / np.hypot(*v), v[1] / np.hypot(*v)))
    reach = 14 + 2.8 * len(name)  # half the label width plus a gap
    sides = [((0, -28), (0, -1), 0.0), ((0, 28), (0, 1), 0.0), ((reach, 0), (1, 0), 0.0), ((-reach, 0), (-1, 0), 0.0)]
    best = min(sides, key=lambda c: max(vx * c[1][0] + vy * c[1][1] for vx, vy in vecs) + c[2])
    return best[0]


for _, s in nodes.iterrows():
    xshift, yshift = label_shift(s["name"])
    fig.add_annotation(
        x=s["x"],
        y=s["y"],
        xshift=xshift,
        yshift=yshift,
        text=f"<b>{s['name']}</b>",
        showarrow=False,
        font=dict(size=9, color=INK),
        bgcolor=ELEVATED_BG,
        bordercolor=INK_SOFT,
        borderwidth=0.6,
        borderpad=2,
    )

# Style
fig.update_layout(
    autosize=False,
    width=WIDTH,
    height=HEIGHT,
    margin=MARGIN,
    title=dict(
        text="network-transport-static · python · plotly · anyplot.ai",
        font=dict(size=18, color=INK),
        x=0.5,
        xanchor="center",
    ),
    xaxis=dict(visible=False, range=x_range),
    yaxis=dict(visible=False, range=y_range),
    plot_bgcolor=PAGE_BG,
    paper_bgcolor=PAGE_BG,
    font=dict(color=INK),
    legend=dict(
        title=dict(text=f"{ROUTE_TYPE}", font=dict(size=10, color=INK)),
        x=0.01,
        y=0.99,
        bgcolor=ELEVATED_BG,
        bordercolor=INK_SOFT,
        borderwidth=0.6,
        font=dict(size=10, color=INK_SOFT),
    ),
)

# Save outputs
fig.write_image(f"plot-{THEME}.png", width=WIDTH, height=HEIGHT, scale=4)
fig.write_html(f"plot-{THEME}.html", include_plotlyjs="cdn")
