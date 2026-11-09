"""anyplot.ai
windbarb-basic: Wind Barb Plot for Meteorological Data
Library: plotly 7.1.0 | Python 3.14.10
Quality: 84/100 | Updated: 2026-11-09
"""

import os

import numpy as np
import pandas as pd
import plotly.graph_objects as go
from scipy.spatial.distance import cdist


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
GRID = "rgba(26,26,23,0.15)" if THEME == "light" else "rgba(240,239,232,0.15)"
BRAND = "#009E73"  # Imprint palette position 1: the barbs are the one data series

# Constants: the standard barb notation
CALM_KT = 2.5  # below this a station reports calm: an open circle and no staff
PENNANT_KT, FULL_KT, HALF_KT = 50, 10, 5  # what a pennant, a full barb and a half barb add
KEY_ROWS = [
    (0, "Calm, under 2.5 kt"),
    (5, "Half barb  5 kt"),
    (10, "Full barb  10 kt"),
    (50, "Pennant  50 kt"),
    (65, "50 + 10 + 5 = 65 kt"),
]

# Columns: set these to your table's column names
LON = "Longitude (°E)"  # role: x
LAT = "Latitude (°N)"  # role: y
U_WIND = "Zonal wind u (kt)"  # role: u
V_WIND = "Meridional wind v (kt)"  # role: v

# Data: replace this block with your own table, for example df = pd.read_csv("stations.csv")
# Surface wind observations from a 10 x 6 grid of stations over the North Sea and Denmark
np.random.seed(42)
col, row = (grid.flatten() for grid in np.meshgrid(np.arange(10), np.arange(6)))
lon, lat = 3.0 + col, 53.0 + row
u = 15 + 10 * np.sin(col * 0.5) + np.random.uniform(-5, 5, size=col.shape)
v = 5 + 8 * np.cos(row * 0.8) + np.random.uniform(-5, 5, size=row.shape)
# A gale off the north-west corner strengthens the flow there; a ridge in the south-east lets it fall calm
gale = 1 + 2.3 * np.exp(-((np.hypot(col, 5 - row) / 2.4) ** 2))
ridge = 1 - 0.98 * np.exp(-((np.hypot(9 - col, row) / 1.8) ** 2))
u, v = u * gale * ridge, v * gale * ridge
df = pd.DataFrame({LON: lon, LAT: lat, U_WIND: u, V_WIND: v})

# Plot: reads only df and the constants above; a station with a missing value has no barb to draw
stations = df.dropna(subset=[LON, LAT, U_WIND, V_WIND])
positions = stations[[LON, LAT]].to_numpy(dtype=float)
distances = cdist(positions, positions) + np.diag(np.full(len(positions), np.inf))
spacing = np.median(distances.min(axis=1))  # typical distance from a station to its nearest neighbour

# Barb geometry in data units, scaled to the station spacing: a staff of half the spacing
# leaves clear room between neighbouring barbs whose feathers lean toward each other
staff = 0.5 * spacing
feather = 0.52 * staff  # full barb and pennant height; a half barb is half of it
step = 0.17 * staff  # distance between feathers along the staff, over twice the stroke width
flag_base = 0.22 * staff
slant = 0.35  # feathers lean toward the staff's outer end, as drawn on synoptic charts
row_step = 0.8 * staff

# Two panels share the barb code: the station map, and the key's westerly samples at the same scale
key_x = np.full(len(KEY_ROWS), 1.2 * staff)
key_y = -row_step * np.arange(len(KEY_ROWS))
key_speeds = np.array([speed for speed, _ in KEY_ROWS], dtype=float)
panels = [
    ("x", "y", positions[:, 0], positions[:, 1], stations[U_WIND].to_numpy(float), stations[V_WIND].to_numpy(float)),
    ("x2", "y2", key_x, key_y, key_speeds, np.zeros(len(KEY_ROWS))),
]
hover = {"x": None, "x2": "skip"}  # only the map's stations answer a hover
drawn = {}

fig = go.Figure()
for xaxis, yaxis, xs, ys, us, vs in panels:
    axes = {"xaxis": xaxis, "yaxis": yaxis}
    speeds = np.hypot(us, vs)
    lines, flags = [], []
    for x0, y0, wind_u, wind_v, speed in zip(xs, ys, us, vs, speeds, strict=True):
        if speed < CALM_KT:
            continue
        rounded = HALF_KT * np.floor(speed / HALF_KT + 0.5)
        pennants, rest = divmod(rounded, PENNANT_KT)
        fulls, rest = divmod(rest, FULL_KT)
        into_wind = np.array([-wind_u, -wind_v]) / speed  # the staff points to where the wind comes from
        side = np.array([into_wind[1], -into_wind[0]])  # left of the wind's travel: Northern Hemisphere
        tip = np.array([x0, y0]) + staff * into_wind
        lines += [(x0, y0), tuple(tip), None]
        along = 0.0 if pennants or fulls else step  # a lone half barb sits one step in from the tip
        for _ in range(int(pennants)):
            outer = tip - along * into_wind
            flags += [tuple(outer), tuple(outer + feather * side), tuple(outer - flag_base * into_wind), None]
            along += flag_base
        # Clear staff between the pennant and the next barb, wide enough that the slanted barb stays off the triangle
        along += 1.6 * step if pennants and (fulls or rest) else 0.0
        for length in [feather] * int(fulls) + [feather / 2] * int(rest >= HALF_KT):
            root = tip - along * into_wind
            lines += [tuple(root), tuple(root + length * (side + slant * into_wind)), None]
            along += step
    drawn[xaxis] = np.array([point for point in lines + flags if point is not None] + list(zip(xs, ys, strict=True)))
    fig.add_trace(
        go.Scatter(
            x=[None if point is None else point[0] for point in lines],
            y=[None if point is None else point[1] for point in lines],
            mode="lines",
            line={"color": BRAND, "width": 2.4},
            hoverinfo="skip",
            showlegend=False,
            **axes,
        )
    )
    fig.add_trace(
        go.Scatter(
            x=[None if point is None else point[0] for point in flags],
            y=[None if point is None else point[1] for point in flags],
            mode="lines",
            fill="toself",
            fillcolor=BRAND,
            line={"color": BRAND, "width": 1},
            hoverinfo="skip",
            showlegend=False,
            **axes,
        )
    )
    # Stations: an open circle when calm, else a dot at the staff's foot that carries the reading
    calm = speeds < CALM_KT
    reading = np.column_stack([speeds, (270 - np.degrees(np.arctan2(vs, us))) % 360])
    for selected, marker in ((calm, {"symbol": "circle-open", "size": 11}), (~calm, {"size": 4})):
        fig.add_trace(
            go.Scatter(
                x=xs[selected],
                y=ys[selected],
                mode="markers",
                marker={**marker, "color": BRAND, "line": {"width": 2, "color": BRAND}},
                customdata=reading[selected],
                hovertemplate="%{customdata[0]:.0f} kt from %{customdata[1]:.0f}°<extra></extra>",
                hoverinfo=hover[xaxis],
                showlegend=False,
                **axes,
            )
        )

# Map extent: every station, staff, feather and pennant, padded by a fifth of the station spacing
pad = 0.2 * spacing
map_range = {axis: [drawn["x"][:, i].min() - pad, drawn["x"][:, i].max() + pad] for i, axis in enumerate("xy")}

# Key: each notation element drawn at the map's scale, labelled to its right
for (_, label), x, y in zip(KEY_ROWS, key_x, key_y, strict=True):
    fig.add_annotation(
        x=x,
        y=y,
        xref="x2",
        yref="y2",
        text=label,
        showarrow=False,
        xanchor="left",
        xshift=10,
        font={"size": 10, "color": INK_SOFT},
    )
fig.add_annotation(
    x=0,
    y=1,
    xref="x2 domain",
    yref="y2 domain",
    text="Barb key",
    showarrow=False,
    xanchor="left",
    yanchor="bottom",
    font={"size": 11, "color": INK},
)

# Style
fig.update_layout(
    autosize=False,
    width=800,
    height=450,
    margin={"l": 70, "r": 30, "t": 80, "b": 60},
    title={"text": "windbarb-basic · python · plotly · anyplot.ai", "font": {"size": 16, "color": INK}, "x": 0.5},
    paper_bgcolor=PAGE_BG,
    plot_bgcolor=PAGE_BG,
    font={"color": INK},
    showlegend=False,
    xaxis={
        "domain": [0, 0.78],
        "range": map_range["x"],
        "constrain": "domain",
        "title": {"text": LON, "font": {"size": 12, "color": INK}},
        "tickfont": {"size": 10, "color": INK_SOFT},
        "gridcolor": GRID,
        "zeroline": False,
        "showline": True,
        "linecolor": INK_SOFT,
        "ticks": "",
    },
    yaxis={
        "range": map_range["y"],
        "scaleanchor": "x",
        "scaleratio": 1,
        "constrain": "domain",
        "title": {"text": LAT, "font": {"size": 12, "color": INK}},
        "tickfont": {"size": 10, "color": INK_SOFT},
        "gridcolor": GRID,
        "zeroline": False,
        "showline": True,
        "linecolor": INK_SOFT,
        "ticks": "",
    },
    xaxis2={
        "domain": [0.82, 1],
        "anchor": "y2",
        "range": [0, 1.3 * staff],
        "scaleanchor": "x",
        "scaleratio": 1,
        "constrain": "range",
        "constraintoward": "left",
        "visible": False,
    },
    yaxis2={
        "domain": [0, 0.92],
        "anchor": "x2",
        "range": [-row_step * (len(KEY_ROWS) - 1) - 0.3 * staff, feather + 0.1 * staff],
        "scaleanchor": "x2",
        "scaleratio": 1,
        "constrain": "range",
        "constraintoward": "top",
        "visible": False,
    },
)

# Save
fig.write_image(f"plot-{THEME}.png", width=800, height=450, scale=4)
fig.write_html(f"plot-{THEME}.html", include_plotlyjs="cdn")
