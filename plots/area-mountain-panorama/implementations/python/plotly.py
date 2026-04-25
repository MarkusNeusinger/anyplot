"""anyplot.ai
area-mountain-panorama: Mountain Panorama Profile with Labeled Peaks
Library: plotly | Python 3.13
Quality: pending | Created: 2026-04-25
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
GRID = "rgba(26,26,23,0.10)" if THEME == "light" else "rgba(240,239,232,0.10)"
BRAND = "#009E73"

# Data — Wallis (Valais) panorama: peaks ordered along a 0–180° angular sweep
peaks = [
    ("Weisshorn", 8, 4506),
    ("Zinalrothorn", 20, 4221),
    ("Ober Gabelhorn", 31, 4063),
    ("Dent Blanche", 42, 4358),
    ("Matterhorn", 58, 4478),
    ("Breithorn", 72, 4164),
    ("Pollux", 81, 4092),
    ("Castor", 89, 4223),
    ("Liskamm", 97, 4527),
    ("Dufourspitze", 109, 4634),
    ("Strahlhorn", 121, 4190),
    ("Rimpfischhorn", 132, 4199),
    ("Allalinhorn", 142, 4027),
    ("Alphubel", 152, 4206),
    ("Täschhorn", 162, 4491),
    ("Dom", 174, 4545),
]

# Build ridgeline control points: peaks alternating with saddles (cols)
np.random.seed(42)
ctrl_x = [-3.0]
ctrl_y = [3250.0]
for i, (_, ang, el) in enumerate(peaks):
    ctrl_x.append(float(ang))
    ctrl_y.append(float(el))
    if i < len(peaks) - 1:
        next_ang = peaks[i + 1][1]
        next_el = peaks[i + 1][2]
        col_ang = (ang + next_ang) / 2 + np.random.uniform(-1.2, 1.2)
        col_drop = np.random.uniform(420, 820)
        col_el = min(el, next_el) - col_drop
        ctrl_x.append(float(col_ang))
        ctrl_y.append(float(col_el))
ctrl_x.append(184.0)
ctrl_y.append(3350.0)

ctrl_x = np.array(ctrl_x)
ctrl_y = np.array(ctrl_y)

# Smooth ridgeline via cosine smoothstep between adjacent control points
ridge_x = []
ridge_y = []
for i in range(len(ctrl_x) - 1):
    n = 80
    last = i == len(ctrl_x) - 2
    t = np.linspace(0.0, 1.0, n, endpoint=last)
    s = 0.5 - 0.5 * np.cos(np.pi * t)
    ridge_x.append(ctrl_x[i] + (ctrl_x[i + 1] - ctrl_x[i]) * t)
    ridge_y.append(ctrl_y[i] + (ctrl_y[i + 1] - ctrl_y[i]) * s)
ridge_x = np.concatenate(ridge_x)
ridge_y = np.concatenate(ridge_y)

# Anchor the silhouette polygon at the lower edge of the visible y-range
Y_FLOOR = 2500
poly_x = np.concatenate([[ridge_x[0]], ridge_x, [ridge_x[-1]]])
poly_y = np.concatenate([[Y_FLOOR], ridge_y, [Y_FLOOR]])

# Plot
fig = go.Figure()

# Mountain silhouette (first categorical series — brand green)
fig.add_trace(
    go.Scatter(
        x=poly_x,
        y=poly_y,
        mode="lines",
        line={"color": BRAND, "width": 2},
        fill="toself",
        fillcolor=BRAND,
        hoverinfo="skip",
        showlegend=False,
    )
)

# Leader lines + peak markers + labels
LEVEL_TIERS = [4880, 5040, 5200]
annotations = []
for i, (name, ang, el) in enumerate(peaks):
    label_y = LEVEL_TIERS[i % 3]
    is_focal = name == "Matterhorn"

    # Leader line (thin, theme-adaptive)
    fig.add_trace(
        go.Scatter(
            x=[ang, ang],
            y=[el + 25, label_y - 80],
            mode="lines",
            line={"color": INK_SOFT, "width": 1},
            hoverinfo="skip",
            showlegend=False,
        )
    )

    # Summit dot (slightly larger for the focal peak)
    fig.add_trace(
        go.Scatter(
            x=[ang],
            y=[el],
            mode="markers",
            marker={"size": 10 if is_focal else 6, "color": INK if is_focal else INK_SOFT, "line": {"width": 0}},
            hoverinfo="skip",
            showlegend=False,
        )
    )

    # Label: name on top, elevation below
    name_size = 17 if is_focal else 14
    weight = "700" if is_focal else "600"
    annotations.append(
        {
            "x": ang,
            "y": label_y,
            "text": (
                f"<span style='font-size:{name_size}px;font-weight:{weight};color:{INK}'>{name}</span><br>"
                f"<span style='font-size:13px;color:{INK_MUTED}'>{el:,} m</span>"
            ),
            "showarrow": False,
            "align": "center",
            "xanchor": "center",
            "yanchor": "middle",
        }
    )

# Subtitle / footnote
annotations.append(
    {
        "x": 0.5,
        "y": 1.08,
        "xref": "paper",
        "yref": "paper",
        "text": f"<span style='color:{INK_SOFT}'>Wallis panorama — sixteen 4 000 m peaks of the Pennine Alps</span>",
        "showarrow": False,
        "font": {"size": 18},
        "xanchor": "center",
    }
)

fig.update_layout(
    title={
        "text": "area-mountain-panorama · plotly · anyplot.ai",
        "font": {"size": 28, "color": INK},
        "x": 0.5,
        "xanchor": "center",
        "y": 0.96,
    },
    annotations=annotations,
    paper_bgcolor=PAGE_BG,
    plot_bgcolor=PAGE_BG,
    font={"color": INK},
    xaxis={
        "range": [-3, 184],
        "showgrid": False,
        "showticklabels": False,
        "ticks": "",
        "zeroline": False,
        "showline": False,
        "fixedrange": True,
    },
    yaxis={
        "title": {"text": "Elevation (m)", "font": {"size": 22, "color": INK}},
        "tickfont": {"size": 18, "color": INK_SOFT},
        "tickvals": [2500, 3000, 3500, 4000, 4500, 5000],
        "ticksuffix": "  ",
        "gridcolor": GRID,
        "linecolor": INK_SOFT,
        "showgrid": True,
        "zeroline": False,
        "showline": False,
        "ticks": "",
        "range": [Y_FLOOR, 5400],
    },
    margin={"l": 120, "r": 80, "t": 160, "b": 60},
)

fig.write_image(f"plot-{THEME}.png", width=1600, height=900, scale=3)
fig.write_html(f"plot-{THEME}.html", include_plotlyjs="cdn")
