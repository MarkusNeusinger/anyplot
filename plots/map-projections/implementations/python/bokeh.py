""" pyplots.ai
map-projections: World Map with Different Projections
Library: bokeh 3.8.2 | Python 3.13.11
Quality: 90/100 | Created: 2026-01-20
"""

import numpy as np
from bokeh.io import export_png, save
from bokeh.layouts import column, gridplot
from bokeh.models import ColumnDataSource, Div, Legend, LegendItem, Title
from bokeh.plotting import figure
from bokeh.resources import CDN


np.random.seed(42)

# Latitude/longitude grid line positions (every 30 degrees)
lats_deg = np.arange(-90, 91, 30)
lons_deg = np.arange(-180, 181, 30)

# Tissot indicatrix positions
tissot_lats = [-60, -30, 0, 30, 60]
tissot_lons = [-150, -90, -30, 30, 90, 150]
tissot_radius_deg = 8

# Store all plot data for each projection
plots = []

# =============================================================================
# PROJECTION 1: Equirectangular (Plate Carrée)
# =============================================================================
p1 = figure(width=2400, height=1350, tools="", toolbar_location=None)
p1.add_layout(Title(text="Equirectangular (Plate Carrée)", text_font_size="40pt", align="center"), "above")

# Graticule lines for Equirectangular
grat1_x = []
grat1_y = []
for lon_d in lons_deg:
    lat_range = np.linspace(-85, 85, 100)
    lon_range = np.full_like(lat_range, lon_d)
    x = np.radians(lon_range)
    y = np.radians(lat_range)
    grat1_x.extend(list(x) + [np.nan])
    grat1_y.extend(list(y) + [np.nan])
for lat_d in lats_deg:
    lon_range = np.linspace(-180, 180, 200)
    lat_range = np.full_like(lon_range, lat_d)
    x = np.radians(lon_range)
    y = np.radians(lat_range)
    grat1_x.extend(list(x) + [np.nan])
    grat1_y.extend(list(y) + [np.nan])

grat1_source = ColumnDataSource(data={"x": grat1_x, "y": grat1_y})
grat_line1 = p1.line(x="x", y="y", source=grat1_source, line_color="#306998", line_width=2, line_alpha=0.6)

# Tissot indicatrices for Equirectangular
tissot1_x = []
tissot1_y = []
for lat_d in tissot_lats:
    for lon_d in tissot_lons:
        angles = np.linspace(0, 2 * np.pi, 50)
        circle_lons = lon_d + tissot_radius_deg * np.cos(angles)
        circle_lats = np.clip(lat_d + tissot_radius_deg * np.sin(angles), -85, 85)
        x = np.radians(circle_lons)
        y = np.radians(circle_lats)
        tissot1_x.extend(list(x) + [np.nan])
        tissot1_y.extend(list(y) + [np.nan])

tissot1_source = ColumnDataSource(data={"x": tissot1_x, "y": tissot1_y})
tissot_line1 = p1.line(x="x", y="y", source=tissot1_source, line_color="#FFD43B", line_width=3, line_alpha=0.9)
p1.patch(x=tissot1_x, y=tissot1_y, fill_color="#FFD43B", fill_alpha=0.3, line_color=None)

# Style
p1.xaxis.visible = False
p1.yaxis.visible = False
p1.xgrid.visible = False
p1.ygrid.visible = False
p1.background_fill_color = "#f5f5f5"
p1.border_fill_color = "#ffffff"
p1.outline_line_color = "#306998"
p1.outline_line_width = 2

# Add legend
legend1 = Legend(
    items=[
        LegendItem(label="Graticule (30° intervals)", renderers=[grat_line1]),
        LegendItem(label="Tissot Indicatrix (distortion)", renderers=[tissot_line1]),
    ],
    location="bottom_right",
    label_text_font_size="18pt",
    spacing=10,
    padding=15,
)
p1.add_layout(legend1)

plots.append(p1)

# =============================================================================
# PROJECTION 2: Mercator
# =============================================================================
p2 = figure(width=2400, height=1350, tools="", toolbar_location=None)
p2.add_layout(Title(text="Mercator", text_font_size="40pt", align="center"), "above")

# Graticule lines for Mercator
grat2_x = []
grat2_y = []
for lon_d in lons_deg:
    lat_range = np.linspace(-85, 85, 100)
    lon_range = np.full_like(lat_range, lon_d)
    lat_rad = np.radians(lat_range)
    lat_clipped = np.clip(lat_rad, -np.pi / 2 * 0.99, np.pi / 2 * 0.99)
    x = np.radians(lon_range)
    y = np.log(np.tan(np.pi / 4 + lat_clipped / 2))
    grat2_x.extend(list(x) + [np.nan])
    grat2_y.extend(list(y) + [np.nan])
for lat_d in lats_deg:
    lon_range = np.linspace(-180, 180, 200)
    lat_range = np.full_like(lon_range, lat_d)
    lat_rad = np.radians(lat_range)
    lat_clipped = np.clip(lat_rad, -np.pi / 2 * 0.99, np.pi / 2 * 0.99)
    x = np.radians(lon_range)
    y = np.log(np.tan(np.pi / 4 + lat_clipped / 2))
    grat2_x.extend(list(x) + [np.nan])
    grat2_y.extend(list(y) + [np.nan])

grat2_source = ColumnDataSource(data={"x": grat2_x, "y": grat2_y})
grat_line2 = p2.line(x="x", y="y", source=grat2_source, line_color="#306998", line_width=2, line_alpha=0.6)

# Tissot indicatrices for Mercator
tissot2_x = []
tissot2_y = []
for lat_d in tissot_lats:
    for lon_d in tissot_lons:
        angles = np.linspace(0, 2 * np.pi, 50)
        circle_lons = lon_d + tissot_radius_deg * np.cos(angles)
        circle_lats = np.clip(lat_d + tissot_radius_deg * np.sin(angles), -85, 85)
        lat_rad = np.radians(circle_lats)
        lat_clipped = np.clip(lat_rad, -np.pi / 2 * 0.99, np.pi / 2 * 0.99)
        x = np.radians(circle_lons)
        y = np.log(np.tan(np.pi / 4 + lat_clipped / 2))
        tissot2_x.extend(list(x) + [np.nan])
        tissot2_y.extend(list(y) + [np.nan])

tissot2_source = ColumnDataSource(data={"x": tissot2_x, "y": tissot2_y})
tissot_line2 = p2.line(x="x", y="y", source=tissot2_source, line_color="#FFD43B", line_width=3, line_alpha=0.9)
p2.patch(x=tissot2_x, y=tissot2_y, fill_color="#FFD43B", fill_alpha=0.3, line_color=None)

# Style
p2.xaxis.visible = False
p2.yaxis.visible = False
p2.xgrid.visible = False
p2.ygrid.visible = False
p2.background_fill_color = "#f5f5f5"
p2.border_fill_color = "#ffffff"
p2.outline_line_color = "#306998"
p2.outline_line_width = 2

plots.append(p2)

# =============================================================================
# PROJECTION 3: Sinusoidal
# =============================================================================
p3 = figure(width=2400, height=1350, tools="", toolbar_location=None)
p3.add_layout(Title(text="Sinusoidal", text_font_size="40pt", align="center"), "above")

# Graticule lines for Sinusoidal
grat3_x = []
grat3_y = []
for lon_d in lons_deg:
    lat_range = np.linspace(-85, 85, 100)
    lon_range = np.full_like(lat_range, lon_d)
    lat_rad = np.radians(lat_range)
    lon_rad = np.radians(lon_range)
    x = lon_rad * np.cos(lat_rad)
    y = lat_rad
    grat3_x.extend(list(x) + [np.nan])
    grat3_y.extend(list(y) + [np.nan])
for lat_d in lats_deg:
    lon_range = np.linspace(-180, 180, 200)
    lat_range = np.full_like(lon_range, lat_d)
    lat_rad = np.radians(lat_range)
    lon_rad = np.radians(lon_range)
    x = lon_rad * np.cos(lat_rad)
    y = lat_rad
    grat3_x.extend(list(x) + [np.nan])
    grat3_y.extend(list(y) + [np.nan])

grat3_source = ColumnDataSource(data={"x": grat3_x, "y": grat3_y})
grat_line3 = p3.line(x="x", y="y", source=grat3_source, line_color="#306998", line_width=2, line_alpha=0.6)

# Tissot indicatrices for Sinusoidal
tissot3_x = []
tissot3_y = []
for lat_d in tissot_lats:
    for lon_d in tissot_lons:
        angles = np.linspace(0, 2 * np.pi, 50)
        circle_lons = lon_d + tissot_radius_deg * np.cos(angles)
        circle_lats = np.clip(lat_d + tissot_radius_deg * np.sin(angles), -85, 85)
        lat_rad = np.radians(circle_lats)
        lon_rad = np.radians(circle_lons)
        x = lon_rad * np.cos(lat_rad)
        y = lat_rad
        tissot3_x.extend(list(x) + [np.nan])
        tissot3_y.extend(list(y) + [np.nan])

tissot3_source = ColumnDataSource(data={"x": tissot3_x, "y": tissot3_y})
tissot_line3 = p3.line(x="x", y="y", source=tissot3_source, line_color="#FFD43B", line_width=3, line_alpha=0.9)
p3.patch(x=tissot3_x, y=tissot3_y, fill_color="#FFD43B", fill_alpha=0.3, line_color=None)

# Style
p3.xaxis.visible = False
p3.yaxis.visible = False
p3.xgrid.visible = False
p3.ygrid.visible = False
p3.background_fill_color = "#f5f5f5"
p3.border_fill_color = "#ffffff"
p3.outline_line_color = "#306998"
p3.outline_line_width = 2

plots.append(p3)

# =============================================================================
# PROJECTION 4: Mollweide
# =============================================================================
p4 = figure(width=2400, height=1350, tools="", toolbar_location=None)
p4.add_layout(Title(text="Mollweide", text_font_size="40pt", align="center"), "above")

# Graticule lines for Mollweide
grat4_x = []
grat4_y = []
for lon_d in lons_deg:
    lat_range = np.linspace(-85, 85, 100)
    lon_range = np.full_like(lat_range, lon_d)
    lat_rad = np.radians(lat_range)
    lon_rad = np.radians(lon_range)
    # Newton-Raphson for Mollweide auxiliary angle
    theta = lat_rad.copy()
    for _ in range(10):
        delta = -(2 * theta + np.sin(2 * theta) - np.pi * np.sin(lat_rad)) / (2 + 2 * np.cos(2 * theta) + 1e-10)
        theta += delta
    x = (2 * np.sqrt(2) / np.pi) * lon_rad * np.cos(theta)
    y = np.sqrt(2) * np.sin(theta)
    grat4_x.extend(list(x) + [np.nan])
    grat4_y.extend(list(y) + [np.nan])
for lat_d in lats_deg:
    lon_range = np.linspace(-180, 180, 200)
    lat_range = np.full_like(lon_range, lat_d)
    lat_rad = np.radians(lat_range)
    lon_rad = np.radians(lon_range)
    theta = lat_rad.copy()
    for _ in range(10):
        delta = -(2 * theta + np.sin(2 * theta) - np.pi * np.sin(lat_rad)) / (2 + 2 * np.cos(2 * theta) + 1e-10)
        theta += delta
    x = (2 * np.sqrt(2) / np.pi) * lon_rad * np.cos(theta)
    y = np.sqrt(2) * np.sin(theta)
    grat4_x.extend(list(x) + [np.nan])
    grat4_y.extend(list(y) + [np.nan])

grat4_source = ColumnDataSource(data={"x": grat4_x, "y": grat4_y})
grat_line4 = p4.line(x="x", y="y", source=grat4_source, line_color="#306998", line_width=2, line_alpha=0.6)

# Tissot indicatrices for Mollweide
tissot4_x = []
tissot4_y = []
for lat_d in tissot_lats:
    for lon_d in tissot_lons:
        angles = np.linspace(0, 2 * np.pi, 50)
        circle_lons = lon_d + tissot_radius_deg * np.cos(angles)
        circle_lats = np.clip(lat_d + tissot_radius_deg * np.sin(angles), -85, 85)
        lat_rad = np.radians(circle_lats)
        lon_rad = np.radians(circle_lons)
        theta = lat_rad.copy()
        for _ in range(10):
            delta = -(2 * theta + np.sin(2 * theta) - np.pi * np.sin(lat_rad)) / (2 + 2 * np.cos(2 * theta) + 1e-10)
            theta += delta
        x = (2 * np.sqrt(2) / np.pi) * lon_rad * np.cos(theta)
        y = np.sqrt(2) * np.sin(theta)
        tissot4_x.extend(list(x) + [np.nan])
        tissot4_y.extend(list(y) + [np.nan])

tissot4_source = ColumnDataSource(data={"x": tissot4_x, "y": tissot4_y})
tissot_line4 = p4.line(x="x", y="y", source=tissot4_source, line_color="#FFD43B", line_width=3, line_alpha=0.9)
p4.patch(x=tissot4_x, y=tissot4_y, fill_color="#FFD43B", fill_alpha=0.3, line_color=None)

# Style
p4.xaxis.visible = False
p4.yaxis.visible = False
p4.xgrid.visible = False
p4.ygrid.visible = False
p4.background_fill_color = "#f5f5f5"
p4.border_fill_color = "#ffffff"
p4.outline_line_color = "#306998"
p4.outline_line_width = 2

plots.append(p4)

# =============================================================================
# Layout
# =============================================================================
grid = gridplot([[plots[0], plots[1]], [plots[2], plots[3]]], merge_tools=False)

# Main title with larger text
title_div = Div(
    text="<h1 style='text-align: center; font-size: 52pt; font-family: sans-serif; "
    "color: #306998; margin: 30px 0 15px 0; font-weight: bold;'>map-projections · bokeh · pyplots.ai</h1>"
    "<p style='text-align: center; font-size: 28pt; color: #555; margin-bottom: 20px;'>"
    "Yellow circles (Tissot indicatrices) reveal distortion: shape shows angular distortion, size shows area distortion. "
    "Blue graticule lines at 30° intervals.</p>",
    width=4800,
)

layout = column(title_div, grid)

# Save outputs
export_png(layout, filename="plot.png")
save(layout, filename="plot.html", resources=CDN, title="Map Projections - pyplots.ai")
