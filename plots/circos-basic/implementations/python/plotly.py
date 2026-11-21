"""anyplot.ai
circos-basic: Circos Plot
Library: plotly 6.7.0 | Python 3.13.13
Quality: pending | Updated: 2026-05-15
"""

import os

import numpy as np
import pandas as pd
import plotly.graph_objects as go


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Imprint palette: all eight positions, one per segment in order
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

# Constants
GAP_DEG = 2  # gap between neighbouring segments on the outer ring
MIN_FLOW = 5  # flows at or below this value are too thin to draw as ribbons

# Columns: set these to your table's column names
SOURCE = "Source region"  # role: source
TARGET = "Target region"  # role: target
FLOW = "Trade flow (billion USD)"  # role: value
SIZE = "Economic size (index)"  # role: segment_size
TRACK = "GDP index"  # role: track_data

# Data: replace this block with your own edge list, for example df = pd.read_csv("flows.csv")
regions = ["North America", "Europe", "East Asia", "South America", "Africa", "Middle East", "South Asia", "Oceania"]
sizes = [25, 30, 28, 10, 8, 12, 15, 6]
track_values = [0.8, 0.95, 0.9, 0.4, 0.25, 0.5, 0.55, 0.3]
flows = np.array(
    [
        [0, 45, 60, 15, 5, 10, 8, 12],
        [40, 0, 35, 12, 18, 25, 15, 8],
        [55, 38, 0, 10, 12, 20, 30, 18],
        [12, 10, 8, 0, 8, 3, 4, 5],
        [6, 20, 10, 10, 0, 15, 6, 2],
        [12, 28, 22, 4, 12, 0, 18, 5],
        [10, 18, 35, 5, 8, 22, 0, 8],
        [15, 10, 22, 6, 3, 6, 10, 0],
    ]
)
df = pd.DataFrame(
    [
        {SOURCE: regions[i], TARGET: regions[j], FLOW: flows[i, j], SIZE: sizes[i], TRACK: track_values[i]}
        for i in range(len(regions))
        for j in range(len(regions))
        if i != j
    ]
)

# Plot: reads only df and the constants above
names = list(pd.unique(pd.concat([df[SOURCE], df[TARGET]], ignore_index=True)))
# Segment attributes come from the rows where the segment is the source; others get the median
segments = df.drop_duplicates(SOURCE).set_index(SOURCE)[[SIZE, TRACK]].reindex(names)
segments = segments.fillna(segments.median())
n_segments = len(names)
position = {name: k for k, name in enumerate(names)}

available = 360 - GAP_DEG * n_segments
segment_angles = segments[SIZE].to_numpy() / segments[SIZE].sum() * available
start_angles = np.concatenate([[0], np.cumsum(segment_angles + GAP_DEG)[:-1]])
track_scale = segments[TRACK].to_numpy()

# Radii of the layers
outer_r = 1.0
inner_r = 0.85
ribbon_r = 0.80
track_r_outer = 0.78
track_r_inner = 0.60

fig = go.Figure()


def arc_band(theta_start, theta_end, r_out, r_in, n_points):
    """Closed polygon between two radii over an angular span (degrees)."""
    theta = np.radians(np.linspace(theta_start, theta_end, n_points))
    x = np.concatenate([r_out * np.cos(theta), r_in * np.cos(theta[::-1])])
    y = np.concatenate([r_out * np.sin(theta), r_in * np.sin(theta[::-1])])
    return np.append(x, x[0]), np.append(y, y[0])


# Outer ring segments with labels
for i, name in enumerate(names):
    mid_deg = start_angles[i] + segment_angles[i] / 2
    x_arc, y_arc = arc_band(start_angles[i], start_angles[i] + segment_angles[i], outer_r, inner_r, 50)
    fig.add_trace(
        go.Scatter(
            x=x_arc,
            y=y_arc,
            fill="toself",
            fillcolor=IMPRINT_PALETTE[i % len(IMPRINT_PALETTE)],
            line={"color": INK_SOFT, "width": 0.5},
            mode="lines",
            hoverinfo="name",
            name=name,
            showlegend=False,
        )
    )

    if 45 < mid_deg < 135:
        xanchor, yanchor = "center", "bottom"
    elif 225 < mid_deg < 315:
        xanchor, yanchor = "center", "top"
    elif mid_deg <= 45 or mid_deg >= 315:
        xanchor, yanchor = "left", "middle"
    else:
        xanchor, yanchor = "right", "middle"
    fig.add_annotation(
        x=(outer_r + 0.09) * np.cos(np.radians(mid_deg)),
        y=(outer_r + 0.09) * np.sin(np.radians(mid_deg)),
        text=name,
        showarrow=False,
        font={"size": 11, "color": INK},
        xanchor=xanchor,
        yanchor=yanchor,
    )

# Ribbons: one per pair, width proportional to the flow value
max_flow = df[FLOW].max()
cursor = np.zeros(n_segments)
for row in df.itertuples(index=False):
    i, j = position[row[0]], position[row[1]]
    value = row[2]
    if i >= j or not value > MIN_FLOW:
        continue
    width_i = value / max_flow * segment_angles[i] * 0.3
    width_j = value / max_flow * segment_angles[j] * 0.3
    i_start = start_angles[i] + cursor[i]
    j_start = start_angles[j] + cursor[j]
    cursor[i] += width_i + 1
    cursor[j] += width_j + 1

    theta_src = np.radians(np.linspace(i_start, i_start + width_i, 10))
    theta_tgt = np.radians(np.linspace(j_start, j_start + width_j, 10))
    x_src, y_src = ribbon_r * np.cos(theta_src), ribbon_r * np.sin(theta_src)
    x_tgt, y_tgt = ribbon_r * np.cos(theta_tgt), ribbon_r * np.sin(theta_tgt)

    # Quadratic Bezier edges pulled towards the centre
    t = np.linspace(0, 1, 30)

    def bezier(p0, p1, t=t):
        return (1 - t) ** 2 * p0 + 2 * (1 - t) * t * 0.2 * p0 + t**2 * p1

    x_ribbon = np.concatenate([x_src, bezier(x_src[-1], x_tgt[0]), x_tgt, bezier(x_tgt[-1], x_src[0]), [x_src[0]]])
    y_ribbon = np.concatenate([y_src, bezier(y_src[-1], y_tgt[0]), y_tgt, bezier(y_tgt[-1], y_src[0]), [y_src[0]]])

    # Ribbon colour: even blend of the two segment colours
    c1, c2 = IMPRINT_PALETTE[i % len(IMPRINT_PALETTE)], IMPRINT_PALETTE[j % len(IMPRINT_PALETTE)]
    mix = [(int(c1[k : k + 2], 16) + int(c2[k : k + 2], 16)) // 2 for k in (1, 3, 5)]
    fig.add_trace(
        go.Scatter(
            x=x_ribbon,
            y=y_ribbon,
            fill="toself",
            fillcolor=f"#{mix[0]:02x}{mix[1]:02x}{mix[2]:02x}",
            opacity=0.5,
            mode="lines",
            line={"color": INK_SOFT, "width": 0.3},
            hoverinfo="text",
            hovertext=f"{names[i]} ↔ {names[j]}: {value}",
            showlegend=False,
        )
    )

# Inner data track: bar height per segment
for i, name in enumerate(names):
    height = track_r_inner + (track_r_outer - track_r_inner) * track_scale[i] / track_scale.max()
    x_bar, y_bar = arc_band(start_angles[i], start_angles[i] + segment_angles[i], height, track_r_inner, 30)
    fig.add_trace(
        go.Scatter(
            x=x_bar,
            y=y_bar,
            fill="toself",
            fillcolor=IMPRINT_PALETTE[i % len(IMPRINT_PALETTE)],
            opacity=0.6,
            mode="lines",
            line={"color": INK_SOFT, "width": 0.3},
            hoverinfo="text",
            hovertext=f"{name} {TRACK}: {track_scale[i]:.2f}",
            showlegend=False,
        )
    )

# Caption explaining the layers
fig.add_annotation(
    xref="paper",
    yref="paper",
    x=0.5,
    y=0.0,
    yanchor="bottom",
    showarrow=False,
    text=f"Ribbons: {FLOW}, width ∝ value<br>Inner track: {TRACK}, bar height per region",
    font={"size": 10, "color": INK_SOFT},
    align="center",
)

# Style
fig.update_layout(
    autosize=False,
    width=600,
    height=600,
    title={"text": "circos-basic · python · plotly · anyplot.ai", "font": {"size": 16, "color": INK}, "x": 0.5},
    showlegend=False,
    xaxis={"visible": False, "range": [-1.5, 1.5], "scaleanchor": "y", "scaleratio": 1},
    yaxis={"visible": False, "range": [-1.2, 1.2]},
    plot_bgcolor=PAGE_BG,
    paper_bgcolor=PAGE_BG,
    margin={"l": 20, "r": 20, "t": 45, "b": 35},
)

fig.write_image(f"plot-{THEME}.png", width=600, height=600, scale=4)
fig.write_html(f"plot-{THEME}.html", include_plotlyjs="cdn")
