"""anyplot.ai
star-chart-constellation: Star Chart with Constellations
Library: pygal 3.1.0 | Python 3.14.3
Quality: pending | Created: 2026-03-18
"""

import math
import os
import sys


# Remove this file's directory from sys.path so `import pygal` resolves to the
# installed package, not this script (which shares the same name).
_this_dir = os.path.dirname(os.path.abspath(__file__))
sys.path = [p for p in sys.path if os.path.abspath(p or ".") != _this_dir]

import xml.etree.ElementTree as ET

import cairosvg
import numpy as np
import pygal
from pygal.style import Style


np.random.seed(42)

# Theme tokens (see prompts/default-style-guide.md "Theme-adaptive Chrome")
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
INK_MUTED = "#6B6A63" if THEME == "light" else "#A8A79F"

# Imprint sequential cmap (single-polarity): brand green -> blue.
# Magnitude is continuous, so tiers sample this ramp; brightest tier == #009E73.
SEQ_LO = "#009E73"
SEQ_HI = "#4467A3"
seq_lo = tuple(int(SEQ_LO[i : i + 2], 16) for i in (1, 3, 5))
seq_hi = tuple(int(SEQ_HI[i : i + 2], 16) for i in (1, 3, 5))
OCHRE = "#BD8233"  # Imprint position 4 — ecliptic = the Sun's warm path

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

# Manual label offsets (RA_offset, Dec_offset) to avoid overlapping stars
label_offsets = {
    "Orion": (0.6, 5.0),
    "Canis Major": (0.7, 3.5),
    "Canis Minor": (0.5, 3.0),
    "Gemini": (0.0, 4.0),
    "Taurus": (-0.5, 4.0),
    "Leo": (0.0, -5.0),
    "Ursa Major": (0.0, -4.0),
    "Auriga": (0.0, 4.0),
}

# Compute constellation centroids for labeling
centroids = {}
for cname, star_list in constellations.items():
    unique = {(ra, dec) for _, ra, dec, _ in star_list}
    ra_c = sum(ra for ra, _ in unique) / len(unique)
    dec_c = sum(dec for _, dec in unique) / len(unique)
    dr, dd = label_offsets.get(cname, (0, 3))
    centroids[cname] = (ra_c + dr, dec_c + dd)

# Collect unique constellation stars for the scatter
seen_stars = set()
all_stars = []
for cname, star_list in constellations.items():
    for name, ra, dec, mag in star_list:
        key = (name, ra, dec)
        if key not in seen_stars:
            seen_stars.add(key)
            all_stars.append((name, ra, dec, mag, cname))

# Background field stars (mag 3.5-5.0 per spec threshold) to fill the sky
n_bg = 150
bg_ra = np.random.uniform(3.0, 14.5, n_bg)
bg_dec = np.random.uniform(-35, 68, n_bg)
bg_mag = np.random.uniform(3.5, 5.0, n_bg)
for i in range(n_bg):
    all_stars.append((f"HD {10000 + i}", bg_ra[i], bg_dec[i], bg_mag[i], None))

# Magnitude tiers: (legend label, mag_lo, mag_hi, dot radius). Brighter = larger.
# Colors sampled from the Imprint sequential ramp; brightest == #009E73.
bright_size = 30
tiers = [
    ("★ Mag < 1 (brightest)", -2.0, 1.0, bright_size),
    ("★ Mag 1–2", 1.0, 2.0, 21),
    ("★ Mag 2–3", 2.0, 3.0, 14),
    ("★ Mag 3–5 (faintest)", 3.0, 6.5, 8),
]
tier_colors = [
    "#{:02X}{:02X}{:02X}".format(
        *(round(seq_lo[k] + (seq_hi[k] - seq_lo[k]) * (j / (len(tiers) - 1))) for k in range(3))
    )
    for j in range(len(tiers))
]

tier_data = {t[0]: [] for t in tiers}
for name, ra, dec, mag, cname in all_stars:
    tooltip = f"{name} (mag {mag:.1f})"
    if cname:
        tooltip += f" — {cname}"
    for tname, lo_m, hi_m, _ in tiers:
        if lo_m <= mag < hi_m:
            tier_data[tname].append({"value": (ra, dec), "label": tooltip})
            break

# Constellation stick-figure lines as ONE series: a None break between each
# constellation collapses 8 redundant legend entries into a single subtle layer.
const_line_points = []
for cname, star_list in constellations.items():
    for name, ra, dec, _mag in star_list:
        const_line_points.append({"value": (ra, dec), "label": f"{name} — {cname}"})
    const_line_points.append(None)

# Ecliptic line (approximate path in equatorial coordinates)
obliquity = 23.44
ecliptic_points = []
for ra_h in np.linspace(3.0, 14.5, 50):
    ecl_lon_rad = math.radians(ra_h * 15.0)
    dec_ecl = obliquity * math.sin(ecl_lon_rad)
    ecliptic_points.append({"value": (ra_h, dec_ecl), "label": f"Ecliptic ({ra_h:.1f}h, {dec_ecl:.1f}°)"})

# Style — theme-adaptive chrome; Imprint data colors stay constant across themes
custom_style = Style(
    background=PAGE_BG,
    plot_background=PAGE_BG,
    foreground=INK,
    foreground_strong=INK,
    foreground_subtle=INK_MUTED,
    colors=(INK_MUTED, OCHRE, *tier_colors),
    opacity=0.9,
    opacity_hover=1.0,
    title_font_size=66,
    label_font_size=56,
    major_label_font_size=44,
    legend_font_size=44,
    value_font_size=36,
    tooltip_font_size=36,
    title_font_family="Trebuchet MS, Helvetica, sans-serif",
    label_font_family="Trebuchet MS, Helvetica, sans-serif",
    major_label_font_family="Trebuchet MS, Helvetica, sans-serif",
    legend_font_family="Trebuchet MS, Helvetica, sans-serif",
    value_font_family="Trebuchet MS, Helvetica, sans-serif",
    stroke_width=2.5,
)

# Chart configuration (Canvas hard rule: 3200x1800 landscape)
chart = pygal.XY(
    width=3200,
    height=1800,
    style=custom_style,
    title="star-chart-constellation · python · pygal · anyplot.ai",
    x_title="Right Ascension (hours)",
    y_title="Declination (°)",
    allow_interruptions=True,
    show_legend=True,
    legend_at_bottom=True,
    legend_at_bottom_columns=3,
    legend_box_size=28,
    stroke=True,
    dots_size=8,
    show_x_guides=True,
    show_y_guides=True,
    x_value_formatter=lambda x: f"{x:.0f}h",
    value_formatter=lambda y: f"{y:.0f}°",
    margin_top=24,
    margin_bottom=40,
    margin_left=24,
    margin_right=40,
    tooltip_border_radius=6,
    tooltip_fancy_mode=True,
    print_values=False,
    spacing=20,
)

# Constellation stick-figure lines (single subtle layer, drawn first = behind stars)
chart.add("Constellations", const_line_points, dots_size=0)

# Ecliptic line (dashed warm reference curve)
chart.add("Ecliptic", ecliptic_points, dots_size=0, stroke_style={"dasharray": "16, 12"})

# Star scatter by magnitude tier (stroke=False for dots only)
for tname, _, _, size in tiers:
    chart.add(tname, tier_data[tname], dots_size=size, stroke=False)

# Render SVG and add constellation name labels via XML post-processing
ET.register_namespace("", "http://www.w3.org/2000/svg")
ET.register_namespace("xlink", "http://www.w3.org/1999/xlink")
svg_bytes = chart.render()
tree = ET.fromstring(svg_bytes)
ns = {"svg": "http://www.w3.org/2000/svg"}

# Use two brightest-star circles (r == bright_size) to build a linear data->pixel map
bright_stars_data = [(ra, dec) for _, ra, dec, mag, _ in all_stars if mag < 1.0]
circles = tree.findall(".//svg:circle", ns)
ref_circles = [(float(c.get("cx")), float(c.get("cy"))) for c in circles if c.get("r") == str(bright_size)]

if len(ref_circles) >= 2 and len(bright_stars_data) >= 2:
    ra1, dec1 = bright_stars_data[0]
    ra2, dec2 = bright_stars_data[1]
    sx1, sy1 = ref_circles[0]
    sx2, sy2 = ref_circles[1]
    # Linear mapping: svg_x = a * ra + b, svg_y = c * dec + d
    a = (sx1 - sx2) / (ra1 - ra2)
    b = sx1 - a * ra1
    c = (sy1 - sy2) / (dec1 - dec2)
    d = sy1 - c * dec1

    # Insert constellation name labels as SVG text elements
    label_group = ET.SubElement(tree, "g")
    label_group.set("class", "constellation-labels")
    for cname, (cx, cy) in centroids.items():
        svg_x = a * cx + b
        svg_y = c * cy + d
        text_el = ET.SubElement(label_group, "text")
        text_el.set("x", f"{svg_x:.1f}")
        text_el.set("y", f"{svg_y:.1f}")
        text_el.set("font-family", "Trebuchet MS, Helvetica, sans-serif")
        text_el.set("font-size", "40")
        text_el.set("fill", INK_SOFT)
        text_el.set("fill-opacity", "0.95")
        text_el.set("text-anchor", "middle")
        text_el.set("font-style", "italic")
        text_el.text = cname

svg_str = ET.tostring(tree, encoding="unicode")

# Save interactive HTML (SVG) version
with open(f"plot-{THEME}.html", "w") as f:
    f.write(svg_str)

# Convert modified SVG to PNG at the exact canvas contract size
cairosvg.svg2png(
    bytestring=svg_str.encode("utf-8"), write_to=f"plot-{THEME}.png", output_width=3200, output_height=1800
)
