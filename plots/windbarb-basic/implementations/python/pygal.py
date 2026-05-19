"""anyplot.ai
windbarb-basic: Wind Barb Plot for Meteorological Data
Library: pygal | Python 3.13
Quality: pending | Created: 2026-05-19
"""

import math
import os

import cairosvg
import numpy as np


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
INK_MUTED = "#6B6A63" if THEME == "light" else "#A8A79F"
BRAND = "#009E73"

# Canvas (4800×2700 landscape)
W, H = 4800, 2700
MT, MB, ML, MR = 200, 270, 300, 200
PW = W - ML - MR
PH = H - MT - MB

# Data: synthetic surface wind observations on a 12×7 station grid
# Domain: western North America, simulating a mid-latitude cyclone
np.random.seed(42)
NX, NY = 12, 7
lons = np.linspace(-125, -70, NX)  # step = 5° → round labels
lats = np.linspace(25, 55, NY)  # step = 5° → round labels

lon_g, lat_g = np.meshgrid(lons, lats)
slons = lon_g.ravel()
slats = lat_g.ravel()
N = len(slons)

# Wind field: counterclockwise inflow toward a low-pressure centre at (-100, 40)
LOW_LON, LOW_LAT = -100.0, 40.0
rel_lon = slons - LOW_LON
rel_lat = slats - LOW_LAT
dist = np.sqrt(rel_lon**2 + rel_lat**2) + 0.5

angle_to_low = np.arctan2(rel_lon, rel_lat)
dirs = (np.degrees(angle_to_low + math.pi / 2) + np.random.normal(0, 12, N)) % 360
speeds = np.clip(22 + 180 / dist + np.random.normal(0, 4, N), 3, 70)  # knots


# Coordinate mapping: geographic → SVG pixels
def gxy(lon, lat):
    px = ML + (lon - lons[0]) / (lons[-1] - lons[0]) * PW
    py = MT + (1 - (lat - lats[0]) / (lats[-1] - lats[0])) * PH
    return px, py


# Wind barb geometry constants
STAFF = 72  # staff length in px
BSPC = 16  # spacing between barbs along staff
BFULL = 44  # full barb arm length
BHALF = 22  # half barb arm length


def barb_svg(x, y, spd, dirn):
    """Return list of SVG element strings for one wind barb."""
    out = []

    if spd < 2.5:
        out.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="14" fill="none" stroke="{BRAND}" stroke-width="3.5"/>')
        return out

    # Station marker dot
    out.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="5" fill="{BRAND}"/>')

    dr = math.radians(dirn)
    # Shaft direction: toward wind source (FROM direction), SVG coords (y-axis inverted)
    sdx = math.sin(dr)
    sdy = -math.cos(dr)

    xt = x + sdx * STAFF  # tail end (where barbs attach)
    yt = y + sdy * STAFF

    out.append(
        f'<line x1="{x:.1f}" y1="{y:.1f}" x2="{xt:.1f}" y2="{yt:.1f}" '
        f'stroke="{BRAND}" stroke-width="3.5" stroke-linecap="round"/>'
    )

    # Perpendicular direction (CCW rotation from shaft in SVG space)
    bpx = -sdy
    bpy = sdx

    # Decompose speed to barb counts (round to nearest 5 kt)
    sp5 = round(spd / 5) * 5
    n50, sp5 = divmod(sp5, 50)
    n10, sp5 = divmod(sp5, 10)
    n5 = sp5 // 5

    pos = 0.0  # distance from tail, stepping inward toward station

    for _ in range(n50):
        bx = xt - sdx * pos
        by = yt - sdy * pos
        tx = bx + bpx * BFULL
        ty = by + bpy * BFULL
        nx2 = bx - sdx * BSPC
        ny2 = by - sdy * BSPC
        out.append(
            f'<polygon points="{bx:.1f},{by:.1f} {tx:.1f},{ty:.1f} {nx2:.1f},{ny2:.1f}" fill="{BRAND}" stroke="none"/>'
        )
        pos += BSPC

    for _ in range(n10):
        bx = xt - sdx * pos
        by = yt - sdy * pos
        tx = bx + bpx * BFULL
        ty = by + bpy * BFULL
        out.append(
            f'<line x1="{bx:.1f}" y1="{by:.1f}" x2="{tx:.1f}" y2="{ty:.1f}" '
            f'stroke="{BRAND}" stroke-width="3.5" stroke-linecap="round"/>'
        )
        pos += BSPC

    for _ in range(n5):
        bx = xt - sdx * pos
        by = yt - sdy * pos
        tx = bx + bpx * BHALF
        ty = by + bpy * BHALF
        out.append(
            f'<line x1="{bx:.1f}" y1="{by:.1f}" x2="{tx:.1f}" y2="{ty:.1f}" '
            f'stroke="{BRAND}" stroke-width="3.5" stroke-linecap="round"/>'
        )
        pos += BSPC

    return out


# Build SVG
parts = [
    f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" font-family="sans-serif">',
    f'<rect width="{W}" height="{H}" fill="{PAGE_BG}"/>',
]

# Subtle grid
rule_opacity = "0.10"
parts.append(f'<g stroke="{INK}" stroke-opacity="{rule_opacity}" stroke-width="1.5">')
for lat in lats:
    _, gy = gxy(lons[0], lat)
    parts.append(f'<line x1="{ML}" y1="{gy:.1f}" x2="{W - MR}" y2="{gy:.1f}"/>')
for lon in lons:
    gx, _ = gxy(lon, lats[0])
    parts.append(f'<line x1="{gx:.1f}" y1="{MT}" x2="{gx:.1f}" y2="{H - MB}"/>')
parts.append("</g>")

# Wind barbs (all stations)
for i in range(N):
    sx, sy = gxy(slons[i], slats[i])
    parts.extend(barb_svg(sx, sy, speeds[i], dirs[i]))

# Axis tick labels
parts.append(f'<g fill="{INK_SOFT}" font-size="24">')
for lon in lons[::2]:  # every other longitude
    gx, _ = gxy(lon, lats[0])
    parts.append(f'<text x="{gx:.1f}" y="{H - MB + 38:.1f}" text-anchor="middle">{abs(int(lon))}°W</text>')
for lat in lats:
    _, gy = gxy(lons[0], lat)
    parts.append(f'<text x="{ML - 16}" y="{gy + 9:.1f}" text-anchor="end">{lat:.0f}°N</text>')
parts.append("</g>")

# Axis titles
parts.append(f'<text x="{W // 2}" y="{H - 28}" text-anchor="middle" fill="{INK_SOFT}" font-size="28">Longitude</text>')
parts.append(
    f'<text x="58" y="{H // 2}" text-anchor="middle" fill="{INK_SOFT}" font-size="28" '
    f'transform="rotate(-90 58 {H // 2})">Latitude</text>'
)

# Legend  (northerly barbs as icons, positioned near bottom-left)
lx0 = ML
ly0 = H - MB + 130
parts.append(f'<g fill="{INK_MUTED}" font-size="26">')
for j, (spd, lbl) in enumerate([(5, "5 kt"), (10, "10 kt"), (20, "20 kt"), (50, "50 kt")]):
    lx = lx0 + j * 340
    parts.extend(barb_svg(lx, ly0, spd, 0))  # northerly (D=0°)
    parts.append(f'<text x="{lx + 100}" y="{ly0 + 10}" text-anchor="start">{lbl}</text>')
cx = lx0 + 4 * 340
parts.append(f'<circle cx="{cx}" cy="{ly0}" r="14" fill="none" stroke="{BRAND}" stroke-width="3.5"/>')
parts.append(
    f'<text x="{cx + 28}" y="{ly0 + 10}" fill="{INK_MUTED}" font-size="26" text-anchor="start">Calm (&lt;2.5 kt)</text>'
)
parts.append("</g>")

# Title
parts.append(
    f'<text x="{W // 2}" y="130" text-anchor="middle" fill="{INK}" '
    f'font-size="52" font-weight="600">'
    f"windbarb-basic · python · pygal · anyplot.ai</text>"
)

parts.append("</svg>")
svg_str = "\n".join(parts)

# Save PNG (via cairosvg, same engine pygal uses internally)
cairosvg.svg2png(bytestring=svg_str.encode("utf-8"), write_to=f"plot-{THEME}.png")

# Save interactive HTML
html = (
    f'<!DOCTYPE html><html><head><meta charset="utf-8">'
    f"<style>body{{margin:0;padding:0;background:{PAGE_BG}}}"
    f"svg{{max-width:100%;height:auto}}</style></head>"
    f"<body>{svg_str}</body></html>"
)
with open(f"plot-{THEME}.html", "w", encoding="utf-8") as f:
    f.write(html)
