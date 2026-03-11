""" pyplots.ai
scatter-ashby-material: Ashby Material Selection Chart
Library: pygal 3.1.0 | Python 3.14.3
Quality: 81/100 | Created: 2026-03-11
"""

import math
import xml.etree.ElementTree as ET

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

# Colorblind-safe palette — avoid red-green confusion
family_colors = (
    "#306998",  # Metals — steel blue
    "#D4513D",  # Ceramics — terracotta/brick red
    "#2CA02C",  # Polymers — green (distinct lightness from ceramics)
    "#E8A317",  # Composites — golden amber
    "#9467BD",  # Elastomers — medium purple
    "#8C8C8C",  # Foams — neutral gray
    "#8C564B",  # Natural Materials — earth brown
)

# Replace green with teal for proper colorblind safety
family_colors = (
    "#306998",  # Metals — steel blue
    "#D4513D",  # Ceramics — brick red
    "#17BECF",  # Polymers — teal/cyan (colorblind-safe vs red)
    "#E8A317",  # Composites — golden amber
    "#9467BD",  # Elastomers — purple
    "#8C8C8C",  # Foams — neutral gray
    "#8C564B",  # Natural Materials — earth brown
)

# Style — refined grid, clean background
custom_style = Style(
    background="white",
    plot_background="#f5f6f8",
    foreground="#2c3e50",
    foreground_strong="#2c3e50",
    foreground_subtle="#e8e8e8",
    colors=family_colors,
    opacity=0.38,
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
    margin_top=30,
    margin_bottom=60,
    margin_left=30,
    margin_right=30,
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

# Render SVG and parse with ElementTree for robust manipulation
svg_bytes = chart.render()
svg_string = svg_bytes.decode("utf-8")

# Register SVG namespace to avoid ns0: prefixes in output
ET.register_namespace("", "http://www.w3.org/2000/svg")
ET.register_namespace("xlink", "http://www.w3.org/1999/xlink")
root = ET.fromstring(svg_string)
ns = {"svg": "http://www.w3.org/2000/svg"}

# Extract circle positions per series using proper XML traversal
series_circles = {}
for g in root.iter("{http://www.w3.org/2000/svg}g"):
    cls = g.get("class", "")
    if cls.startswith("series serie-"):
        parts = cls.split()
        serie_idx = int(parts[1].replace("serie-", ""))
        circles = []
        for circle in g.iter("{http://www.w3.org/2000/svg}circle"):
            cx = circle.get("cx")
            cy = circle.get("cy")
            if cx and cy:
                circles.append((float(cx), float(cy)))
        if circles and serie_idx not in series_circles:
            series_circles[serie_idx] = circles

# Compute SVG centroids using median for robustness against outliers
family_names = list(families.keys())

# Label offset adjustments tuned per family
label_offsets = {
    "Metals": (0, -45),
    "Ceramics": (0, -45),
    "Polymers": (0, -38),
    "Composites": (0, 45),  # Place below median to stay near main cluster
    "Elastomers": (0, -38),
    "Foams": (130, -38),
    "Natural Materials": (60, -38),
}

# Create overlay group for labels
labels_group = ET.SubElement(root, "{http://www.w3.org/2000/svg}g")
labels_group.set("class", "family-labels")

for serie_idx, circles in series_circles.items():
    if serie_idx < len(family_names):
        name = family_names[serie_idx]
        color = family_colors[serie_idx]
        # Use median instead of mean for robust centroid (avoids outlier skew)
        cx_med = float(np.median([c[0] for c in circles]))
        cy_med = float(np.median([c[1] for c in circles]))
        ox, oy = label_offsets.get(name, (0, -32))
        label_x = cx_med + ox
        label_y = cy_med + oy
        anchor = "start" if name == "Foams" else "middle"
        text_el = ET.SubElement(labels_group, "{http://www.w3.org/2000/svg}text")
        text_el.set("x", f"{label_x:.1f}")
        text_el.set("y", f"{label_y:.1f}")
        text_el.set("font-family", "Trebuchet MS, Helvetica, sans-serif")
        text_el.set("font-size", "25")
        text_el.set("font-weight", "bold")
        text_el.set("fill", color)
        text_el.set("text-anchor", anchor)
        text_el.set("stroke", "white")
        text_el.set("stroke-width", "5")
        text_el.set("paint-order", "stroke")
        text_el.text = name

# Add E/ρ constant performance index guide lines
all_cx = [cx for circles in series_circles.values() for cx, cy in circles]
all_cy = [cy for circles in series_circles.values() for cx, cy in circles]

if all_cx and all_cy:
    svg_x_min, svg_x_max = min(all_cx), max(all_cx)
    svg_y_min, svg_y_max = min(all_cy), max(all_cy)  # SVG y is inverted

    # Known data ranges from the dataset
    log_x_min = math.log10(min(d for f in families.values() for d in f["density"]) * 0.9)
    log_x_max = math.log10(max(d for f in families.values() for d in f["density"]) * 1.1)
    log_y_min = math.log10(min(m for f in families.values() for m in f["modulus"]) * 0.9)
    log_y_max = math.log10(max(m for f in families.values() for m in f["modulus"]) * 1.1)

    def data_to_svg(log_x, log_y):
        frac_x = (log_x - log_x_min) / (log_x_max - log_x_min)
        frac_y = (log_y - log_y_min) / (log_y_max - log_y_min)
        sx = svg_x_min + frac_x * (svg_x_max - svg_x_min)
        sy = svg_y_max - frac_y * (svg_y_max - svg_y_min)  # SVG y inverted
        return sx, sy

    guides_group = ET.SubElement(root, "{http://www.w3.org/2000/svg}g")
    guides_group.set("class", "guide-lines")

    # E/ρ guide lines: E = C * ρ  →  log(E) = log(C) + log(ρ)  (slope=1 on log-log)
    for c_val, label_text in [(0.01, "E/ρ = 0.01"), (0.0001, "E/ρ = 10⁻⁴")]:
        log_c = math.log10(c_val)
        ly1 = log_x_min + log_c
        ly2 = log_x_max + log_c
        lx1, lx2 = log_x_min, log_x_max
        # Clip to y bounds
        if ly1 < log_y_min:
            lx1 = log_y_min - log_c
            ly1 = log_y_min
        if ly2 > log_y_max:
            lx2 = log_y_max - log_c
            ly2 = log_y_max
        if ly1 > log_y_max or ly2 < log_y_min:
            continue
        sx1, sy1 = data_to_svg(lx1, ly1)
        sx2, sy2 = data_to_svg(lx2, ly2)
        line_el = ET.SubElement(guides_group, "{http://www.w3.org/2000/svg}line")
        line_el.set("x1", f"{sx1:.1f}")
        line_el.set("y1", f"{sy1:.1f}")
        line_el.set("x2", f"{sx2:.1f}")
        line_el.set("y2", f"{sy2:.1f}")
        line_el.set("stroke", "#aaaaaa")
        line_el.set("stroke-width", "2")
        line_el.set("stroke-dasharray", "12,6")
        line_el.set("opacity", "0.6")
        # Guide line label — larger and darker for visibility
        text_el = ET.SubElement(guides_group, "{http://www.w3.org/2000/svg}text")
        text_el.set("x", f"{sx2 - 10:.1f}")
        text_el.set("y", f"{sy2 - 10:.1f}")
        text_el.set("font-family", "Trebuchet MS, Helvetica, sans-serif")
        text_el.set("font-size", "20")
        text_el.set("fill", "#666666")
        text_el.set("text-anchor", "end")
        text_el.set("font-style", "italic")
        text_el.text = label_text

# Serialize back to string
final_svg = ET.tostring(root, encoding="unicode", xml_declaration=False)

# Save outputs
with open("plot.html", "w") as f:
    f.write(final_svg)

cairosvg.svg2png(bytestring=final_svg.encode("utf-8"), write_to="plot.png")
