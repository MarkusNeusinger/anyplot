""" pyplots.ai
star-chart-constellation: Star Chart with Constellations
Library: highcharts unknown | Python 3.14.3
Quality: 91/100 | Created: 2026-03-18
"""

import math
import tempfile
import time
import urllib.request
from pathlib import Path

import numpy as np
from highcharts_core.chart import Chart
from highcharts_core.options import HighchartsOptions
from highcharts_core.options.series.scatter import ScatterSeries
from highcharts_core.options.series.spline import SplineSeries
from selenium import webdriver
from selenium.webdriver.chrome.options import Options


np.random.seed(42)


# --- Star catalog: (name, RA hours, Dec degrees, apparent magnitude, constellation) ---
star_catalog = [
    # Orion
    ("Betelgeuse", 5.92, 7.41, 0.42, "Ori"),
    ("Rigel", 5.24, -8.20, 0.13, "Ori"),
    ("Bellatrix", 5.42, 6.35, 1.64, "Ori"),
    ("Mintaka", 5.53, -0.30, 2.23, "Ori"),
    ("Alnilam", 5.60, -1.20, 1.69, "Ori"),
    ("Alnitak", 5.68, -1.94, 1.77, "Ori"),
    ("Saiph", 5.80, -9.67, 2.09, "Ori"),
    # Ursa Major (Big Dipper)
    ("Dubhe", 11.06, 61.75, 1.79, "UMa"),
    ("Merak", 11.03, 56.38, 2.37, "UMa"),
    ("Phecda", 11.90, 53.69, 2.44, "UMa"),
    ("Megrez", 12.26, 57.03, 3.31, "UMa"),
    ("Alioth", 12.90, 55.96, 1.77, "UMa"),
    ("Mizar", 13.40, 54.93, 2.27, "UMa"),
    ("Alkaid", 13.79, 49.31, 1.86, "UMa"),
    # Cassiopeia
    ("Schedar", 0.68, 56.54, 2.23, "Cas"),
    ("Caph", 0.15, 59.15, 2.27, "Cas"),
    ("Gamma Cas", 0.95, 60.72, 2.47, "Cas"),
    ("Ruchbah", 1.36, 60.24, 2.68, "Cas"),
    ("Segin", 1.91, 63.67, 3.37, "Cas"),
    # Leo
    ("Regulus", 10.14, 11.97, 1.35, "Leo"),
    ("Denebola", 11.82, 14.57, 2.13, "Leo"),
    ("Algieba", 10.33, 19.84, 2.28, "Leo"),
    ("Zosma", 11.24, 20.52, 2.56, "Leo"),
    ("Chertan", 11.24, 15.43, 3.33, "Leo"),
    ("Eta Leo", 10.12, 16.76, 3.52, "Leo"),
    # Cygnus
    ("Deneb", 20.69, 45.28, 1.25, "Cyg"),
    ("Sadr", 20.37, 40.26, 2.20, "Cyg"),
    ("Gienah Cyg", 20.77, 33.97, 2.46, "Cyg"),
    ("Delta Cyg", 19.75, 45.13, 2.87, "Cyg"),
    ("Albireo", 19.51, 27.96, 3.08, "Cyg"),
    # Lyra
    ("Vega", 18.62, 38.78, 0.03, "Lyr"),
    ("Sheliak", 18.83, 33.36, 3.45, "Lyr"),
    ("Sulafat", 18.98, 32.69, 3.24, "Lyr"),
    # Gemini
    ("Pollux", 7.76, 28.03, 1.14, "Gem"),
    ("Castor", 7.58, 31.89, 1.58, "Gem"),
    ("Alhena", 6.63, 16.40, 1.93, "Gem"),
    ("Wasat", 7.07, 21.98, 3.53, "Gem"),
    ("Mebsuta", 6.73, 25.13, 2.98, "Gem"),
    ("Tejat", 6.38, 22.51, 2.88, "Gem"),
    # Taurus
    ("Aldebaran", 4.60, 16.51, 0.85, "Tau"),
    ("Elnath", 5.44, 28.61, 1.65, "Tau"),
    ("Alcyone", 3.79, 24.11, 2.87, "Tau"),
    ("Tianguan", 5.63, 21.14, 3.00, "Tau"),
    # Scorpius
    ("Antares", 16.49, -26.43, 0.96, "Sco"),
    ("Shaula", 17.56, -37.10, 1.63, "Sco"),
    ("Sargas", 17.62, -42.99, 1.87, "Sco"),
    ("Dschubba", 16.01, -22.62, 2.32, "Sco"),
    ("Graffias", 16.09, -19.81, 2.62, "Sco"),
    ("Lesath", 17.53, -37.29, 2.69, "Sco"),
    # Bootes
    ("Arcturus", 14.26, 19.18, -0.05, "Boo"),
    ("Izar", 14.75, 27.07, 2.37, "Boo"),
    ("Muphrid", 13.91, 18.40, 2.68, "Boo"),
    ("Nekkar", 15.03, 40.39, 3.50, "Boo"),
    # Aquila
    ("Altair", 19.85, 8.87, 0.77, "Aql"),
    ("Tarazed", 19.77, 10.61, 2.72, "Aql"),
    ("Alshain", 19.92, 6.41, 3.71, "Aql"),
    # Canis Major
    ("Sirius", 6.75, -16.72, -1.46, "CMa"),
    ("Adhara", 6.98, -28.97, 1.50, "CMa"),
    ("Wezen", 7.14, -26.39, 1.84, "CMa"),
    ("Mirzam", 6.38, -17.96, 1.98, "CMa"),
    ("Aludra", 7.40, -29.30, 2.45, "CMa"),
    # Auriga
    ("Capella", 5.28, 46.00, 0.08, "Aur"),
    ("Menkalinan", 5.99, 44.95, 1.90, "Aur"),
    ("Mahasim", 5.03, 41.08, 3.17, "Aur"),
    ("Hassaleh", 4.95, 33.17, 2.69, "Aur"),
    # Perseus
    ("Mirfak", 3.41, 49.86, 1.79, "Per"),
    ("Algol", 3.14, 40.96, 2.12, "Per"),
    ("Zeta Per", 3.90, 31.88, 2.85, "Per"),
    ("Epsilon Per", 3.96, 40.01, 2.89, "Per"),
    # Andromeda
    ("Alpheratz", 0.14, 29.09, 2.06, "And"),
    ("Mirach", 1.16, 35.62, 2.05, "And"),
    ("Almach", 2.06, 42.33, 2.17, "And"),
]

constellation_edges = [
    # Orion
    ("Betelgeuse", "Bellatrix"),
    ("Betelgeuse", "Mintaka"),
    ("Bellatrix", "Mintaka"),
    ("Mintaka", "Alnilam"),
    ("Alnilam", "Alnitak"),
    ("Alnitak", "Saiph"),
    ("Mintaka", "Rigel"),
    ("Rigel", "Saiph"),
    # Ursa Major
    ("Dubhe", "Merak"),
    ("Merak", "Phecda"),
    ("Phecda", "Megrez"),
    ("Megrez", "Alioth"),
    ("Alioth", "Mizar"),
    ("Mizar", "Alkaid"),
    ("Megrez", "Dubhe"),
    # Cassiopeia
    ("Caph", "Schedar"),
    ("Schedar", "Gamma Cas"),
    ("Gamma Cas", "Ruchbah"),
    ("Ruchbah", "Segin"),
    # Leo
    ("Regulus", "Eta Leo"),
    ("Eta Leo", "Algieba"),
    ("Algieba", "Zosma"),
    ("Zosma", "Denebola"),
    ("Regulus", "Chertan"),
    ("Chertan", "Denebola"),
    # Cygnus
    ("Deneb", "Sadr"),
    ("Sadr", "Gienah Cyg"),
    ("Sadr", "Delta Cyg"),
    ("Sadr", "Albireo"),
    # Lyra
    ("Vega", "Sheliak"),
    ("Vega", "Sulafat"),
    ("Sheliak", "Sulafat"),
    # Gemini
    ("Castor", "Pollux"),
    ("Castor", "Mebsuta"),
    ("Mebsuta", "Tejat"),
    ("Pollux", "Wasat"),
    ("Wasat", "Alhena"),
    ("Tejat", "Alhena"),
    # Taurus
    ("Aldebaran", "Tianguan"),
    ("Tianguan", "Elnath"),
    ("Aldebaran", "Alcyone"),
    # Scorpius
    ("Graffias", "Dschubba"),
    ("Dschubba", "Antares"),
    ("Antares", "Shaula"),
    ("Shaula", "Lesath"),
    ("Shaula", "Sargas"),
    # Bootes
    ("Arcturus", "Izar"),
    ("Arcturus", "Muphrid"),
    ("Izar", "Nekkar"),
    # Aquila
    ("Altair", "Tarazed"),
    ("Altair", "Alshain"),
    # Canis Major
    ("Sirius", "Mirzam"),
    ("Sirius", "Wezen"),
    ("Wezen", "Adhara"),
    ("Wezen", "Aludra"),
    # Auriga
    ("Capella", "Menkalinan"),
    ("Capella", "Mahasim"),
    ("Mahasim", "Hassaleh"),
    # Perseus
    ("Mirfak", "Algol"),
    ("Mirfak", "Epsilon Per"),
    ("Epsilon Per", "Zeta Per"),
    # Andromeda
    ("Alpheratz", "Mirach"),
    ("Mirach", "Almach"),
]

# Project star positions
star_names = [s[0] for s in star_catalog]
ra_hours = np.array([s[1] for s in star_catalog])
dec_deg = np.array([s[2] for s in star_catalog])
magnitudes = np.array([s[3] for s in star_catalog])
constellations = [s[4] for s in star_catalog]

ra_deg = ra_hours * 15.0
# Azimuthal equidistant projection from north pole: r = 90 - dec, RA=0h at top
ra_rad = np.radians(ra_deg)
proj_r = 90.0 - dec_deg
proj_x = proj_r * np.sin(ra_rad)
proj_y = proj_r * np.cos(ra_rad)

# Magnitude to marker radius (brighter = larger)
mag_min, mag_max = magnitudes.min(), magnitudes.max()
radius_min, radius_max = 5, 30
star_radii = radius_min + (radius_max - radius_min) * (1 - (magnitudes - mag_min) / (mag_max - mag_min))
star_opacity = 0.5 + 0.5 * (1 - (magnitudes - mag_min) / (mag_max - mag_min))

star_lookup = {s[0]: i for i, s in enumerate(star_catalog)}

constellation_names = {
    "Ori": "Orion",
    "UMa": "Ursa Major",
    "Cas": "Cassiopeia",
    "Leo": "Leo",
    "Cyg": "Cygnus",
    "Lyr": "Lyra",
    "Gem": "Gemini",
    "Tau": "Taurus",
    "Sco": "Scorpius",
    "Boo": "Boötes",
    "Aql": "Aquila",
    "CMa": "Canis Major",
    "Aur": "Auriga",
    "Per": "Perseus",
    "And": "Andromeda",
}

# Colorblind-safe palette: maximise hue diversity, distinct for deuteranopia/protanopia
constellation_colors = {
    "Ori": "#6EC6FF",  # sky blue
    "UMa": "#FFD54F",  # gold
    "Cas": "#CE93D8",  # orchid purple
    "Leo": "#FF8A65",  # coral orange
    "Cyg": "#66BB6A",  # green
    "Lyr": "#26C6DA",  # teal cyan
    "Gem": "#C5E1A5",  # lime
    "Tau": "#A1887F",  # warm taupe (was amber — too close to gold)
    "Sco": "#EF5350",  # red
    "Boo": "#80CBC4",  # mint teal
    "Aql": "#42A5F5",  # medium blue
    "CMa": "#B3E5FC",  # ice blue
    "Aur": "#E0E0E0",  # silver (was lemon yellow — too close to gold)
    "Per": "#B39DDB",  # lavender
    "And": "#F48FB1",  # pink
}

# Chart boundary radius (dec = -50 → r = 140)
R_BOUNDARY = 140
AXIS_RANGE = 155  # Axis range with margin for labels

# --- Build chart ---
chart = Chart(container="container")
chart.options = HighchartsOptions()

chart.options.chart = {
    "type": "scatter",
    "width": 3600,
    "height": 3600,
    "backgroundColor": "#0a0e1a",
    "style": {"fontFamily": "'Segoe UI', Helvetica, Arial, sans-serif"},
    "marginTop": 160,
    "marginBottom": 80,
    "marginLeft": 80,
    "marginRight": 80,
    "plotBackgroundColor": {
        "radialGradient": {"cx": 0.5, "cy": 0.5, "r": 0.5},
        "stops": [[0, "#0d1326"], [0.7, "#080c1a"], [1, "#050810"]],
    },
}

chart.options.title = {
    "text": "star-chart-constellation · highcharts · pyplots.ai",
    "style": {"fontSize": "52px", "fontWeight": "600", "color": "#c8d6e5", "letterSpacing": "1px"},
    "margin": 20,
}

chart.options.subtitle = {
    "text": (
        "Azimuthal Equidistant Projection — North Celestial Pole at Center<br>15 Constellations · 70+ Stars to mag 3.7"
    ),
    "style": {"fontSize": "30px", "color": "#576574", "fontWeight": "400"},
    "useHTML": True,
}

# Axes: hidden but used for coordinate positioning
chart.options.x_axis = {"min": -AXIS_RANGE, "max": AXIS_RANGE, "visible": False, "gridLineWidth": 0}

chart.options.y_axis = {"min": -AXIS_RANGE, "max": AXIS_RANGE, "visible": False, "gridLineWidth": 0}

chart.options.legend = {"enabled": False}
chart.options.credits = {"enabled": False}
chart.options.tooltip = {
    "headerFormat": "",
    "pointFormat": (
        '<span style="font-size:22px;color:{point.color}">★</span> '
        '<span style="font-size:24px;color:#c8d6e5">'
        "<b>{point.name}</b><br/>"
        "RA: {point.raStr} · Dec: {point.decStr}<br/>"
        "Magnitude: {point.mag:.2f}</span>"
    ),
    "backgroundColor": "rgba(10, 14, 26, 0.92)",
    "borderColor": "#4FC3F7",
    "borderRadius": 8,
    "borderWidth": 1,
    "style": {"fontSize": "24px", "color": "#c8d6e5"},
}

# --- Declination grid circles ---
grid_color = "rgba(99, 128, 160, 0.15)"
for dec_val in [-30, 0, 30, 60]:
    r = 90.0 - dec_val
    pts = []
    for angle in np.linspace(0, 2 * math.pi, 200):
        pts.append([round(r * math.sin(angle), 2), round(r * math.cos(angle), 2)])
    pts.append(pts[0])  # close circle
    grid_circle = SplineSeries()
    grid_circle.data = pts
    grid_circle.color = grid_color
    grid_circle.line_width = 1
    grid_circle.dash_style = "Dot"
    grid_circle.marker = {"enabled": False}
    grid_circle.enable_mouse_tracking = False
    grid_circle.show_in_legend = False
    grid_circle.z_index = 0
    chart.add_series(grid_circle)

# --- RA grid lines (every 3 hours = 45°) ---
for ra_h in range(0, 24, 3):
    ra_rad = math.radians(ra_h * 15)
    r_inner = 0
    r_outer = R_BOUNDARY
    line = SplineSeries()
    line.data = [
        [round(r_inner * math.sin(ra_rad), 2), round(r_inner * math.cos(ra_rad), 2)],
        [round(r_outer * math.sin(ra_rad), 2), round(r_outer * math.cos(ra_rad), 2)],
    ]
    line.color = grid_color
    line.line_width = 1
    line.dash_style = "Dot"
    line.marker = {"enabled": False}
    line.enable_mouse_tracking = False
    line.show_in_legend = False
    line.z_index = 0
    chart.add_series(line)

# --- Circular sky boundary ---
boundary_pts = []
for angle in np.linspace(0, 2 * math.pi, 360):
    boundary_pts.append([round(R_BOUNDARY * math.sin(angle), 2), round(R_BOUNDARY * math.cos(angle), 2)])
boundary_pts.append(boundary_pts[0])
boundary = SplineSeries()
boundary.data = boundary_pts
boundary.color = "rgba(99, 128, 160, 0.4)"
boundary.line_width = 2
boundary.marker = {"enabled": False}
boundary.enable_mouse_tracking = False
boundary.show_in_legend = False
boundary.z_index = 1
chart.add_series(boundary)

# --- Grid labels: RA hours at boundary edge ---
ra_label_data = []
label_r = R_BOUNDARY + 8
for ra_h in range(0, 24, 3):
    ra_rad = math.radians(ra_h * 15)
    lx = round(label_r * math.sin(ra_rad), 2)
    ly = round(label_r * math.cos(ra_rad), 2)
    ra_label_data.append(
        {
            "x": lx,
            "y": ly,
            "name": f"{ra_h}h",
            "dataLabels": {
                "enabled": True,
                "format": f"{ra_h}h",
                "style": {"fontSize": "24px", "color": "#576574", "textOutline": "2px #0a0e1a", "fontWeight": "500"},
                "y": 0,
            },
            "marker": {"radius": 0, "states": {"hover": {"enabled": False}}},
        }
    )

ra_labels = ScatterSeries()
ra_labels.data = ra_label_data
ra_labels.name = "RA Labels"
ra_labels.color = "rgba(0,0,0,0)"
ra_labels.enable_mouse_tracking = False
ra_labels.show_in_legend = False
ra_labels.z_index = 5
ra_labels.marker = {"radius": 0}
chart.add_series(ra_labels)

# --- Grid labels: Declination along RA=0h line (top) ---
dec_label_data = []
for dec_val in [-30, 0, 30, 60]:
    r = 90.0 - dec_val
    dec_label_data.append(
        {
            "x": 5,
            "y": r,
            "name": f"{dec_val:+d}°",
            "dataLabels": {
                "enabled": True,
                "format": f"{dec_val:+d}°",
                "align": "left",
                "style": {"fontSize": "28px", "color": "#576574", "textOutline": "2px #0a0e1a", "fontWeight": "400"},
                "x": 8,
                "y": -4,
            },
            "marker": {"radius": 0, "states": {"hover": {"enabled": False}}},
        }
    )

dec_labels = ScatterSeries()
dec_labels.data = dec_label_data
dec_labels.name = "Dec Labels"
dec_labels.color = "rgba(0,0,0,0)"
dec_labels.enable_mouse_tracking = False
dec_labels.show_in_legend = False
dec_labels.z_index = 5
dec_labels.marker = {"radius": 0}
chart.add_series(dec_labels)

# --- Constellation lines ---
for abbr in constellation_colors:
    edges_for_const = [
        (s1, s2)
        for s1, s2 in constellation_edges
        if star_catalog[star_lookup[s1]][4] == abbr or star_catalog[star_lookup[s2]][4] == abbr
    ]
    for s1, s2 in edges_for_const:
        i1, i2 = star_lookup[s1], star_lookup[s2]
        line = SplineSeries()
        line.data = [[float(proj_x[i1]), float(proj_y[i1])], [float(proj_x[i2]), float(proj_y[i2])]]
        line.color = constellation_colors[abbr]
        line.opacity = 0.4
        line.line_width = 2
        line.marker = {"enabled": False}
        line.enable_mouse_tracking = False
        line.show_in_legend = False
        line.z_index = 1
        chart.add_series(line)

# --- Summer Triangle asterism (Vega–Deneb–Altair) for storytelling emphasis ---
summer_triangle_stars = ["Vega", "Deneb", "Altair"]
st_edges = [("Vega", "Deneb"), ("Deneb", "Altair"), ("Altair", "Vega")]
for s1, s2 in st_edges:
    i1, i2 = star_lookup[s1], star_lookup[s2]
    tri_line = SplineSeries()
    tri_line.data = [[float(proj_x[i1]), float(proj_y[i1])], [float(proj_x[i2]), float(proj_y[i2])]]
    tri_line.color = "rgba(255, 255, 200, 0.18)"
    tri_line.line_width = 3
    tri_line.dash_style = "ShortDash"
    tri_line.marker = {"enabled": False}
    tri_line.enable_mouse_tracking = False
    tri_line.show_in_legend = False
    tri_line.z_index = 1
    chart.add_series(tri_line)

# Summer Triangle label at centroid
st_cx = float(np.mean([proj_x[star_lookup[s]] for s in summer_triangle_stars]))
st_cy = float(np.mean([proj_y[star_lookup[s]] for s in summer_triangle_stars]))
st_label = ScatterSeries()
st_label.data = [
    {
        "x": st_cx,
        "y": st_cy,
        "dataLabels": {
            "enabled": True,
            "format": "Summer Triangle",
            "style": {
                "fontSize": "22px",
                "color": "rgba(255, 255, 200, 0.45)",
                "textOutline": "2px #0a0e1a",
                "fontStyle": "italic",
                "fontWeight": "400",
            },
            "y": -14,
        },
        "marker": {"radius": 0, "states": {"hover": {"enabled": False}}},
    }
]
st_label.color = "rgba(0,0,0,0)"
st_label.enable_mouse_tracking = False
st_label.show_in_legend = False
st_label.z_index = 4
st_label.marker = {"radius": 0}
chart.add_series(st_label)

# --- Star scatter points ---
star_data_points = []
for i in range(len(star_catalog)):
    ra_h_val = ra_hours[i]
    ra_str = f"{int(ra_h_val)}h{int((ra_h_val % 1) * 60):02d}m"
    dec_str = f"{dec_deg[i]:+.1f}°"
    star_data_points.append(
        {
            "x": float(proj_x[i]),
            "y": float(proj_y[i]),
            "name": star_names[i],
            "mag": float(magnitudes[i]),
            "raStr": ra_str,
            "decStr": dec_str,
            "marker": {
                "radius": float(star_radii[i]),
                "fillColor": {
                    "radialGradient": {"cx": 0.4, "cy": 0.3, "r": 0.7},
                    "stops": [
                        [0, "#ffffff"],
                        [0.3, f"rgba(255, 248, 220, {float(star_opacity[i]):.2f})"],
                        [1, f"rgba(200, 214, 229, {float(star_opacity[i] * 0.3):.2f})"],
                    ],
                },
                "lineWidth": 0,
            },
        }
    )

stars_series = ScatterSeries()
stars_series.data = star_data_points
stars_series.name = "Stars"
stars_series.color = "#FFF8DC"
stars_series.z_index = 3
stars_series.marker = {"symbol": "circle", "lineWidth": 0}
chart.add_series(stars_series)

# --- Constellation name labels ---
# Pre-compute centroids, then adjust overlapping ones
label_positions = {}
for abbr in constellation_names:
    const_stars = [i for i, s in enumerate(star_catalog) if s[4] == abbr]
    if not const_stars:
        continue
    cx = float(np.mean([proj_x[i] for i in const_stars]))
    cy = float(np.mean([proj_y[i] for i in const_stars]))
    label_positions[abbr] = (cx, cy)

# Offset Lyra label to avoid Cygnus overlap — shift down-left
if "Lyr" in label_positions:
    lx, ly = label_positions["Lyr"]
    label_positions["Lyr"] = (lx - 6, ly - 8)

label_data = []
for abbr, full_name in constellation_names.items():
    if abbr not in label_positions:
        continue
    cx, cy = label_positions[abbr]
    label_data.append(
        {
            "x": cx,
            "y": cy,
            "name": full_name,
            "dataLabels": {
                "enabled": True,
                "format": full_name,
                "style": {
                    "fontSize": "26px",
                    "color": constellation_colors[abbr],
                    "textOutline": "2px #0a0e1a",
                    "fontWeight": "600",
                    "letterSpacing": "2px",
                },
                "y": -20,
            },
            "marker": {"radius": 0, "states": {"hover": {"enabled": False}}},
        }
    )

label_series = ScatterSeries()
label_series.data = label_data
label_series.name = "Constellation Labels"
label_series.color = "rgba(0,0,0,0)"
label_series.enable_mouse_tracking = False
label_series.show_in_legend = False
label_series.z_index = 4
label_series.marker = {"radius": 0}
chart.add_series(label_series)

# --- Background stars for atmosphere ---
np.random.seed(99)
n_bg_stars = 400
bg_ra_h = np.random.uniform(0, 24, n_bg_stars)
bg_dec = np.random.uniform(-50, 90, n_bg_stars)
bg_mag = np.random.uniform(4.0, 6.5, n_bg_stars)
bg_radius = 1 + (6.5 - bg_mag) / 2.5

bg_ra_deg = bg_ra_h * 15.0
bg_ra_rad = np.radians(bg_ra_deg)
bg_r = 90.0 - bg_dec
bg_px = bg_r * np.sin(bg_ra_rad)
bg_py = bg_r * np.cos(bg_ra_rad)

# Filter to within boundary circle
mask = np.sqrt(bg_px**2 + bg_py**2) <= R_BOUNDARY
bg_px, bg_py, bg_mag, bg_radius = bg_px[mask], bg_py[mask], bg_mag[mask], bg_radius[mask]

bg_data = []
for i in range(len(bg_px)):
    bg_data.append(
        {
            "x": float(bg_px[i]),
            "y": float(bg_py[i]),
            "marker": {
                "radius": float(bg_radius[i]),
                "fillColor": (f"rgba(180, 200, 220, {0.12 + 0.15 * (6.5 - float(bg_mag[i])) / 2.5:.2f})"),
                "lineWidth": 0,
            },
        }
    )

bg_series = ScatterSeries()
bg_series.data = bg_data
bg_series.name = "Background Stars"
bg_series.color = "rgba(180, 200, 220, 0.2)"
bg_series.enable_mouse_tracking = False
bg_series.show_in_legend = False
bg_series.z_index = 0
bg_series.marker = {"symbol": "circle", "lineWidth": 0}
chart.add_series(bg_series)

# --- Ecliptic line (dashed, approximate) ---
# The ecliptic has dec ≈ 23.4° * sin(RA - 90°) roughly
ecliptic_pts = []
for ra_d in np.linspace(0, 360, 300):
    ecl_dec = 23.44 * math.sin(math.radians(ra_d - 90))
    ecl_r = 90.0 - ecl_dec
    ecl_ra_rad = math.radians(ra_d)
    ex = ecl_r * math.sin(ecl_ra_rad)
    ey = ecl_r * math.cos(ecl_ra_rad)
    r = math.sqrt(ex**2 + ey**2)
    if r <= R_BOUNDARY:
        ecliptic_pts.append([round(ex, 2), round(ey, 2)])

ecliptic = SplineSeries()
ecliptic.data = ecliptic_pts
ecliptic.color = "rgba(255, 183, 77, 0.35)"
ecliptic.line_width = 2
ecliptic.dash_style = "LongDash"
ecliptic.marker = {"enabled": False}
ecliptic.enable_mouse_tracking = False
ecliptic.show_in_legend = False
ecliptic.z_index = 1
chart.add_series(ecliptic)

# --- Ecliptic label ---
ecl_label_ra = 270
ecl_label_dec = 23.44 * math.sin(math.radians(ecl_label_ra - 90))
ecl_label_r = 90.0 - ecl_label_dec
ecl_label_ra_rad = math.radians(ecl_label_ra)
elx = ecl_label_r * math.sin(ecl_label_ra_rad)
ely = ecl_label_r * math.cos(ecl_label_ra_rad)
ecl_label = ScatterSeries()
ecl_label.data = [
    {
        "x": round(elx, 2),
        "y": round(ely, 2),
        "dataLabels": {
            "enabled": True,
            "format": "Ecliptic",
            "style": {
                "fontSize": "28px",
                "color": "rgba(255, 183, 77, 0.65)",
                "textOutline": "2px #0a0e1a",
                "fontStyle": "italic",
            },
            "y": -16,
        },
        "marker": {"radius": 0, "states": {"hover": {"enabled": False}}},
    }
]
ecl_label.color = "rgba(0,0,0,0)"
ecl_label.enable_mouse_tracking = False
ecl_label.show_in_legend = False
ecl_label.z_index = 5
ecl_label.marker = {"radius": 0}
chart.add_series(ecl_label)

# --- Download Highcharts JS ---
js_urls = [("https://code.highcharts.com/highcharts.js", "https://cdn.jsdelivr.net/npm/highcharts@11/highcharts.js")]
js_parts = []
for primary, fallback in js_urls:
    for url in (primary, fallback):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(req, timeout=30) as response:
                js_parts.append(response.read().decode("utf-8"))
            break
        except Exception:
            continue
highcharts_js = "\n".join(js_parts)

# Generate HTML with inline scripts
html_str = chart.to_js_literal()
html_content = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <script>{highcharts_js}</script>
</head>
<body style="margin:0; background:#0a0e1a;">
    <div id="container" style="width: 3600px; height: 3600px;"></div>
    <script>{html_str}</script>
</body>
</html>"""

# Write temp HTML and take screenshot
with tempfile.NamedTemporaryFile(mode="w", suffix=".html", delete=False, encoding="utf-8") as f:
    f.write(html_content)
    temp_path = f.name

chrome_options = Options()
chrome_options.add_argument("--headless")
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("--disable-dev-shm-usage")
chrome_options.add_argument("--disable-gpu")
chrome_options.add_argument("--window-size=3600,3600")

driver = webdriver.Chrome(options=chrome_options)
driver.get(f"file://{temp_path}")
time.sleep(5)

container = driver.find_element("id", "container")
container.screenshot("plot.png")
driver.quit()

Path(temp_path).unlink()

# Save HTML for interactive version
with open("plot.html", "w", encoding="utf-8") as f:
    interactive_html = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <script src="https://code.highcharts.com/highcharts.js"></script>
</head>
<body style="margin:0; background:#0a0e1a;">
    <div id="container" style="width: 100vmin; height: 100vmin; margin: auto;"></div>
    <script>{html_str}</script>
</body>
</html>"""
    f.write(interactive_html)
