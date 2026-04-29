""" anyplot.ai
radar-basic: Basic Radar Chart
Library: altair 6.1.0 | Python 3.13.13
Quality: 83/100 | Updated: 2026-04-29
"""

import importlib
import os
import sys


# Prevent this file (altair.py) from shadowing the installed altair package
_here = os.path.realpath(os.path.dirname(__file__))
sys.path = [p for p in sys.path if not (p and os.path.realpath(p) == _here)]
del _here

alt = importlib.import_module("altair")
np = importlib.import_module("numpy")
pd = importlib.import_module("pandas")


THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
INK_MUTED = "#6B6A63" if THEME == "light" else "#A8A79F"

OKABE_ITO = ["#009E73", "#D55E00", "#0072B2", "#CC79A7", "#E69F00", "#56B4E9", "#F0E442"]

categories = ["Communication", "Technical Skills", "Teamwork", "Problem Solving", "Leadership", "Creativity"]
n = len(categories)
MAX_VAL = 100

alice_vals = [85, 90, 75, 88, 70, 82]
bob_vals = [72, 78, 88, 75, 85, 68]

angles = np.linspace(0, 2 * np.pi, n, endpoint=False).tolist()


def to_xy(values):
    scaled = [v / MAX_VAL for v in values]
    return (
        [s * np.cos(a - np.pi / 2) for s, a in zip(scaled, angles, strict=True)],
        [s * np.sin(a - np.pi / 2) for s, a in zip(scaled, angles, strict=True)],
    )


def to_xy_closed(values):
    x, y = to_xy(values)
    return x + [x[0]], y + [y[0]]


# Grid rings (hexagonal at 5 levels)
grid_data = []
for level in [20, 40, 60, 80, 100]:
    ls = level / MAX_VAL
    for i, angle in enumerate(angles):
        grid_data.append(
            {"x": ls * np.cos(angle - np.pi / 2), "y": ls * np.sin(angle - np.pi / 2), "level": level, "order": i}
        )
    grid_data.append(
        {"x": ls * np.cos(angles[0] - np.pi / 2), "y": ls * np.sin(angles[0] - np.pi / 2), "level": level, "order": n}
    )
df_grid = pd.DataFrame(grid_data)

# Spokes from center to outer edge
spokes_data = []
for cat, angle in zip(categories, angles, strict=True):
    spokes_data.extend(
        [
            {"x": 0.0, "y": 0.0, "cat": cat, "ord": 0},
            {"x": np.cos(angle - np.pi / 2), "y": np.sin(angle - np.pi / 2), "cat": cat, "ord": 1},
        ]
    )
df_spokes = pd.DataFrame(spokes_data)

# Outer axis labels
label_off = 1.24
df_labels = pd.DataFrame(
    [
        {"x": label_off * np.cos(a - np.pi / 2), "y": label_off * np.sin(a - np.pi / 2), "label": c}
        for c, a in zip(categories, angles, strict=True)
    ]
)

# Grid ring value annotations along the top (vertical) spoke
df_ring_labels = pd.DataFrame(
    [{"x": 0.05, "y": level / MAX_VAL, "label": str(level)} for level in [20, 40, 60, 80, 100]]
)

# Series line data (closed polygons for outlines)
series_line_rows = []
for name, vals in [("Alice", alice_vals), ("Bob", bob_vals)]:
    x_c, y_c = to_xy_closed(vals)
    for i, (x, y) in enumerate(zip(x_c, y_c, strict=True)):
        series_line_rows.append({"Employee": name, "x": x, "y": y, "order": i})
df_series_line = pd.DataFrame(series_line_rows)

# Series point data (unclosed, for tooltips and click selection)
pts_rows = []
for name, vals in [("Alice", alice_vals), ("Bob", bob_vals)]:
    x_p, y_p = to_xy(vals)
    for x, y, v, cat in zip(x_p, y_p, vals, categories, strict=True):
        pts_rows.append({"Employee": name, "x": x, "y": y, "value": v, "category": cat})
df_pts = pd.DataFrame(pts_rows)


# GeoJSON polygon helper
def make_geo(x_c, y_c):
    return {
        "type": "Feature",
        "geometry": {"type": "Polygon", "coordinates": [list(zip(x_c, y_c, strict=True))]},
        "properties": {},
    }


alice_x_c, alice_y_c = to_xy_closed(alice_vals)
bob_x_c, bob_y_c = to_xy_closed(bob_vals)

# Click-based interactive selection: click a vertex point to highlight its series
selection = alt.selection_point(fields=["Employee"])

color_scale = alt.Scale(domain=["Alice", "Bob"], range=[OKABE_ITO[0], OKABE_ITO[1]])

# Static grid rings
grid_lines = (
    alt.Chart(df_grid)
    .mark_line(strokeWidth=1.5, color=INK_SOFT, opacity=0.3)
    .encode(
        x=alt.X("x:Q", axis=None, scale=alt.Scale(domain=[-1.45, 1.45])),
        y=alt.Y("y:Q", axis=None, scale=alt.Scale(domain=[-1.45, 1.45])),
        detail="level:N",
        order="order:O",
    )
)

# Static spokes
spokes = (
    alt.Chart(df_spokes)
    .mark_line(strokeWidth=1, color=INK_SOFT, opacity=0.25)
    .encode(x=alt.X("x:Q", axis=None), y=alt.Y("y:Q", axis=None), detail="cat:N", order="ord:O")
)

# Static filled polygons (semi-transparent, one geoshape per series)
alice_fill = (
    alt.Chart(alt.Data(values=[make_geo(alice_x_c, alice_y_c)]))
    .mark_geoshape(fill=OKABE_ITO[0], fillOpacity=0.18, stroke="none")
    .project(type="identity", reflectY=True)
)

bob_fill = (
    alt.Chart(alt.Data(values=[make_geo(bob_x_c, bob_y_c)]))
    .mark_geoshape(fill=OKABE_ITO[1], fillOpacity=0.18, stroke="none")
    .project(type="identity", reflectY=True)
)

# Interactive polygon outlines — click a series to highlight it (dims the other)
series_lines = (
    alt.Chart(df_series_line)
    .mark_line(strokeWidth=3.5)
    .encode(
        x=alt.X("x:Q", axis=None),
        y=alt.Y("y:Q", axis=None),
        color=alt.Color(
            "Employee:N",
            scale=color_scale,
            legend=alt.Legend(
                title="Employee",
                titleFontSize=22,
                titleFontWeight="bold",
                labelFontSize=20,
                symbolSize=300,
                symbolStrokeWidth=4,
                orient="top-right",
                offset=10,
            ),
        ),
        detail="Employee:N",
        order="order:O",
        opacity=alt.condition(selection, alt.value(1.0), alt.value(0.15)),
    )
)

# Interactive vertex points with hover tooltips — click to select series
points = (
    alt.Chart(df_pts)
    .mark_point(filled=True, size=350)
    .encode(
        x=alt.X("x:Q"),
        y=alt.Y("y:Q"),
        color=alt.Color("Employee:N", scale=color_scale, legend=None),
        opacity=alt.condition(selection, alt.value(1.0), alt.value(0.10)),
        tooltip=[
            alt.Tooltip("Employee:N", title="Employee"),
            alt.Tooltip("category:N", title="Competency"),
            alt.Tooltip("value:Q", title="Score"),
        ],
    )
    .add_params(selection)
)

# Outer axis category labels
axis_labels = (
    alt.Chart(df_labels)
    .mark_text(fontSize=20, fontWeight="bold")
    .encode(x=alt.X("x:Q"), y=alt.Y("y:Q"), text="label:N", color=alt.value(INK))
)

# Grid ring value annotations (20, 40, 60, 80, 100) along the top spoke
ring_labels = (
    alt.Chart(df_ring_labels)
    .mark_text(fontSize=15, align="left")
    .encode(x=alt.X("x:Q"), y=alt.Y("y:Q"), text="label:N", color=alt.value(INK_MUTED))
)

chart = (
    alt.layer(grid_lines, spokes, alice_fill, bob_fill, series_lines, points, axis_labels, ring_labels)
    .properties(
        width=1200,
        height=1200,
        background=PAGE_BG,
        title=alt.Title(text="radar-basic · altair · anyplot.ai", fontSize=32, color=INK, fontWeight="bold", offset=24),
    )
    .configure_view(strokeWidth=0, fill=PAGE_BG)
    .configure_legend(
        fillColor=ELEVATED_BG,
        strokeColor=INK_SOFT,
        labelColor=INK_SOFT,
        titleColor=INK,
        labelFontSize=20,
        titleFontSize=22,
        padding=16,
        cornerRadius=4,
    )
)

chart.save(f"plot-{THEME}.png", scale_factor=3.0)
chart.save(f"plot-{THEME}.html")
