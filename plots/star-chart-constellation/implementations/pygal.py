""" pyplots.ai
star-chart-constellation: Star Chart with Constellations
Library: pygal 3.1.0 | Python 3.14.3
Quality: 82/100 | Created: 2026-03-18
"""

import math
import re

import cairosvg
import numpy as np
import pygal
from pygal.style import Style


np.random.seed(42)

# Constellation data: stars as (name, RA_hours, Dec_degrees, apparent_magnitude)
# Path order traces stick-figure lines without lifting pen (nodes may repeat for branches)
constellations = {
    "Orion": [
        ("Betelgeuse", 5.92, 7.41, 0.42),
        ("Bellatrix", 5.42, 6.35, 1.64),
        ("Mintaka", 5.53, -0.30, 2.23),
        ("Alnilam", 5.60, -1.20, 1.69),
        ("Alnitak", 5.68, -1.94, 1.77),
        ("Saiph", 5.80, -9.67, 2.09),
        ("Rigel", 5.24, -8.20, 0.13),
    ],
    "Ursa Major": [
        ("Alkaid", 13.79, 49.31, 1.86),
        ("Mizar", 13.40, 54.93, 2.27),
        ("Alioth", 12.90, 55.96, 1.77),
        ("Megrez", 12.26, 57.03, 3.31),
        ("Dubhe", 11.06, 61.75, 1.79),
        ("Merak", 11.03, 56.38, 2.37),
        ("Phecda", 11.90, 53.69, 2.44),
        ("Megrez", 12.26, 57.03, 3.31),
    ],
    "Taurus": [
        ("Alcyone", 3.79, 24.11, 2.87),
        ("Aldebaran", 4.60, 16.51, 0.85),
        ("Prima Hyadum", 4.33, 15.63, 3.65),
        ("Aldebaran", 4.60, 16.51, 0.85),
        ("Elnath", 5.44, 28.61, 1.65),
        ("Tianguan", 5.63, 21.14, 3.00),
    ],
    "Gemini": [
        ("Alhena", 6.63, 16.40, 1.93),
        ("Tejat", 6.38, 22.51, 2.88),
        ("Mebsuta", 6.73, 25.13, 3.06),
        ("Castor", 7.58, 31.89, 1.58),
        ("Pollux", 7.76, 28.03, 1.14),
    ],
    "Canis Major": [
        ("Mirzam", 6.38, -17.96, 1.98),
        ("Sirius", 6.75, -16.72, -1.46),
        ("Wezen", 7.14, -26.39, 1.83),
        ("Adhara", 6.98, -28.97, 1.50),
        ("Wezen", 7.14, -26.39, 1.83),
        ("Aludra", 7.40, -29.30, 2.45),
    ],
    "Leo": [
        ("Ras Elased", 10.00, 23.77, 2.98),
        ("Algieba", 10.33, 19.84, 2.28),
        ("Regulus", 10.14, 11.97, 1.40),
        ("Denebola", 11.82, 14.57, 2.14),
        ("Zosma", 11.24, 20.52, 2.56),
        ("Algieba", 10.33, 19.84, 2.28),
    ],
    "Auriga": [
        ("Capella", 5.28, 46.00, 0.08),
        ("Menkalinan", 5.99, 44.95, 1.90),
        ("Mahasim", 5.99, 37.21, 2.69),
        ("Hassaleh", 4.95, 33.17, 2.69),
        ("Capella", 5.28, 46.00, 0.08),
    ],
    "Canis Minor": [("Procyon", 7.66, 5.22, 0.34), ("Gomeisa", 7.45, 8.29, 2.89)],
}

# Compute constellation centroids for labeling
centroids = {}
for cname, star_list in constellations.items():
    unique = {(ra, dec) for _, ra, dec, _ in star_list}
    centroids[cname] = (sum(ra for ra, _ in unique) / len(unique), sum(dec for _, dec in unique) / len(unique))

# Collect unique constellation stars for scatter plot
seen_stars = set()
all_stars = []
for cname, star_list in constellations.items():
    for name, ra, dec, mag in star_list:
        key = (name, ra, dec)
        if key not in seen_stars:
            seen_stars.add(key)
            all_stars.append((name, ra, dec, mag, cname))

# Background field stars
n_bg = 100
bg_ra = np.random.uniform(3.0, 14.5, n_bg)
bg_dec = np.random.uniform(-35, 68, n_bg)
bg_mag = np.random.uniform(3.5, 5.5, n_bg)
for i in range(n_bg):
    all_stars.append((f"HD {10000 + i}", bg_ra[i], bg_dec[i], bg_mag[i], None))

# Magnitude tiers with distinct colors (brighter = lower magnitude = larger dot)
tiers = [
    ("\u2605 Mag < 1 (brightest)", lambda m: m < 1.0, 32),
    ("\u2605 Mag 1\u20132", lambda m: 1.0 <= m < 2.0, 22),
    ("\u2605 Mag 2\u20133", lambda m: 2.0 <= m < 3.0, 14),
    ("\u2605 Mag 3\u20135.5 (faintest)", lambda m: m >= 3.0, 6),
]

tier_data = {t[0]: [] for t in tiers}
for name, ra, dec, mag, cname in all_stars:
    tooltip = f"{name} (mag {mag:.1f})"
    if cname:
        tooltip += f" \u2014 {cname}"
    for tname, cond, _ in tiers:
        if cond(mag):
            tier_data[tname].append({"value": (ra, dec), "label": tooltip})
            break

# Constellation line series data (ordered star path coordinates)
const_line_data = {}
for cname, star_list in constellations.items():
    const_line_data[cname] = [
        {"value": (ra, dec), "label": f"{name} \u2014 {cname}"} for name, ra, dec, mag in star_list
    ]

# Ecliptic line (approximate path in equatorial coordinates)
obliquity = 23.44
ecliptic_points = []
for ra_h in np.linspace(3.0, 14.5, 50):
    ecl_lon_rad = math.radians(ra_h * 15.0)
    dec_ecl = obliquity * math.sin(ecl_lon_rad)
    ecliptic_points.append({"value": (ra_h, dec_ecl), "label": f"Ecliptic ({ra_h:.1f}h, {dec_ecl:.1f}\u00b0)"})

# Style — dark night sky with very subtle grid and distinct tier colors
n_series_const = len(constellations)
line_color = "#1e3a6a"
ecliptic_color = "#cc6633"
custom_style = Style(
    background="#04041a",
    plot_background="#060820",
    foreground="#6680aa",
    foreground_strong="#aabbdd",
    foreground_subtle="#0c1228",
    colors=((line_color,) * n_series_const + (ecliptic_color,) + ("#ffffff", "#ffd700", "#6eb5ff", "#556677")),
    opacity=0.80,
    opacity_hover=1.0,
    title_font_size=34,
    label_font_size=20,
    major_label_font_size=20,
    legend_font_size=17,
    value_font_size=18,
    tooltip_font_size=16,
    title_font_family="Trebuchet MS, Helvetica, sans-serif",
    label_font_family="Trebuchet MS, Helvetica, sans-serif",
    major_label_font_family="Trebuchet MS, Helvetica, sans-serif",
    legend_font_family="Trebuchet MS, Helvetica, sans-serif",
    value_font_family="Trebuchet MS, Helvetica, sans-serif",
    stroke_width=1.5,
)

# Chart configuration
chart = pygal.XY(
    width=4800,
    height=2700,
    style=custom_style,
    title="star-chart-constellation \u00b7 pygal \u00b7 pyplots.ai",
    x_title="Right Ascension (hours)",
    y_title="Declination (\u00b0)",
    show_legend=True,
    legend_at_bottom=True,
    legend_at_bottom_columns=4,
    legend_box_size=18,
    stroke=True,
    dots_size=8,
    show_x_guides=True,
    show_y_guides=True,
    x_value_formatter=lambda x: f"{x:.0f}h",
    value_formatter=lambda y: f"{y:.0f}\u00b0",
    margin_top=20,
    margin_bottom=60,
    margin_left=20,
    margin_right=20,
    tooltip_border_radius=6,
    tooltip_fancy_mode=True,
    print_values=False,
    truncate_legend=30,
    spacing=10,
)

# Constellation stick-figure lines (each constellation as its own series)
for cname in constellations:
    chart.add(cname, const_line_data[cname], dots_size=0)

# Ecliptic line
chart.add("Ecliptic", ecliptic_points, dots_size=0)

# Star scatter by magnitude tier (stroke=False for dots only)
for tname, _, size in tiers:
    chart.add(tname, tier_data[tname], dots_size=size, stroke=False)

# Render SVG and add constellation name labels via SVG post-processing
svg_bytes = chart.render()
svg_str = svg_bytes.decode("utf-8")

# Extract all circles with their radius to find brightest stars (r=32)
circle_pattern = re.compile(r'<circle[^>]*cx="([\d.]+)"[^>]*cy="([\d.]+)"[^>]*r="32"')
bright_circles = [(float(m[0]), float(m[1])) for m in circle_pattern.findall(svg_str)]

# Bright stars in data order (order they appear in all_stars)
bright_stars_data = [(ra, dec) for _, ra, dec, mag, _ in all_stars if mag < 1.0]

# Match data points to SVG circles: pygal renders dots in the order they appear in the series
# The brightest tier series is added after constellation lines and ecliptic
# Its dots appear in data order, so bright_circles[i] corresponds to bright_stars_data[i]
if len(bright_circles) >= 2 and len(bright_stars_data) >= 2:
    # Use first two bright stars as reference points for coordinate mapping
    ra1, dec1 = bright_stars_data[0]
    ra2, dec2 = bright_stars_data[1]
    sx1, sy1 = bright_circles[0]
    sx2, sy2 = bright_circles[1]
    # Linear mapping: svg_x = a * ra + b, svg_y = c * dec + d
    a = (sx1 - sx2) / (ra1 - ra2)
    b = sx1 - a * ra1
    c = (sy1 - sy2) / (dec1 - dec2)
    d = sy1 - c * dec1

    # Inject constellation name labels as SVG text elements
    label_elements = []
    for cname, (cx, cy) in centroids.items():
        svg_x = a * cx + b
        svg_y = c * (cy + 4) + d  # offset above centroid
        label_elements.append(
            f'<text x="{svg_x:.1f}" y="{svg_y:.1f}" '
            f'font-family="Trebuchet MS, Helvetica, sans-serif" '
            f'font-size="22" fill="#99aacc" fill-opacity="0.9" '
            f'text-anchor="middle" font-style="italic">{cname}</text>'
        )

    # Insert labels before the closing </svg> tag
    label_group = '<g class="constellation-labels">' + "".join(label_elements) + "</g>"
    svg_str = svg_str.replace("</svg>", label_group + "</svg>")

# Save HTML (SVG) version
with open("plot.html", "w") as f:
    f.write(svg_str)

# Convert modified SVG to PNG
cairosvg.svg2png(bytestring=svg_str.encode("utf-8"), write_to="plot.png")
