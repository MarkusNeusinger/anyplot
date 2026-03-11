""" pyplots.ai
scatter-ashby-material: Ashby Material Selection Chart
Library: bokeh 3.8.2 | Python 3.14.3
Quality: 83/100 | Created: 2026-03-11
"""

import numpy as np
import pandas as pd
from bokeh.io import export_png
from bokeh.models import ColumnDataSource, HoverTool, Label, Legend, LegendItem, Range1d
from bokeh.plotting import figure, save
from scipy.spatial import ConvexHull


np.random.seed(42)


# Data - realistic material properties (density kg/m³ vs Young's modulus GPa)
families = {
    "Metals": {
        "density": [
            2700,
            4500,
            7800,
            7900,
            8900,
            8500,
            7300,
            19300,
            1740,
            7200,
            2800,
            7600,
            8000,
            8700,
            7100,
            4600,
            8200,
            7400,
            7850,
            8100,
        ],
        "modulus": [69, 116, 210, 193, 117, 100, 45, 400, 44, 170, 73, 200, 195, 130, 90, 110, 205, 160, 215, 180],
    },
    "Polymers": {
        "density": [950, 1050, 1200, 1400, 1140, 900, 1300, 1070, 1240, 1350, 1420, 960, 1100, 1180, 1500],
        "modulus": [0.9, 2.5, 3.0, 2.8, 3.5, 1.3, 4.0, 2.0, 2.9, 3.8, 7.0, 0.4, 1.8, 2.2, 4.5],
    },
    "Ceramics": {
        "density": [3900, 3200, 2200, 3100, 5600, 3500, 2650, 3980, 6000, 2500, 3850, 3300, 5700, 2350, 3150],
        "modulus": [380, 310, 70, 200, 210, 270, 73, 400, 230, 95, 370, 290, 200, 62, 220],
    },
    "Composites": {
        "density": [1600, 1550, 2000, 1800, 1500, 1700, 1900, 1450, 1650, 2100, 1750, 1580, 1850, 1950, 2050],
        "modulus": [140, 70, 45, 90, 180, 100, 55, 200, 120, 40, 80, 150, 65, 50, 35],
    },
    "Elastomers": {
        "density": [1100, 920, 1250, 1500, 1150, 1050, 980, 1300, 1380, 1200],
        "modulus": [0.005, 0.002, 0.01, 0.05, 0.008, 0.003, 0.001, 0.02, 0.04, 0.015],
    },
    "Foams": {
        "density": [30, 60, 120, 200, 50, 80, 150, 35, 100, 250, 45, 70, 180, 25, 110],
        "modulus": [0.001, 0.01, 0.1, 0.3, 0.005, 0.02, 0.2, 0.002, 0.05, 0.5, 0.003, 0.015, 0.25, 0.0008, 0.08],
    },
    "Natural Materials": {
        "density": [600, 700, 500, 1500, 900, 450, 800, 650, 1100, 400, 750, 550, 1300, 850, 1000],
        "modulus": [12, 14, 8, 30, 10, 6, 11, 9, 25, 5, 16, 7, 20, 13, 18],
    },
}

# Colorblind-safe palette (avoids teal/blue confusion)
colors = {
    "Metals": "#306998",
    "Polymers": "#E8833A",
    "Ceramics": "#B5494E",
    "Composites": "#5BA05B",
    "Elastomers": "#9B6FB8",
    "Foams": "#C4A632",
    "Natural Materials": "#8B6C42",
}

# Emphasis levels for visual hierarchy (key structural families emphasized)
emphasis = {
    "Metals": {"fill_alpha": 0.20, "line_width": 3, "marker_size": 20},
    "Ceramics": {"fill_alpha": 0.18, "line_width": 2.5, "marker_size": 19},
    "Composites": {"fill_alpha": 0.16, "line_width": 2.5, "marker_size": 18},
    "Polymers": {"fill_alpha": 0.14, "line_width": 2, "marker_size": 17},
    "Natural Materials": {"fill_alpha": 0.12, "line_width": 2, "marker_size": 16},
    "Elastomers": {"fill_alpha": 0.12, "line_width": 1.5, "marker_size": 15},
    "Foams": {"fill_alpha": 0.12, "line_width": 1.5, "marker_size": 15},
}

rows = []
for family_name, props in families.items():
    for d, m in zip(props["density"], props["modulus"], strict=True):
        jitter_d = d * (1 + np.random.uniform(-0.08, 0.08))
        jitter_m = m * (1 + np.random.uniform(-0.12, 0.12))
        rows.append({"family": family_name, "density": jitter_d, "modulus": jitter_m, "color": colors[family_name]})

df = pd.DataFrame(rows)

# Plot
p = figure(
    width=4800,
    height=2700,
    x_axis_type="log",
    y_axis_type="log",
    x_axis_label="Density (kg/m\u00b3)",
    y_axis_label="Young's Modulus (GPa)",
    title="scatter-ashby-material \u00b7 bokeh \u00b7 pyplots.ai",
    x_range=Range1d(10, 50000),
    y_range=Range1d(0.0005, 1000),
    toolbar_location=None,
)

p.add_tools(
    HoverTool(tooltips=[("Family", "@family"), ("Density", "@x{0,0} kg/m\u00b3"), ("Modulus", "@y{0.000} GPa")])
)

# Performance index guide lines: E/rho = constant (lightweight stiffness)
# On log-log plot, E = C * rho is a line with slope 1
for c_val, label_text, lx, ly in [(0.01, "E/\u03c1 = 0.01", 5000, 0.01 * 5000), (1.0, "E/\u03c1 = 1", 500, 1.0 * 500)]:
    guide_x = [10, 50000]
    guide_y = [c_val * 10, c_val * 50000]
    p.line(guide_x, guide_y, line_color="#AAAAAA", line_width=1.5, line_dash="dashed", line_alpha=0.5)
    p.add_layout(
        Label(
            x=lx,
            y=ly,
            text=label_text,
            text_font_size="14pt",
            text_font_style="italic",
            text_color="#999999",
            text_alpha=0.7,
            x_offset=10,
            y_offset=-15,
        )
    )

# Label offset map to avoid overlap (manually tuned for known data positions)
label_offsets = {
    "Metals": (30, 20),
    "Ceramics": (-20, 30),
    "Composites": (0, 25),
    "Polymers": (0, -25),
    "Elastomers": (0, -20),
    "Foams": (-10, 20),
    "Natural Materials": (20, -20),
}

# Draw convex hull envelopes for each family
legend_items = []
for family_name in families:
    fam_df = df[df["family"] == family_name]
    log_x = np.log10(fam_df["density"].values)
    log_y = np.log10(fam_df["modulus"].values)
    color = colors[family_name]
    emph = emphasis[family_name]

    if len(fam_df) >= 3:
        pts = np.column_stack([log_x, log_y])
        hull = ConvexHull(pts)
        hull_indices = list(hull.vertices) + [hull.vertices[0]]
        hull_pts = pts[hull_indices]

        center_log_x = pts[hull.vertices, 0].mean()
        center_log_y = pts[hull.vertices, 1].mean()
        expanded = hull_pts.copy()
        for i in range(len(expanded)):
            dx = expanded[i, 0] - center_log_x
            dy = expanded[i, 1] - center_log_y
            expanded[i, 0] += dx * 0.15
            expanded[i, 1] += dy * 0.15

        hull_x = list(10 ** expanded[:, 0])
        hull_y = list(10 ** expanded[:, 1])

        p.patch(
            hull_x,
            hull_y,
            fill_alpha=emph["fill_alpha"],
            fill_color=color,
            line_color=color,
            line_alpha=0.5,
            line_width=emph["line_width"],
        )

        # Position label at top of hull to reduce overlap
        top_idx = np.argmax(pts[hull.vertices, 1])
        label_x = 10 ** pts[hull.vertices[top_idx], 0]
        label_y = 10 ** pts[hull.vertices[top_idx], 1]
        x_off, y_off = label_offsets.get(family_name, (0, 15))
        p.add_layout(
            Label(
                x=label_x,
                y=label_y,
                text=family_name,
                text_font_size="18pt",
                text_font_style="bold",
                text_color=color,
                text_alpha=0.85,
                x_offset=x_off,
                y_offset=y_off,
            )
        )

# Scatter points per family
for family_name in families:
    fam_df = df[df["family"] == family_name]
    source = ColumnDataSource(data={"x": fam_df["density"], "y": fam_df["modulus"], "family": fam_df["family"]})
    emph = emphasis[family_name]
    renderer = p.scatter(
        x="x",
        y="y",
        source=source,
        size=emph["marker_size"],
        color=colors[family_name],
        alpha=0.75,
        line_color="white",
        line_width=1.5,
    )
    legend_items.append(LegendItem(label=family_name, renderers=[renderer]))

# Add legend
legend = Legend(
    items=legend_items,
    location="top_right",
    label_text_font_size="16pt",
    glyph_height=20,
    glyph_width=20,
    spacing=10,
    padding=15,
    margin=20,
    background_fill_alpha=0.75,
    background_fill_color="#FFFFFF",
    border_line_alpha=0.3,
)
p.add_layout(legend, "right")

# Style
p.title.text_font_size = "28pt"
p.title.text_font_style = "normal"
p.xaxis.axis_label_text_font_size = "22pt"
p.yaxis.axis_label_text_font_size = "22pt"
p.xaxis.major_label_text_font_size = "18pt"
p.yaxis.major_label_text_font_size = "18pt"

p.xgrid.grid_line_alpha = 0.15
p.ygrid.grid_line_alpha = 0.15
p.xgrid.grid_line_width = 1
p.ygrid.grid_line_width = 1

p.outline_line_color = None
p.xaxis.minor_tick_line_color = None
p.yaxis.minor_tick_line_color = None
p.xaxis.major_tick_line_color = None
p.yaxis.major_tick_line_color = None
p.xaxis.axis_line_color = "#CCCCCC"
p.yaxis.axis_line_color = "#CCCCCC"

p.background_fill_color = "#FAFAFA"
p.border_fill_color = "#FFFFFF"

# Save
export_png(p, filename="plot.png")
save(p, filename="plot.html", title="Ashby Material Selection Chart")
