""" pyplots.ai
scatter-ashby-material: Ashby Material Selection Chart
Library: pygal 3.1.0 | Python 3.14.3
Quality: 81/100 | Created: 2026-03-11
"""

import re

import cairosvg
import numpy as np
import pygal
from pygal.style import Style


# Data — Density (kg/m³) vs Young's Modulus (GPa) for common engineering materials
np.random.seed(42)

families = {
    "Metals": {
        "materials": [
            "Steel",
            "Aluminum",
            "Titanium",
            "Copper",
            "Nickel",
            "Zinc",
            "Magnesium",
            "Tungsten",
            "Brass",
            "Bronze",
            "Cast Iron",
            "Stainless Steel",
            "Inconel",
            "Tin",
        ],
        "density": [7850, 2700, 4500, 8900, 8900, 7130, 1740, 19300, 8500, 8800, 7200, 7900, 8440, 7300],
        "modulus": [200, 69, 116, 117, 200, 108, 45, 411, 100, 110, 170, 193, 205, 50],
    },
    "Ceramics": {
        "materials": [
            "Alumina",
            "Silicon Carbide",
            "Zirconia",
            "Silicon Nitride",
            "Boron Carbide",
            "Glass",
            "Porcelain",
            "Magnesia",
            "Tungsten Carbide",
            "Titanium Carbide",
        ],
        "density": [3950, 3210, 5680, 3180, 2520, 2500, 2400, 3580, 15600, 4930],
        "modulus": [370, 450, 200, 310, 460, 70, 65, 300, 680, 450],
    },
    "Polymers": {
        "materials": [
            "Polyethylene (HDPE)",
            "Polypropylene",
            "Nylon 6,6",
            "PMMA",
            "Polycarbonate",
            "PET",
            "ABS",
            "PEEK",
            "Polystyrene",
            "PVC",
            "PTFE",
            "Epoxy",
        ],
        "density": [960, 910, 1140, 1190, 1200, 1370, 1050, 1300, 1050, 1400, 2170, 1250],
        "modulus": [1.1, 1.5, 2.8, 3.1, 2.4, 2.8, 2.3, 3.6, 3.2, 3.3, 0.5, 3.5],
    },
    "Composites": {
        "materials": [
            "CFRP (UD)",
            "GFRP (UD)",
            "Kevlar/Epoxy",
            "CFRP (Woven)",
            "GFRP (Woven)",
            "Boron/Epoxy",
            "Al-SiC MMC",
            "Wood-Polymer",
        ],
        "density": [1550, 2000, 1380, 1600, 1900, 2100, 2900, 1100],
        "modulus": [140, 40, 76, 70, 25, 210, 120, 8],
    },
    "Elastomers": {
        "materials": ["Natural Rubber", "Silicone", "Neoprene", "Butyl Rubber", "Polyurethane", "EPDM", "Viton", "SBR"],
        "density": [930, 1100, 1240, 920, 1200, 860, 1850, 940],
        "modulus": [0.003, 0.007, 0.005, 0.001, 0.025, 0.004, 0.008, 0.004],
    },
    "Foams": {
        "materials": [
            "Polyurethane Foam",
            "Polystyrene Foam",
            "PVC Foam",
            "Metallic Foam (Al)",
            "Phenolic Foam",
            "Syntactic Foam",
            "Cork",
            "Balsa Wood",
        ],
        "density": [30, 25, 80, 300, 35, 500, 120, 160],
        "modulus": [0.025, 0.012, 0.07, 1.0, 0.035, 3.5, 0.03, 3.5],
    },
    "Natural Materials": {
        "materials": ["Oak", "Pine", "Bamboo", "Bone", "Balsa", "Leather", "Horn", "Ivory"],
        "density": [700, 500, 700, 1900, 160, 860, 1200, 1850],
        "modulus": [12, 9, 18, 20, 3.5, 0.3, 3.5, 15],
    },
}

# Add slight jitter for visual separation
jitter_density = np.random.normal(1.0, 0.04, 200)
jitter_modulus = np.random.normal(1.0, 0.04, 200)
idx = 0

# Colorblind-safe palette — Foams changed from teal to silver gray for distinction
family_colors = (
    "#306998",  # Metals — steel blue
    "#E74C3C",  # Ceramics — red
    "#27AE60",  # Polymers — emerald green
    "#F39C12",  # Composites — amber
    "#9B59B6",  # Elastomers — purple
    "#95A5A6",  # Foams — silver gray
    "#D35400",  # Natural Materials — burnt orange
)

# Style — refined grid, clean background
custom_style = Style(
    background="white",
    plot_background="#f8f9fa",
    foreground="#2c3e50",
    foreground_strong="#2c3e50",
    foreground_subtle="#e8e8e8",
    colors=family_colors,
    opacity=0.35,
    opacity_hover=0.92,
    title_font_size=38,
    label_font_size=22,
    major_label_font_size=20,
    legend_font_size=20,
    value_font_size=14,
    tooltip_font_size=18,
    title_font_family="Trebuchet MS, Helvetica, sans-serif",
    label_font_family="Trebuchet MS, Helvetica, sans-serif",
    major_label_font_family="Trebuchet MS, Helvetica, sans-serif",
    legend_font_family="Trebuchet MS, Helvetica, sans-serif",
    value_font_family="Trebuchet MS, Helvetica, sans-serif",
)

# Chart — large dots for Ashby-style bubble region effect
chart = pygal.XY(
    width=4800,
    height=2700,
    style=custom_style,
    title="Density vs Young's Modulus · scatter-ashby-material · pygal · pyplots.ai",
    x_title="Density (kg/m³)",
    y_title="Young's Modulus (GPa)",
    show_legend=True,
    legend_at_bottom=True,
    legend_at_bottom_columns=7,
    legend_box_size=22,
    stroke=False,
    dots_size=26,
    show_x_guides=True,
    show_y_guides=True,
    logarithmic=True,
    x_value_formatter=lambda x: f"{x:,.0f}",
    value_formatter=lambda x: f"{x:.3g}",
    margin_top=20,
    margin_bottom=50,
    margin_left=20,
    margin_right=20,
    tooltip_border_radius=8,
    tooltip_fancy_mode=True,
    print_values=False,
    truncate_legend=-1,
    spacing=15,
)

# Track jittered data for centroid computation
family_points = {}

# Add each material family as a series
for family_name, family_data in families.items():
    points = []
    coords = []
    for i, mat in enumerate(family_data["materials"]):
        d = family_data["density"][i] * jitter_density[idx % 200]
        m = family_data["modulus"][i] * jitter_modulus[idx % 200]
        idx += 1
        coords.append((d, m))
        points.append(
            {
                "value": (round(d, 1), round(m, 4)),
                "label": f"{mat} — {family_name}\nDensity: {d:,.0f} kg/m³\nModulus: {m:.3g} GPa",
            }
        )
    chart.add(family_name, points)
    family_points[family_name] = coords

# Render SVG and add text labels at family centroids
svg_string = chart.render().decode("utf-8")

# Extract SVG coordinate info by finding circle positions per series
# pygal groups series as: <g class="series serie-N color-N">
series_circles = {}
series_pattern = re.compile(r'<g class="series serie-(\d+) color-\d+"[^>]*>(.*?)</g>', re.DOTALL)
circle_pattern = re.compile(r'<circle\s+cx="([^"]+)"\s+cy="([^"]+)"')

for match in series_pattern.finditer(svg_string):
    serie_idx = int(match.group(1))
    group_content = match.group(2)
    circles = circle_pattern.findall(group_content)
    if circles and serie_idx not in series_circles:
        series_circles[serie_idx] = [(float(cx), float(cy)) for cx, cy in circles]

# Compute SVG centroids and insert text labels
family_names = list(families.keys())
label_elements = []

# Label offset adjustments to avoid overlap with dots
label_offsets = {
    "Metals": (0, -38),
    "Ceramics": (0, -38),
    "Polymers": (0, -32),
    "Composites": (0, -38),
    "Elastomers": (0, -32),
    "Foams": (130, -32),
    "Natural Materials": (0, -32),
}

for serie_idx, circles in series_circles.items():
    if serie_idx < len(family_names):
        name = family_names[serie_idx]
        color = family_colors[serie_idx]
        cx_avg = sum(c[0] for c in circles) / len(circles)
        cy_avg = sum(c[1] for c in circles) / len(circles)
        ox, oy = label_offsets.get(name, (0, -30))
        label_x = cx_avg + ox
        label_y = cy_avg + oy
        anchor = "start" if name == "Foams" else "middle"
        label_elements.append(
            f'<text x="{label_x:.1f}" y="{label_y:.1f}" '
            f'font-family="Trebuchet MS, Helvetica, sans-serif" '
            f'font-size="20" font-weight="bold" fill="{color}" '
            f'text-anchor="{anchor}" '
            f'stroke="white" stroke-width="4" paint-order="stroke">'
            f"{name}</text>"
        )

# Insert labels before closing </svg>
if label_elements:
    labels_group = '<g class="family-labels">' + "".join(label_elements) + "</g>"
    svg_string = svg_string.replace("</svg>", labels_group + "</svg>")

# Save outputs
with open("plot.html", "w") as f:
    f.write(svg_string)

cairosvg.svg2png(bytestring=svg_string.encode("utf-8"), write_to="plot.png")
