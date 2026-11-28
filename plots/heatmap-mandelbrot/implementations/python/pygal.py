""" anyplot.ai
heatmap-mandelbrot: Mandelbrot Set Fractal Visualization
Library: pygal 3.1.3 | Python 3.14.10
Quality: 85/100 | Updated: 2026-11-28
"""

import base64
import os
import re
import sys
from io import BytesIO
from pathlib import Path


sys.path = [p for p in sys.path if p != str(Path(__file__).parent)]

import cairosvg  # noqa: E402
import numpy as np  # noqa: E402
import pygal  # noqa: E402
from PIL import Image  # noqa: E402
from pygal.style import Style  # noqa: E402


# Theme tokens — Imprint palette, theme-adaptive chrome
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
INK_MUTED = "#6B6A63" if THEME == "light" else "#A8A79F"

# Imprint palette (first position is the brand green)
IMPRINT_PALETTE = ("#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314")

# Imprint sequential ramp (fields: colored cells fill the plot), low → high escape time
SEQ_FIELDS = (
    [(0.0, "#66E2B2"), (0.369, "#009E73"), (0.803, "#024582"), (1.0, "#351E45")]
    if THEME == "light"
    else [(0.0, "#404C02"), (0.487, "#009E73"), (1.0, "#CDD9FF")]
)

# Constants
MARGIN_BASE = 330  # side margin before the equal-scale adjustment
CANVAS_W, CANVAS_H = 3200, 1800  # landscape canvas
BAILOUT = 256  # escape radius; large so the smooth iteration count is continuous
LUT_SIZE = 1024  # entries of the color lookup table
FONT = "sans-serif"
TEXT_SIZE = 44  # tick labels, axis titles, colorbar ticks and legend
NOTE_SIZE = 36  # annotations on the field

# Data: generated — named parameters of the complex plane and the iteration
x_min, x_max = -2.5, 1.0
y_min, y_max = -1.25, 1.25
max_iter = 200
grid_w, grid_h = 1400, 1000

# Plot
real = np.linspace(x_min, x_max, grid_w)
imag = np.linspace(y_max, y_min, grid_h)
c = real[np.newaxis, :] + 1j * imag[:, np.newaxis]

z = np.zeros_like(c)
escape_iter = np.full(c.shape, max_iter, dtype=np.float64)
mask = np.ones(c.shape, dtype=bool)

for i in range(max_iter):
    z[mask] = z[mask] ** 2 + c[mask]
    escaped = mask & (np.abs(z) > BAILOUT)
    log_zn = np.log(np.abs(z[escaped]))
    nu = np.log(log_zn / np.log(BAILOUT)) / np.log(2)
    escape_iter[escaped] = i + 1 - nu
    mask[escaped] = False

exterior = escape_iter < max_iter

# Imprint sequential LUT along the theme's fields stops
t_vals = np.linspace(0, 1, LUT_SIZE)
stop_pos = [p for p, _ in SEQ_FIELDS]
stop_rgb = np.array([[int(h[k : k + 2], 16) for k in (1, 3, 5)] for _, h in SEQ_FIELDS], dtype=float)
lut = np.stack([np.interp(t_vals, stop_pos, stop_rgb[:, ch]) for ch in range(3)], axis=1).round().astype(np.uint8)

# Log-normalized color mapping (exterior = Imprint seq; interior = black)
cell_colors = np.zeros((*c.shape, 3), dtype=np.uint8)
log_min, log_max = 0.0, 1.0
if np.any(exterior):
    log_vals = np.log(escape_iter[exterior] + 1)
    log_min, log_max = log_vals.min(), log_vals.max()
    span = log_max - log_min
    normalized = (log_vals - log_min) / span if span > 0 else np.zeros_like(log_vals)
    cell_colors[exterior] = lut[np.clip((normalized * (LUT_SIZE - 1)).astype(int), 0, LUT_SIZE - 1)]

# Encode the field as a PNG data URI to embed in the SVG
buf = BytesIO()
Image.fromarray(cell_colors).save(buf, format="PNG")
heatmap_uri = "data:image/png;base64," + base64.b64encode(buf.getvalue()).decode()

# Axis ticks in coordinates of the complex plane, derived from the ranges
x_ticks = [float(v) for v in np.arange(np.ceil(x_min * 2) / 2, x_max + 1e-9, 0.5)]
y_ticks = [float(v) for v in np.arange(np.ceil(y_min * 2) / 2, y_max + 1e-9, 0.5)]

title_str = "heatmap-mandelbrot · python · pygal · anyplot.ai"
title_fontsize = round(66 * 67 / len(title_str)) if len(title_str) > 67 else 66

custom_style = Style(
    background=PAGE_BG,
    plot_background=PAGE_BG,
    foreground=INK,
    foreground_strong=INK,
    foreground_subtle=INK_MUTED,
    guide_stroke_color=INK_MUTED,
    major_guide_stroke_color=INK_MUTED,
    colors=IMPRINT_PALETTE,
    title_font_size=title_fontsize,
    label_font_size=TEXT_SIZE,
    major_label_font_size=TEXT_SIZE,
    legend_font_size=TEXT_SIZE,
    value_font_size=NOTE_SIZE,
    font_family=FONT,
    title_font_family=FONT,
    label_font_family=FONT,
    major_label_font_family=FONT,
    # The axis titles are drawn by pygal at the label size, bold via the CSS below
)


# The pygal XY chart supplies title, axes, ticks and axis titles for the complex plane
chart = pygal.XY(
    width=CANVAS_W,
    height=CANVAS_H,
    style=custom_style,
    title=title_str,
    x_title="Real Axis (Re)",
    y_title="Imaginary Axis (Im)",
    xrange=(x_min, x_max),
    range=(y_min, y_max),
    x_labels=x_ticks,
    y_labels=y_ticks,
    x_value_formatter=lambda v: f"{v:.1f}",
    value_formatter=lambda v: f"{v:.1f}i" if v == 0 else f"{v:+.1f}i",
    show_legend=False,
    show_x_guides=False,
    show_y_guides=False,
    margin=30,
    margin_left=MARGIN_BASE,
    margin_right=MARGIN_BASE,
    margin_top=150,
    spacing=20,
)
chart.add("window", [(x_min, y_min), (x_max, y_max)], stroke=False, dots_size=0.1)  # corner probes of the window


def plot_box(svg):
    """Origin (x, y) and size (w, h) of the plot rectangle in canvas pixels, read from pygal's SVG."""
    ox, oy = map(float, re.search(r'translate\(([\d.]+), ([\d.]+)\)" class="plot"', svg).groups())
    # Two invisible probe dots sit at the corners of the complex-plane window; pygal pads its axes
    (x0, y0), (x1, y1) = [(float(a), float(b)) for a, b in re.findall(r'<circle cx="([\d.]+)" cy="([\d.]+)"', svg)]
    return ox + x0, oy + y1, x1 - x0, y0 - y1


# First pass finds the plot rectangle; the second narrows it to the equal-scale aspect of the complex plane
ASPECT = (x_max - x_min) / (y_max - y_min)
svg_text = chart.render().decode()
ox, oy, pw, ph = plot_box(svg_text)
slack = pw - ph * ASPECT
for _ in range(2):
    # Plot + colorbar block sits centered: the slack is shared by the left margin and the right margin
    chart.margin_left = MARGIN_BASE + slack / 2 - 120
    chart.margin_right = MARGIN_BASE + slack / 2 + 120
    svg_text = chart.render().decode()
    ox, oy, pw, ph = plot_box(svg_text)
    slack += pw - ph * ASPECT

# pygal's zero line spans the whole plot height and would stick out above the field; Im = 0 is drawn by the overlay
svg_text = re.sub(r'<path[^>]*class="(?:axis )?line"[^>]*/>', "", svg_text)

# Map complex-plane coordinates to canvas pixels
px, py = ox, oy
sx, sy = pw / (x_max - x_min), ph / (y_max - y_min)


def to_x(re_val):
    return px + (re_val - x_min) * sx


def to_y(im_val):
    return py + (y_max - im_val) * sy


def note(x, y, s, size, fill, anchor="start", extra=""):
    return (
        f'<text x="{x:.1f}" y="{y:.1f}" text-anchor="{anchor}" '
        f'style="font-size:{size}px;font-family:{FONT};fill:{fill};{extra}">{s}</text>'
    )


# Overlay: the field, its frame, the formula subtitle, annotations, colorbar and the in-set key
parts = [
    '<g xmlns:xlink="http://www.w3.org/1999/xlink" class="mandelbrot-overlay">',
    f'<image x="{px:.1f}" y="{py:.1f}" width="{pw:.1f}" height="{ph:.1f}" preserveAspectRatio="none" '
    f'xlink:href="{heatmap_uri}"/>',
    f'<rect x="{px:.1f}" y="{py:.1f}" width="{pw:.1f}" height="{ph:.1f}" '
    f'style="fill:none;stroke:{INK_SOFT};stroke-width:2"/>',
    note(
        px + pw / 2,
        py - 24,
        "zₙ₊₁ = zₙ² + c · escape time, smooth coloring",
        TEXT_SIZE,
        INK_MUTED,
        "middle",
        "font-style:italic;font-weight:300;font-family:Georgia,serif;letter-spacing:1px",
    ),
    # Real axis hairline
    f'<line x1="{px:.1f}" y1="{to_y(0):.1f}" x2="{px + pw:.1f}" y2="{to_y(0):.1f}" '
    f'style="stroke:{INK_SOFT};stroke-width:1.5;stroke-dasharray:8,6;opacity:0.5"/>',
    note(px + pw - 14, to_y(0) - 12, "Im = 0", NOTE_SIZE, INK, "end", "opacity:0.85"),
]

# Period-2 bulb annotation: placed in the exterior above the bulb, leader line down to its top edge
bulb_col = real[np.argmin(np.abs(real - (-1.0)))]
bulb_rows = np.where(~exterior[:, np.argmin(np.abs(real - bulb_col))])[0]
bulb_top_im = imag[bulb_rows.min()]
ann_y = to_y(bulb_top_im + 0.18)
parts.append(
    f'<line x1="{to_x(bulb_col):.1f}" y1="{ann_y + 10:.1f}" x2="{to_x(bulb_col):.1f}" y2="{to_y(bulb_top_im) - 8:.1f}" '
    f'style="stroke:{INK};stroke-width:2;opacity:0.6"/>'
)
parts.append(note(to_x(bulb_col), ann_y, "Period-2 bulb", NOTE_SIZE, INK, "middle", "opacity:0.85"))

# Colorbar: gradient in the log-normalized iteration scale
cb_x, cb_w = px + pw + 40, 44
cb_top, cb_h = py + 30, ph - 150
grad = "".join(
    f'<stop offset="{k / 40:.4f}" style="stop-color:#{lut[int((1 - k / 40) * (LUT_SIZE - 1))][0]:02x}'
    f'{lut[int((1 - k / 40) * (LUT_SIZE - 1))][1]:02x}{lut[int((1 - k / 40) * (LUT_SIZE - 1))][2]:02x}"/>'
    for k in range(41)
)
parts.append(f'<defs><linearGradient id="cbar" x1="0" y1="0" x2="0" y2="1">{grad}</linearGradient></defs>')
parts.append(f'<rect x="{cb_x:.1f}" y="{cb_top:.1f}" width="{cb_w}" height="{cb_h:.1f}" style="fill:url(#cbar)"/>')
parts.append(
    f'<rect x="{cb_x:.1f}" y="{cb_top:.1f}" width="{cb_w}" height="{cb_h:.1f}" '
    f'style="fill:none;stroke:{INK_SOFT};stroke-width:2"/>'
)
parts.append(note(cb_x - 4, cb_top - 24, "Iterations", TEXT_SIZE, INK, "start", "font-weight:600"))
for it in (5, 10, 25, 50, 100, 200):
    lv = np.log(it + 1)
    if lv < log_min or lv > log_max:
        continue
    ty = cb_top + (1 - (lv - log_min) / (log_max - log_min)) * cb_h
    parts.append(
        f'<line x1="{cb_x + cb_w:.1f}" y1="{ty:.1f}" x2="{cb_x + cb_w + 12:.1f}" y2="{ty:.1f}" '
        f'style="stroke:{INK_SOFT};stroke-width:2"/>'
    )
    parts.append(note(cb_x + cb_w + 20, ty + 15, str(it), TEXT_SIZE, INK_SOFT))

# In-set key: black swatch with an ink outline so it stands out on the dark page
key_y = py + ph - 40
parts.append(
    f'<rect x="{cb_x:.1f}" y="{key_y - 36:.1f}" width="40" height="40" style="fill:#000000;stroke:{INK};stroke-width:3"/>'
)
parts.append(note(cb_x + 54, key_y - 2, "In set", TEXT_SIZE, INK_SOFT))
parts.append("</g>")

svg_final = svg_text.replace("</svg>", "".join(parts) + "</svg>")

# Save PNG and interactive HTML (both theme-suffixed)
cairosvg.svg2png(bytestring=svg_final.encode("utf-8"), write_to=f"plot-{THEME}.png", output_width=CANVAS_W)

html_content = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>{title_str}</title>
    <style>
        body {{ margin: 0; display: flex; justify-content: center; align-items: center;
               min-height: 100vh; background: {PAGE_BG}; }}
        .chart {{ max-width: 100%; height: auto; }}
    </style>
</head>
<body>
    <figure class="chart">
        {svg_final}
    </figure>
</body>
</html>
"""

with open(f"plot-{THEME}.html", "w", encoding="utf-8") as f:
    f.write(html_content)
