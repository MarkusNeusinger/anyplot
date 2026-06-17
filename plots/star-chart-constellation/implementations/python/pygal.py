"""anyplot.ai
star-chart-constellation: Star Chart with Constellations
Library: pygal 3.1.0 | Python 3.13.13
Quality: 87/100 | Updated: 2026-06-17
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
GRID = "#CFCDC4" if THEME == "light" else "#3A3934"  # subtle solid graticule

# Imprint sequential cmap (single-polarity): brand green -> blue.
# Magnitude is continuous, so tiers sample this ramp; brightest tier == #009E73.
SEQ_LO = "#009E73"
SEQ_HI = "#4467A3"
seq_lo = tuple(int(SEQ_LO[i : i + 2], 16) for i in (1, 3, 5))
seq_hi = tuple(int(SEQ_HI[i : i + 2], 16) for i in (1, 3, 5))
OCHRE = "#BD8233"  # Imprint position 4 — ecliptic = the Sun's warm path

# Azimuthal-equidistant projection from the North Celestial Pole. This gives the
# natural circular sky boundary the spec asks for: Polaris sits at the centre,
# declination parallels become concentric circles, RA meridians become radial
# spokes. Radius = angular distance from the pole (90 - dec) in degrees.
BOUNDARY_DEC = -30.0  # outer rim of the chart (declination floor)
R_MAX = 90.0 - BOUNDARY_DEC  # 120


def project(ra_h, dec_deg):
    """RA (hours) + Dec (degrees) -> planar (x, y) on the equidistant disk."""
    r = 90.0 - dec_deg
    az = math.radians(ra_h * 15.0)
    return r * math.sin(az), r * math.cos(az)


def project_polar(r, ra_h):
    """Radius + RA -> planar (x, y) (for graticule/label placement)."""
    az = math.radians(ra_h * 15.0)
    return r * math.sin(az), r * math.cos(az)


# Constellation data: stars as (name, RA_hours, Dec_degrees, apparent_magnitude).
# Real catalog coordinates/magnitudes. Path order traces stick-figure lines
# without lifting pen (nodes may repeat where the asterism branches).
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
    "Ursa Minor": [
        ("Polaris", 2.53, 89.26, 1.98),
        ("Yildun", 17.54, 86.59, 4.36),
        ("Epsilon UMi", 16.77, 82.04, 4.23),
        ("Zeta UMi", 15.73, 77.79, 4.32),
        ("Kochab", 14.85, 74.16, 2.08),
        ("Pherkad", 15.35, 71.83, 3.05),
    ],
    "Cassiopeia": [
        ("Segin", 1.91, 63.67, 3.35),
        ("Ruchbah", 1.43, 60.24, 2.68),
        ("Gamma Cas", 0.95, 60.72, 2.47),
        ("Schedar", 0.68, 56.54, 2.24),
        ("Caph", 0.15, 59.15, 2.28),
    ],
    "Cepheus": [
        ("Alderamin", 21.31, 62.59, 2.45),
        ("Alfirk", 21.48, 70.56, 3.23),
        ("Errai", 23.66, 77.63, 3.21),
        ("Iota Cep", 22.83, 66.20, 3.50),
        ("Zeta Cep", 22.18, 58.20, 3.35),
        ("Alderamin", 21.31, 62.59, 2.45),
    ],
    "Draco": [
        ("Eltanin", 17.94, 51.49, 2.23),
        ("Rastaban", 17.51, 52.30, 2.79),
        ("Altais", 19.21, 67.66, 3.07),
        ("Aldhibah", 17.15, 65.71, 3.17),
        ("Edasich", 15.42, 58.97, 3.29),
        ("Thuban", 14.07, 64.38, 3.65),
    ],
    "Cygnus": [
        ("Deneb", 20.69, 45.28, 1.25),
        ("Sadr", 20.37, 40.26, 2.23),
        ("Gienah", 20.77, 33.97, 2.46),
        ("Sadr", 20.37, 40.26, 2.23),
        ("Delta Cyg", 19.75, 45.13, 2.87),
        ("Sadr", 20.37, 40.26, 2.23),
        ("Albireo", 19.51, 27.96, 3.18),
    ],
    "Lyra": [
        ("Vega", 18.62, 38.78, 0.03),
        ("Zeta Lyr", 18.75, 37.60, 4.36),
        ("Sheliak", 18.83, 33.36, 3.52),
        ("Sulafat", 18.98, 32.69, 3.25),
        ("Zeta Lyr", 18.75, 37.60, 4.36),
    ],
    "Aquila": [
        ("Tarazed", 19.77, 10.61, 2.72),
        ("Altair", 19.85, 8.87, 0.76),
        ("Alshain", 19.92, 6.41, 3.71),
        ("Altair", 19.85, 8.87, 0.76),
        ("Zeta Aql", 19.09, 13.86, 2.99),
    ],
    "Hercules": [
        ("Kornephoros", 16.50, 21.49, 2.78),
        ("Zeta Her", 16.69, 31.60, 2.81),
        ("Eta Her", 16.71, 38.92, 3.48),
        ("Pi Her", 17.25, 36.81, 3.16),
        ("Zeta Her", 16.69, 31.60, 2.81),
    ],
    "Bootes": [
        ("Muphrid", 13.91, 18.40, 2.68),
        ("Arcturus", 14.26, 19.18, -0.05),
        ("Izar", 14.75, 27.07, 2.35),
        ("Seginus", 14.53, 38.31, 3.04),
        ("Nekkar", 15.03, 40.39, 3.49),
    ],
    "Corona Borealis": [
        ("Theta CrB", 15.55, 31.36, 4.14),
        ("Nusakan", 15.46, 29.11, 3.66),
        ("Alphecca", 15.58, 26.71, 2.22),
        ("Gamma CrB", 15.71, 26.30, 3.80),
        ("Delta CrB", 15.82, 26.07, 4.59),
    ],
    "Leo": [
        ("Ras Elased", 10.00, 23.77, 2.98),
        ("Algieba", 10.33, 19.84, 2.28),
        ("Regulus", 10.14, 11.97, 1.40),
        ("Denebola", 11.82, 14.57, 2.14),
        ("Zosma", 11.24, 20.52, 2.56),
        ("Algieba", 10.33, 19.84, 2.28),
    ],
    "Cancer": [
        ("Beta Cnc", 8.28, 9.19, 3.52),
        ("Acubens", 8.97, 11.86, 4.25),
        ("Asellus Aus", 8.74, 18.15, 3.94),
        ("Asellus Bor", 8.72, 21.47, 4.66),
    ],
    "Gemini": [
        ("Alhena", 6.63, 16.40, 1.93),
        ("Tejat", 6.38, 22.51, 2.88),
        ("Mebsuta", 6.73, 25.13, 3.06),
        ("Castor", 7.58, 31.89, 1.58),
        ("Pollux", 7.76, 28.03, 1.14),
    ],
    "Auriga": [
        ("Capella", 5.28, 46.00, 0.08),
        ("Menkalinan", 5.99, 44.95, 1.90),
        ("Mahasim", 5.99, 37.21, 2.69),
        ("Hassaleh", 4.95, 33.17, 2.69),
        ("Capella", 5.28, 46.00, 0.08),
    ],
    "Perseus": [
        ("Gamma Per", 3.08, 53.51, 2.91),
        ("Mirfak", 3.41, 49.86, 1.79),
        ("Delta Per", 3.72, 47.79, 3.01),
        ("Epsilon Per", 3.96, 40.01, 2.89),
        ("Delta Per", 3.72, 47.79, 3.01),
        ("Mirfak", 3.41, 49.86, 1.79),
        ("Algol", 3.14, 40.96, 2.12),
    ],
    "Taurus": [
        ("Alcyone", 3.79, 24.11, 2.87),
        ("Aldebaran", 4.60, 16.51, 0.85),
        ("Prima Hyadum", 4.33, 15.63, 3.65),
        ("Aldebaran", 4.60, 16.51, 0.85),
        ("Elnath", 5.44, 28.61, 1.65),
        ("Tianguan", 5.63, 21.14, 3.00),
    ],
    "Aries": [("Hamal", 2.12, 23.46, 2.00), ("Sheratan", 1.91, 20.81, 2.64), ("Mesarthim", 1.89, 19.29, 3.86)],
    "Triangulum": [
        ("Mothallah", 1.88, 29.58, 3.41),
        ("Beta Tri", 2.16, 34.99, 3.00),
        ("Gamma Tri", 2.29, 33.85, 4.01),
        ("Mothallah", 1.88, 29.58, 3.41),
    ],
    "Andromeda": [
        ("Almach", 2.06, 42.33, 2.10),
        ("Mirach", 1.16, 35.62, 2.05),
        ("Delta And", 0.66, 30.86, 3.27),
        ("Alpheratz", 0.14, 29.09, 2.06),
    ],
    "Pegasus": [
        ("Algenib", 0.22, 15.18, 2.83),
        ("Alpheratz", 0.14, 29.09, 2.06),
        ("Scheat", 23.06, 28.08, 2.42),
        ("Markab", 23.08, 15.21, 2.48),
        ("Algenib", 0.22, 15.18, 2.83),
        ("Markab", 23.08, 15.21, 2.48),
        ("Enif", 21.74, 9.88, 2.39),
    ],
    "Canis Major": [
        ("Mirzam", 6.38, -17.96, 1.98),
        ("Sirius", 6.75, -16.72, -1.46),
        ("Wezen", 7.14, -26.39, 1.83),
        ("Adhara", 6.98, -28.97, 1.50),
        ("Wezen", 7.14, -26.39, 1.83),
        ("Aludra", 7.40, -29.30, 2.45),
    ],
    "Canis Minor": [("Procyon", 7.66, 5.22, 0.34), ("Gomeisa", 7.45, 8.29, 2.89)],
}

# Collect unique constellation stars for the scatter, carrying projected coords.
seen_stars = set()
all_stars = []  # (name, ra, dec, px, py, mag, cname)
for cname, star_list in constellations.items():
    for name, ra, dec, mag in star_list:
        key = (name, ra, dec)
        if key not in seen_stars:
            seen_stars.add(key)
            px, py = project(ra, dec)
            all_stars.append((name, ra, dec, px, py, mag, cname))

# Background field stars sampled uniformly across the projected disk so the sky
# fills evenly (area-uniform on the equidistant plane). r = R_MAX * sqrt(U).
n_bg = 160
bg_r = R_MAX * np.sqrt(np.random.uniform(0.0, 1.0, n_bg))
bg_az = np.random.uniform(0.0, 2 * math.pi, n_bg)
bg_mag = np.random.uniform(3.5, 5.5, n_bg)
for i in range(n_bg):
    px = bg_r[i] * math.sin(bg_az[i])
    py = bg_r[i] * math.cos(bg_az[i])
    dec = 90.0 - bg_r[i]
    ra = (math.degrees(bg_az[i]) / 15.0) % 24.0
    all_stars.append((f"HD {10000 + i}", ra, dec, px, py, bg_mag[i], None))

# Anchor each constellation label on its brightest star (pushed slightly radially
# outward). Anchoring on the brightest star instead of the centroid keeps labels
# next to a recognizable anchor and stops large pole-region constellations from
# piling their labels at the chart centre.
centroids = {}
for cname, star_list in constellations.items():
    name, ra, dec, _mag = min(star_list, key=lambda s: s[3])
    bx, by = project(ra, dec)
    norm = math.hypot(bx, by) or 1.0
    centroids[cname] = (bx + bx / norm * 6.0, by + by / norm * 6.0)

# Magnitude tiers: (legend label, mag_lo, mag_hi, dot radius). Brighter = larger.
# Colors sampled from the Imprint sequential ramp; brightest == #009E73.
bright_size = 28
tiers = [
    ("★ Mag < 1 (brightest)", -2.0, 1.0, bright_size),
    ("★ Mag 1–2", 1.0, 2.0, 20),
    ("★ Mag 2–3", 2.0, 3.0, 13),
    ("★ Mag 3–5.5 (faintest)", 3.0, 6.5, 7),
]
tier_colors = [
    "#{:02X}{:02X}{:02X}".format(
        *(round(seq_lo[k] + (seq_hi[k] - seq_lo[k]) * (j / (len(tiers) - 1))) for k in range(3))
    )
    for j in range(len(tiers))
]

tier_data = {t[0]: [] for t in tiers}
for name, ra, dec, px, py, mag, cname in all_stars:
    tooltip = f"{name} (mag {mag:.1f}, RA {ra:.1f}h, Dec {dec:+.0f}°)"
    if cname:
        tooltip += f" — {cname}"
    for tname, lo_m, hi_m, _ in tiers:
        if lo_m <= mag < hi_m:
            tier_data[tname].append({"value": (px, py), "label": tooltip})
            break

# Coordinate graticule (solid, subtle): Dec parallels as concentric circles and
# RA meridians as radial spokes — drawn ourselves so the native dashed guides
# can be turned off in favour of the clean solid sky grid the style guide wants.
grid_points = []
for dec in (60, 30, 0, -30):
    r = 90.0 - dec
    for az_deg in range(0, 361, 4):
        grid_points.append({"value": project_polar(r, az_deg / 15.0)})
    grid_points.append(None)
for ra_h in range(0, 24, 2):
    grid_points.append({"value": project_polar(5.0, ra_h)})
    grid_points.append({"value": project_polar(R_MAX, ra_h)})
    grid_points.append(None)

# Constellation stick-figure lines as ONE series: a None break between each
# constellation collapses 23 redundant legend entries into a single subtle layer.
const_line_points = []
for cname, star_list in constellations.items():
    for name, ra, dec, _mag in star_list:
        px, py = project(ra, dec)
        const_line_points.append({"value": (px, py), "label": f"{name} — {cname}"})
    const_line_points.append(None)

# Ecliptic (the Sun's path) as a proper great circle in equatorial coordinates,
# then projected — a dashed warm reference curve.
obliquity = math.radians(23.44)
ecliptic_points = []
for lon_deg in np.linspace(0, 360, 145):
    lon = math.radians(lon_deg)
    dec_ecl = math.degrees(math.asin(math.sin(obliquity) * math.sin(lon)))
    ra_ecl = (math.degrees(math.atan2(math.cos(obliquity) * math.sin(lon), math.cos(lon))) / 15.0) % 24.0
    if dec_ecl >= BOUNDARY_DEC:
        ecliptic_points.append(
            {"value": project(ra_ecl, dec_ecl), "label": f"Ecliptic ({ra_ecl:.1f}h, {dec_ecl:+.0f}°)"}
        )
    else:
        ecliptic_points.append(None)

# Style — theme-adaptive chrome; Imprint data colors stay constant across themes.
custom_style = Style(
    background=PAGE_BG,
    plot_background=PAGE_BG,
    foreground=INK,
    foreground_strong=INK,
    foreground_subtle=INK_MUTED,
    colors=(GRID, INK_MUTED, OCHRE, *tier_colors),
    opacity=0.9,
    opacity_hover=1.0,
    title_font_size=56,
    label_font_size=44,
    major_label_font_size=40,
    legend_font_size=40,
    value_font_size=34,
    tooltip_font_size=34,
    title_font_family="Trebuchet MS, Helvetica, sans-serif",
    label_font_family="Trebuchet MS, Helvetica, sans-serif",
    major_label_font_family="Trebuchet MS, Helvetica, sans-serif",
    legend_font_family="Trebuchet MS, Helvetica, sans-serif",
    value_font_family="Trebuchet MS, Helvetica, sans-serif",
    stroke_width=2.5,
)

# Chart configuration (Canvas hard rule: square 2400x2400 suits the circular sky).
# xrange is widened vs range so the bottom legend's height loss does not squash
# the projected disk into an ellipse (keeps the sky boundary round).
chart = pygal.XY(
    width=2400,
    height=2400,
    style=custom_style,
    title="star-chart-constellation · python · pygal · anyplot.ai",
    allow_interruptions=True,
    show_legend=True,
    legend_at_bottom=True,
    legend_at_bottom_columns=4,
    legend_box_size=26,
    stroke=True,
    dots_size=7,
    show_x_guides=False,
    show_y_guides=False,
    show_x_labels=False,
    show_y_labels=False,
    xrange=(-154, 154),
    range=(-139, 139),
    margin_top=20,
    margin_bottom=120,
    margin_left=20,
    margin_right=20,
    tooltip_border_radius=6,
    tooltip_fancy_mode=True,
    print_values=False,
    spacing=18,
)

# Solid coordinate graticule (drawn first = furthest back), thin and subtle.
chart.add("RA / Dec grid", grid_points, dots_size=0, stroke_style={"width": 1.5})

# Constellation stick-figure lines (single subtle layer, behind the stars).
chart.add("Constellations", const_line_points, dots_size=0)

# Ecliptic line (dashed warm reference curve).
chart.add("Ecliptic", ecliptic_points, dots_size=0, stroke_style={"dasharray": "16, 12"})

# Star scatter by magnitude tier (stroke=False for dots only).
for tname, _, _, size in tiers:
    chart.add(tname, tier_data[tname], dots_size=size, stroke=False)

# Render SVG and add constellation + coordinate labels via XML post-processing.
ET.register_namespace("", "http://www.w3.org/2000/svg")
ET.register_namespace("xlink", "http://www.w3.org/1999/xlink")
svg_bytes = chart.render()
tree = ET.fromstring(svg_bytes)
ns = {"svg": "http://www.w3.org/2000/svg"}

# Use two brightest-star circles (r == bright_size) to build a linear data->pixel
# map; pygal renders dots in add order, so circle order matches all_stars order.
bright_stars_data = [(px, py) for _, _, _, px, py, mag, _ in all_stars if mag < 1.0]
circles = tree.findall(".//svg:circle", ns)
ref_circles = [(float(c.get("cx")), float(c.get("cy"))) for c in circles if c.get("r") == str(bright_size)]


def add_text(group, x, y, text, size, fill, italic=False, anchor="middle"):
    el = ET.SubElement(group, "text")
    el.set("x", f"{x:.1f}")
    el.set("y", f"{y:.1f}")
    el.set("font-family", "Trebuchet MS, Helvetica, sans-serif")
    el.set("font-size", str(size))
    el.set("fill", fill)
    el.set("text-anchor", anchor)
    if italic:
        el.set("font-style", "italic")
    el.text = text


if len(ref_circles) >= 2 and len(bright_stars_data) >= 2:
    px1, py1 = bright_stars_data[0]
    px2, py2 = bright_stars_data[1]
    sx1, sy1 = ref_circles[0]
    sx2, sy2 = ref_circles[1]
    # Linear mapping: svg_x = a * px + b, svg_y = c * py + d
    a = (sx1 - sx2) / (px1 - px2)
    b = sx1 - a * px1
    c = (sy1 - sy2) / (py1 - py2)
    d = sy1 - c * py1

    def to_svg(px, py):
        return a * px + b, c * py + d

    # Constellation name labels.
    name_group = ET.SubElement(tree, "g")
    name_group.set("class", "constellation-labels")
    for cname, (cx, cy) in centroids.items():
        sx, sy = to_svg(cx, cy)
        add_text(name_group, sx, sy, cname, 42, INK_SOFT, italic=True)

    # Coordinate labels: RA hours around the rim, Dec degrees along a meridian.
    coord_group = ET.SubElement(tree, "g")
    coord_group.set("class", "coordinate-labels")
    for ra_h in range(0, 24, 2):
        lx, ly = project_polar(R_MAX + 6.0, ra_h)
        sx, sy = to_svg(lx, ly)
        add_text(coord_group, sx, sy + 12, f"{ra_h}h", 38, INK_MUTED)
    for dec in (60, 30, 0, -30):
        lx, ly = project_polar(90.0 - dec, 10.5)
        sx, sy = to_svg(lx, ly)
        add_text(coord_group, sx + 6, sy, f"{dec:+d}°", 38, INK_MUTED, anchor="start")

svg_str = ET.tostring(tree, encoding="unicode")

# Save interactive HTML (SVG) version.
with open(f"plot-{THEME}.html", "w") as f:
    f.write(svg_str)

# Convert modified SVG to PNG at the exact canvas contract size.
cairosvg.svg2png(
    bytestring=svg_str.encode("utf-8"), write_to=f"plot-{THEME}.png", output_width=2400, output_height=2400
)
