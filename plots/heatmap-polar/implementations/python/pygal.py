"""anyplot.ai
heatmap-polar: Polar Heatmap for Cyclic Two-Dimensional Data
Library: pygal 3.1.3 | Python 3.14.10
Quality: 82/100 | Updated: 2026-11-22
"""

import math
import os

import cairosvg
import numpy as np
import pandas as pd
import pygal
from pygal.style import Style


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
INK_MUTED = "#6B6A63" if THEME == "light" else "#A8A79F"

# Imprint palette: all eight positions, one per series in order
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

# Constants
SEQ_LOW, SEQ_HIGH = "#009E73", "#4467A3"  # imprint_seq: brand green -> blue

# Columns: set these to your table's column names
MONTH = "Month"  # role: angular
YEAR = "Year"  # role: radial
VISITORS = "Visitors (thousand)"  # role: value

# Data: replace this block with your own table, for example df = pd.read_csv("arrivals.csv")
# Monthly tourist arrivals at a Mediterranean coastal resort: summer peak, quiet winter, steady growth
np.random.seed(42)
month_names = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
season = np.array([22, 24, 38, 58, 84, 118, 152, 160, 112, 66, 30, 28], dtype=float)
year_list = [2017, 2018, 2019, 2020, 2021, 2022]
df = pd.DataFrame(
    [
        (m, y, season[j] * (1 + 0.04 * i) + np.random.normal(0, 3.0))
        for i, y in enumerate(year_list)
        for j, m in enumerate(month_names)
    ],
    columns=[MONTH, YEAR, VISITORS],
)

# Plot
table = df.pivot_table(index=YEAR, columns=MONTH, values=VISITORS, sort=False)
months = table.columns.tolist()
years = table.index.tolist()
vmin, vmax = np.nanmin(table.to_numpy()), np.nanmax(table.to_numpy())


def lerp_hex(c0, c1, t):
    """Linear RGB interpolation between two hex colors."""
    a = [int(c0[i : i + 2], 16) for i in (1, 3, 5)]
    b = [int(c1[i : i + 2], 16) for i in (1, 3, 5)]
    return "#" + "".join(f"{round(x + (y - x) * t):02X}" for x, y in zip(a, b, strict=True))


def val_to_hex(val):
    if np.isnan(val):  # a missing cell stays visibly empty, in the muted tone
        return INK_MUTED
    return lerp_hex(SEQ_LOW, SEQ_HIGH, float(np.clip((val - vmin) / (vmax - vmin), 0, 1)))


# pygal's Pie draws one series as a single ring (inner_radius sets the hole) with equal sectors,
# starting at 12 o'clock and running clockwise. A multi-series Pie would lay the series out as
# consecutive sectors instead of rings, so each year is its own single-series Pie, scaled to
# its ring radius and nested in one SVG. Ring 0 (the first year) is innermost.
SIZE = 2400
CX, CY = SIZE / 2, 1170
R_HOLE, R_OUT = 230, 860
ring_w = (R_OUT - R_HOLE) / len(years)
PIE_BASE = 1000  # side of each pie chart; its outer radius is 0.9 * PIE_BASE / 2
PIE_R = 0.9 * PIE_BASE / 2

ring_svgs = []
for i, y in enumerate(years):
    r0, r1 = R_HOLE + i * ring_w, R_HOLE + (i + 1) * ring_w
    ring_style = Style(
        background="transparent",
        plot_background="transparent",
        colors=tuple(val_to_hex(table.loc[y, m]) for m in months),
        opacity=1,
        opacity_hover=1,
        stroke_width=4,
    )
    ring = pygal.Pie(
        width=PIE_BASE,
        height=PIE_BASE,
        style=ring_style,
        inner_radius=0.9 * r0 / r1,  # pygal measures the hole against the pie's full radius, not its 0.9 outer edge
        show_legend=False,
        print_values=False,
        margin=0,
    )
    for m in months:
        ring.add(f"{m} {y}: {table.loc[y, m]:.0f}k", 1)  # equal sectors; colour carries the value
    inner = ring.render().decode("utf-8")
    inner = inner[inner.index("<svg") :]
    side = 2 * r1 * (PIE_BASE / 2) / PIE_R
    ring_svgs.append(
        inner.replace(
            "<svg", f'<svg x="{CX - side / 2:.2f}" y="{CY - side / 2:.2f}" width="{side:.2f}" height="{side:.2f}"', 1
        )
    )

# Overlay text: title, subtitle, month labels around the rim, year labels along the 12 o'clock seam
FONT = "DejaVu Sans, sans-serif"
# Thin page-coloured borders between cells: ring circles and radial seams, drawn over the pies
borders = "".join(
    f'<circle cx="{CX}" cy="{CY}" r="{R_HOLE + k * ring_w:.1f}" fill="none" stroke="{PAGE_BG}" stroke-width="5"/>'
    for k in range(len(years) + 1)
) + "".join(
    f'<line x1="{CX + R_HOLE * math.sin(j * 2 * math.pi / len(months)):.1f}" '
    f'y1="{CY - R_HOLE * math.cos(j * 2 * math.pi / len(months)):.1f}" '
    f'x2="{CX + R_OUT * math.sin(j * 2 * math.pi / len(months)):.1f}" '
    f'y2="{CY - R_OUT * math.cos(j * 2 * math.pi / len(months)):.1f}" stroke="{PAGE_BG}" stroke-width="5"/>'
    for j in range(len(months))
)
texts = [
    f'<text x="{CX}" y="100" text-anchor="middle" fill="{INK}" font-size="60" font-weight="bold" font-family="{FONT}">'
    "heatmap-polar · python · pygal · anyplot.ai</text>",
    f'<text x="{CX}" y="170" text-anchor="middle" fill="{INK_SOFT}" font-size="42" font-family="{FONT}">'
    f"Monthly tourist arrivals; rings run from {years[0]} (inner) to {years[-1]} (outer)</text>",
]
for j, month in enumerate(months):
    angle = (j + 0.5) * 2 * math.pi / len(months)
    lx, ly = CX + (R_OUT + 95) * math.sin(angle), CY - (R_OUT + 95) * math.cos(angle)
    texts.append(
        f'<text x="{lx:.0f}" y="{ly:.0f}" text-anchor="middle" dominant-baseline="central" fill="{INK}" '
        f'font-size="46" font-weight="500" font-family="{FONT}">{month}</text>'
    )
for i, y in enumerate(years):
    ly = CY - (R_HOLE + (i + 0.5) * ring_w)
    texts.append(
        f'<text x="{CX}" y="{ly:.0f}" text-anchor="middle" dominant-baseline="central" fill="{INK}" '
        f'font-size="40" font-weight="bold" '
        f'font-family="{FONT}">{y}</text>'
    )

# Colour bar (pygal has none): horizontal gradient from the same two-stop colormap
cb_w, cb_h = 700, 48
cb_x, cb_y = CX - cb_w / 2, 2250
grad_stops = "".join(
    f'<stop offset="{k * 10}%" stop-color="{lerp_hex(SEQ_LOW, SEQ_HIGH, k / 10)}"/>' for k in range(11)
)
colorbar = f"""
<defs><linearGradient id="cbGrad" x1="0" y1="0" x2="1" y2="0">{grad_stops}</linearGradient></defs>
<rect x="{cb_x}" y="{cb_y}" width="{cb_w}" height="{cb_h}" fill="url(#cbGrad)"/>
<rect x="{cb_x}" y="{cb_y}" width="{cb_w}" height="{cb_h}" fill="none" stroke="{INK_MUTED}" stroke-width="2"/>
<text x="{cb_x}" y="{cb_y + cb_h + 46}" text-anchor="middle" fill="{INK_SOFT}" font-size="38" font-family="{FONT}">{vmin:.0f}</text>
<text x="{CX}" y="{cb_y - 20}" text-anchor="middle" fill="{INK_SOFT}" font-size="38" font-family="{FONT}">{VISITORS}</text>
<text x="{cb_x + cb_w}" y="{cb_y + cb_h + 46}" text-anchor="middle" fill="{INK_SOFT}" font-size="38" font-family="{FONT}">{vmax:.0f}</text>
"""

svg_str = (
    f'<svg xmlns="http://www.w3.org/2000/svg" width="{SIZE}" height="{SIZE}" viewBox="0 0 {SIZE} {SIZE}">'
    f'<rect width="{SIZE}" height="{SIZE}" fill="{PAGE_BG}"/>'
    + "".join(ring_svgs)
    + borders
    + "".join(texts)
    + colorbar
    + "</svg>"
)

with open(f"plot-{THEME}.html", "w", encoding="utf-8") as f:
    f.write(
        f"<!DOCTYPE html><html><head><meta charset='utf-8'><style>body{{margin:0;background:{PAGE_BG};}}</style></head>"
        f"<body>{svg_str}</body></html>"
    )

cairosvg.svg2png(
    bytestring=svg_str.encode("utf-8"), write_to=f"plot-{THEME}.png", output_width=SIZE, output_height=SIZE
)
