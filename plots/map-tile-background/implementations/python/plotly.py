"""anyplot.ai
map-tile-background: Map with Tile Background
Library: plotly 7.1.0 | Python 3.14.10
Quality: pending | Updated: 2026-11-26
"""

import os
import sys


# Remove this script's directory from sys.path so "plotly.py" doesn't shadow
# the installed plotly package when Python prepends the script dir.
_script_dir = os.path.dirname(os.path.abspath(__file__))
sys.path = [p for p in sys.path if os.path.abspath(p) != _script_dir]

import numpy as np
import pandas as pd
import plotly.graph_objects as go


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Imprint palette: brand green first
BRAND = "#009E73"

# Imprint sequential ramp for colored marks, per theme
SEQ_MARKS = (
    [[0.0, "#009E73"], [0.687, "#024582"], [1.0, "#351E45"]]
    if THEME == "light"
    else [[0.0, "#6F7E20"], [0.21, "#009E73"], [1.0, "#CDD9FF"]]
)

# Theme-adaptive map tile style (tile providers do not follow the page colors)
MAP_STYLE = "open-street-map" if THEME == "light" else "carto-darkmatter"

# Columns: set these to your table's column names
TRAILHEAD = "Trailhead"  # role: label
LAT = "Latitude"  # role: lat
LON = "Longitude"  # role: lon
HIKERS = "Annual hikers (thousands)"  # role: value
LABEL_SIDE = "Label side"  # role: label position

# Data: replace this block with your own table, for example df = pd.read_csv("trailheads.csv")
df = pd.DataFrame(
    {
        TRAILHEAD: [
            "Angels Landing",
            "Half Dome",
            "Bright Angel",
            "Delicate Arch",
            "Cascade Pass",
            "Mount Whitney",
            "Grinnell Glacier",
            "Skyline Trail",
            "Hoh River",
            "Mount Washburn",
            "Bear Lake",
            "Cleetwood Cove",
            "Jenny Lake",
        ],
        LAT: [
            37.2590,
            37.7326,
            36.0576,
            38.7436,
            48.4730,
            36.5786,
            48.7966,
            46.7860,
            47.8602,
            44.7920,
            40.3126,
            42.9690,
            43.7513,
        ],
        LON: [
            -112.9511,
            -119.5577,
            -112.1401,
            -109.4993,
            -121.0750,
            -118.2292,
            -113.7180,
            -121.7350,
            -123.9350,
            -110.4330,
            -105.6450,
            -122.0070,
            -110.7242,
        ],
        HIKERS: [250, 50, 650, 450, 30, 100, 120, 380, 90, 200, 550, 150, 480],
        LABEL_SIDE: [
            "right",
            "left",
            "right",
            "right",
            "right",
            "left",
            "right",
            "right",
            "right",
            "top",
            "left",
            "right",
            "right",
        ],
    }
)

# Plot: reads only df and the constants above
# View fitted to the data bounds: pick the zoom at which both spans fit the map area
WIDTH, HEIGHT = 800, 450
MAP_W, MAP_H = WIDTH - 40, HEIGHT - 70
PAD = 1.2


lon_span = df[LON].max() - df[LON].min()
merc_y = np.degrees(np.log(np.tan(np.pi / 4 + np.radians(df[LAT]) / 2)))
merc_span = merc_y.max() - merc_y.min()
zoom = min(np.log2(360 * MAP_W / (512 * lon_span * PAD)), np.log2(360 * MAP_H / (512 * merc_span * PAD)))
center = {"lat": float(df[LAT].mean()), "lon": float((df[LON].max() + df[LON].min()) / 2)}

# Marker diameters (12-28 px) scale with the visitor count
size = 12 + (df[HIKERS] - df[HIKERS].min()) / (df[HIKERS].max() - df[HIKERS].min()) * 16

fig = go.Figure()

# Halo in the page color keeps each marker separated from busy tiles
fig.add_trace(
    go.Scattermap(
        lat=df[LAT],
        lon=df[LON],
        mode="markers",
        marker={"size": size + 4, "color": PAGE_BG, "opacity": 0.9},
        hoverinfo="skip",
        showlegend=False,
    )
)

# Colored markers carry the value, hover and the colorbar
fig.add_trace(
    go.Scattermap(
        lat=df[LAT],
        lon=df[LON],
        mode="markers",
        marker={
            "size": size,
            "color": df[HIKERS],
            "colorscale": SEQ_MARKS,
            "cmin": df[HIKERS].min(),
            "cmax": df[HIKERS].max(),
            "opacity": 0.92,
            "colorbar": {
                "title": {"text": HIKERS, "side": "right", "font": {"size": 12, "color": INK}},
                "tickfont": {"size": 11, "color": INK_SOFT},
                "bgcolor": ELEVATED_BG,
                "bordercolor": INK_SOFT,
                "borderwidth": 1,
                "thickness": 18,
                "len": 0.6,
                "x": 0.995,
                "xanchor": "right",
                "y": 0.62,
            },
        },
        text=df[TRAILHEAD],
        hovertemplate="<b>%{text}</b><br>" + HIKERS + ": %{marker.color:,.0f}<extra></extra>",
        showlegend=False,
    )
)

# Labels are layout annotations at the markers' map pixel positions: MapLibre drops colliding
# symbol labels, so a point could lose its name. Each sits just outside its marker's radius.
center_y = np.degrees(np.log(np.tan(np.pi / 4 + np.radians(center["lat"]) / 2)))
px_per_deg = 512 * 2**zoom / 360
label_x = 0.5 + (df[LON] - center["lon"]) * px_per_deg / MAP_W
label_y = 0.5 + (merc_y - center_y) * px_per_deg / MAP_H
anchors = {"right": ("left", "middle", 1, 0), "left": ("right", "middle", -1, 0), "top": ("center", "bottom", 0, 1)}
labels = []
for name, x, y, side_, radius in zip(df[TRAILHEAD], label_x, label_y, df[LABEL_SIDE], size / 2 + 4, strict=True):
    xanchor, yanchor, dx, dy = anchors[side_]
    labels.append(
        {
            "text": name,
            "xref": "paper",
            "yref": "paper",
            "x": x,
            "y": y,
            "xanchor": xanchor,
            "yanchor": yanchor,
            "xshift": dx * radius,
            "yshift": dy * radius,
            "showarrow": False,
            "font": {"size": 12, "color": INK},
            "bgcolor": PAGE_BG,
            "opacity": 0.95,
            "borderpad": 1,
        }
    )

top = df.loc[df[HIKERS].idxmax()]
title = "Western US Trailheads by Annual Hikers · map-tile-background · python · plotly · anyplot.ai"
title_size = round(16 * min(1.0, 67 / len(title)))

fig.update_layout(
    autosize=False,
    paper_bgcolor=PAGE_BG,
    font={"color": INK},
    title={"text": title, "font": {"size": max(title_size, 12), "color": INK}, "x": 0.5, "xanchor": "center"},
    map={"style": MAP_STYLE, "center": center, "zoom": float(zoom)},
    margin={"l": 20, "r": 20, "t": 50, "b": 20},
    annotations=[
        *labels,
        {
            "text": f"<b>★ Busiest trailhead</b><br>{top[TRAILHEAD]} · {top[HIKERS]:,.0f}k hikers/yr",
            "xref": "paper",
            "yref": "paper",
            "x": 0.015,
            "y": 0.03,
            "xanchor": "left",
            "yanchor": "bottom",
            "showarrow": False,
            "font": {"size": 12, "color": INK},
            "bgcolor": ELEVATED_BG,
            "bordercolor": BRAND,
            "borderwidth": 2,
            "borderpad": 6,
            "align": "left",
        },
    ],
)

fig.write_image(f"plot-{THEME}.png", width=WIDTH, height=HEIGHT, scale=4)
fig.write_html(f"plot-{THEME}.html", include_plotlyjs="cdn")
