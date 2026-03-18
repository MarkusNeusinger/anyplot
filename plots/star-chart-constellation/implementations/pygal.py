""" pyplots.ai
star-chart-constellation: Star Chart with Constellations
Library: pygal 3.1.0 | Python 3.14.3
Quality: 81/100 | Created: 2026-03-18
"""

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

# Star magnitude tiers (brighter = lower magnitude = larger dot)
tiers = [
    ("Mag < 1 (brightest)", lambda m: m < 1.0, 30),
    ("Mag 1\u20132", lambda m: 1.0 <= m < 2.0, 20),
    ("Mag 2\u20133", lambda m: 2.0 <= m < 3.0, 12),
    ("Mag 3\u20135.5 (faintest)", lambda m: m >= 3.0, 5),
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

# Build constellation line series data (ordered star path coordinates)
const_line_data = {}
for cname, star_list in constellations.items():
    const_line_data[cname] = [
        {"value": (ra, dec), "label": f"{name} \u2014 {cname}"} for name, ra, dec, mag in star_list
    ]

# Style — dark night sky
n_const = len(constellations)
line_color = "#2a4878"
custom_style = Style(
    background="#060620",
    plot_background="#080c24",
    foreground="#7788aa",
    foreground_strong="#bbccdd",
    foreground_subtle="#182040",
    colors=(line_color,) * n_const + ("#ffffff", "#f0e68c", "#a0b0c4", "#4a5a6a"),
    opacity=0.70,
    opacity_hover=1.0,
    title_font_size=32,
    label_font_size=18,
    major_label_font_size=18,
    legend_font_size=15,
    value_font_size=14,
    tooltip_font_size=16,
    title_font_family="Trebuchet MS, Helvetica, sans-serif",
    label_font_family="Trebuchet MS, Helvetica, sans-serif",
    major_label_font_family="Trebuchet MS, Helvetica, sans-serif",
    legend_font_family="Trebuchet MS, Helvetica, sans-serif",
    value_font_family="Trebuchet MS, Helvetica, sans-serif",
    stroke_width=1.5,
)

# Chart
chart = pygal.XY(
    width=4800,
    height=2700,
    style=custom_style,
    title="star-chart-constellation \u00b7 pygal \u00b7 pyplots.ai",
    x_title="Right Ascension (hours)",
    y_title="Declination (\u00b0)",
    show_legend=True,
    legend_at_bottom=True,
    legend_at_bottom_columns=6,
    legend_box_size=16,
    stroke=True,
    dots_size=8,
    show_x_guides=True,
    show_y_guides=True,
    x_value_formatter=lambda x: f"{x:.0f}h",
    value_formatter=lambda y: f"{y:.0f}\u00b0",
    margin_top=20,
    margin_bottom=50,
    margin_left=20,
    margin_right=20,
    tooltip_border_radius=6,
    tooltip_fancy_mode=True,
    print_values=False,
    truncate_legend=25,
    spacing=10,
)

# Constellation stick-figure lines (each constellation as its own series)
for cname in constellations:
    chart.add(cname, const_line_data[cname], dots_size=0)

# Star scatter by magnitude tier (stroke=False for dots only)
for tname, _, size in tiers:
    chart.add(tname, tier_data[tname], dots_size=size, stroke=False)

# Save
chart.render_to_file("plot.html")
chart.render_to_png("plot.png")
