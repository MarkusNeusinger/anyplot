""" pyplots.ai
chord-basic: Basic Chord Diagram
Library: pygal 3.1.0 | Python 3.14
Quality: 73/100 | Updated: 2026-04-06
"""

import math

import cairosvg
import pygal
from pygal.style import Style


# Data: Migration flows between 6 continents (thousands of people)
continents = ["Africa", "Asia", "Europe", "N. America", "S. America", "Oceania"]
n = len(continents)

flows = [
    (0, 1, 8),
    (0, 2, 25),
    (0, 3, 12),
    (0, 4, 5),
    (0, 5, 3),
    (1, 0, 6),
    (1, 2, 20),
    (1, 3, 35),
    (1, 4, 8),
    (1, 5, 18),
    (2, 0, 4),
    (2, 1, 12),
    (2, 3, 22),
    (2, 4, 15),
    (2, 5, 10),
    (3, 0, 2),
    (3, 1, 10),
    (3, 2, 18),
    (3, 4, 14),
    (3, 5, 6),
    (4, 0, 3),
    (4, 1, 7),
    (4, 2, 28),
    (4, 3, 20),
    (4, 5, 4),
    (5, 0, 2),
    (5, 1, 15),
    (5, 2, 12),
    (5, 3, 8),
    (5, 4, 3),
]

# Colorblind-safe palette — all colors with strong contrast on white
colors = [
    "#306998",  # Africa - Python Blue
    "#BF8C00",  # Asia - Dark Gold
    "#2E7D32",  # Europe - Forest Green
    "#D84315",  # N. America - Deep Orange
    "#7B1FA2",  # S. America - Deep Purple
    "#00838F",  # Oceania - Teal
]

# Arc allocation proportional to total flow per entity
totals = [0] * n
for s, t, v in flows:
    totals[s] += v
    totals[t] += v
grand_total = sum(totals)

gap = 0.05  # radians between arcs
arc_spans = [(2 * math.pi - gap * n) * totals[i] / grand_total for i in range(n)]
arc_starts = []
angle = -math.pi / 2  # start at top
for i in range(n):
    arc_starts.append(angle)
    angle += arc_spans[i] + gap

# Style
custom_style = Style(
    background="white",
    plot_background="white",
    foreground="#333333",
    foreground_strong="#333333",
    foreground_subtle="#999999",
    colors=tuple(colors),
    title_font_size=72,
    label_font_size=48,
    major_label_font_size=44,
    legend_font_size=44,
    value_font_size=36,
    stroke_width=3,
)

# Pygal chart for structure, title, and legend
center = 5.0
chart = pygal.XY(
    width=3600,
    height=3600,
    style=custom_style,
    title="chord-basic \u00b7 pygal \u00b7 pyplots.ai",
    show_legend=True,
    x_title="",
    y_title="",
    show_x_guides=False,
    show_y_guides=False,
    show_x_labels=False,
    show_y_labels=False,
    stroke=True,
    dots_size=0,
    legend_at_bottom=True,
    legend_at_bottom_columns=6,
    legend_box_size=24,
    range=(0, 10),
    xrange=(0, 10),
    truncate_legend=-1,
)

# Node arcs as pygal XY series (thick strokes, provide legend entries)
node_r = 3.55
for i, name in enumerate(continents):
    steps = max(20, int(arc_spans[i] * 30))
    pts = [
        (
            center + node_r * math.cos(arc_starts[i] + arc_spans[i] * k / steps),
            center + node_r * math.sin(arc_starts[i] + arc_spans[i] * k / steps),
        )
        for k in range(steps + 1)
    ]
    chart.add(name, pts, stroke=True, show_dots=False, fill=False, stroke_style={"width": 36, "linecap": "butt"})

chart.render_to_file("plot.svg")

# --- SVG injection: filled chord ribbons + labels ---
# Coordinate mapping: chart data (0-10) → root SVG pixels
pad = 550
plot_sz = 2500
svg_cx = pad + plot_sz / 2  # 1800
svg_cy = pad + plot_sz / 2  # 1800
scale = plot_sz / 10  # 250 px per chart unit


def polar_svg(r_chart, theta):
    """Convert polar coords (chart-unit radius, math angle) to SVG pixels."""
    return (svg_cx + r_chart * scale * math.cos(theta), svg_cy - r_chart * scale * math.sin(theta))


# Build filled chord ribbons
chord_r = 3.2  # chart units — inner edge of node arcs
arc_pos = list(arc_starts)
max_val = max(v for _, _, v in flows)
svg_elems = []

for s, t, v in flows:
    s_ext = arc_spans[s] * v / totals[s]
    t_ext = arc_spans[t] * v / totals[t]
    s_a1, s_a2 = arc_pos[s], arc_pos[s] + s_ext
    t_a1, t_a2 = arc_pos[t], arc_pos[t] + t_ext
    arc_pos[s] = s_a2
    arc_pos[t] = t_a2

    sx1, sy1 = polar_svg(chord_r, s_a1)
    sx2, sy2 = polar_svg(chord_r, s_a2)
    tx1, ty1 = polar_svg(chord_r, t_a1)
    tx2, ty2 = polar_svg(chord_r, t_a2)
    r_px = chord_r * scale

    # Opacity scales with flow magnitude for visual hierarchy
    opacity = 0.45 + 0.30 * v / max_val

    # Filled ribbon: bezier → arc → bezier → arc
    path = (
        f"M {sx1:.1f},{sy1:.1f} "
        f"Q {svg_cx:.1f},{svg_cy:.1f} {tx1:.1f},{ty1:.1f} "
        f"A {r_px:.1f},{r_px:.1f} 0 0,1 {tx2:.1f},{ty2:.1f} "
        f"Q {svg_cx:.1f},{svg_cy:.1f} {sx2:.1f},{sy2:.1f} "
        f"A {r_px:.1f},{r_px:.1f} 0 0,0 {sx1:.1f},{sy1:.1f} Z"
    )
    svg_elems.append(f'  <path d="{path}" fill="{colors[s]}" fill-opacity="{opacity:.2f}" stroke="none"/>')

# Labels positioned outside node arcs
label_r = 4.1
for i, name in enumerate(continents):
    mid = arc_starts[i] + arc_spans[i] / 2
    lx, ly = polar_svg(label_r, mid)
    deg = math.degrees(mid) % 360
    if deg <= 75 or deg >= 285:
        anchor = "start"
    elif 105 <= deg <= 255:
        anchor = "end"
    else:
        anchor = "middle"
    svg_elems.append(
        f'  <text x="{lx:.0f}" y="{ly:.0f}" fill="{colors[i]}" '
        f'font-size="52" font-weight="bold" text-anchor="{anchor}" '
        f'dominant-baseline="central" '
        f'font-family="DejaVu Sans, sans-serif">{name}</text>'
    )

# Inject elements and render
with open("plot.svg") as f:
    svg = f.read()
svg = svg.replace("</svg>", "\n".join(svg_elems) + "\n</svg>")
with open("plot.svg", "w") as f:
    f.write(svg)

cairosvg.svg2png(bytestring=svg.encode("utf-8"), write_to="plot.png")

# Interactive HTML
with open("plot.html", "w") as f:
    f.write(
        "<!DOCTYPE html>\n<html>\n<head>\n"
        "    <title>chord-basic \u00b7 pygal \u00b7 pyplots.ai</title>\n"
        "    <style>body{margin:0;padding:20px;background:#f5f5f5}"
        ".container{max-width:100%;margin:0 auto}"
        "object{width:100%;height:auto}</style>\n</head>\n<body>\n"
        '    <div class="container">\n'
        '        <object type="image/svg+xml" data="plot.svg">'
        "Chord diagram</object>\n"
        "    </div>\n</body>\n</html>"
    )
