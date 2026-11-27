"""anyplot.ai
hexbin-basic: Basic Hexbin Plot
Library: pygal 3.1.3 | Python 3.14.10
Quality: 83/100 | Created: 2026-11-27
"""

import math
import os
import re
from itertools import pairwise

import cairosvg
import numpy as np
import pandas as pd
import pygal
from pygal.style import Style


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_MUTED = "#6B6A63" if THEME == "light" else "#A8A79F"

# Imprint palette: all eight positions in canonical order
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

# Imprint sequential ramp for fields (cells that fill the plot), theme-specific stops
SEQ_FIELDS = (
    [(0.0, "#66E2B2"), (0.369, "#009E73"), (0.803, "#024582"), (1.0, "#351E45")]
    if THEME == "light"
    else [(0.0, "#404C02"), (0.487, "#009E73"), (1.0, "#CDD9FF")]
)

# Constants
GRIDSIZE = 22  # hexagons across the plot width
N_TIERS = 16  # color steps along the ramp: one pygal series per occupied step
RAMP_START = 0.12  # start the ramp above its pale end so the sparsest hexagons stand off the page
HEX_FILL = 0.96  # share of the cell a hexagon fills, the rest is the gap between neighbours


def ramp_color(stops, t):
    """The hex at t (0 to 1) along (position, hex) stops, blended linearly in sRGB."""
    t = min(max(t, 0.0), 1.0)
    (p0, c0), (p1, c1) = next((a, b) for a, b in pairwise(stops) if t <= b[0])
    share = (t - p0) / (p1 - p0)
    return "#" + "".join(
        f"{round(int(c0[i : i + 2], 16) * (1 - share) + int(c1[i : i + 2], 16) * share):02X}" for i in (1, 3, 5)
    )


# Columns: set these to your table's column names
X = "Sensor grid X (km)"  # role: x
Y = "Sensor grid Y (km)"  # role: y

# Data: replace this block with your own table, for example df = pd.read_csv("sensors.csv")
# Urban air-quality sensor network with three pollution hotspots and a thin background
rng = np.random.default_rng(42)
df = pd.DataFrame(
    {
        X: np.concatenate(
            [
                rng.normal(1.5, 0.6, 2500),  # urban core
                rng.normal(-2.5, 1.1, 1200),  # industrial zone
                rng.normal(5.0, 0.4, 600),  # highway corridor
                rng.uniform(-4.0, 6.5, 150),  # background
            ]
        ),
        Y: np.concatenate(
            [
                rng.normal(3.0, 0.6, 2500),
                rng.normal(-1.0, 0.9, 1200),
                rng.normal(1.0, 1.8, 600),
                rng.uniform(-3.0, 5.5, 150),
            ]
        ),
    }
)

# Plot: reads only df and the constants above
# Viewport: starts at the data extent; the padding loop below widens it by one cell
x_lo, x_hi = df[X].min(), df[X].max()
y_lo, y_hi = df[Y].min(), df[Y].max()

chart_args = {
    "width": 3200,
    "height": 1800,
    "title": "hexbin-basic · python · pygal · anyplot.ai",
    "x_title": X,
    "y_title": Y,
    "show_legend": False,
    "stroke": False,
    "show_x_guides": False,
    "show_y_guides": False,
    "margin_right": 500,  # room for the color bar
    "value_formatter": lambda v: f"{v:g}",
    "x_value_formatter": lambda v: f"{v:g}",
}
style_args = {
    "background": PAGE_BG,
    "plot_background": PAGE_BG,
    "foreground": INK,
    "foreground_strong": INK,
    "foreground_subtle": INK_MUTED,
    "guide_stroke_color": INK_MUTED,
    "major_guide_stroke_color": INK_MUTED,
    "opacity": 1.0,
    "opacity_hover": 1.0,
    "title_font_size": 66,
    "label_font_size": 44,
    "major_label_font_size": 44,
    "legend_font_size": 44,
    "value_font_size": 36,
    "title_font_family": "sans-serif",
    "label_font_family": "sans-serif",
    "major_label_font_family": "sans-serif",
}

# Probe render: read the plot area in SVG pixels, so the hexagons can be regular on screen.
# The viewport is padded by one cell on each side, so every occupied hexagon lies whole inside the axes.
for _ in range(2):
    x_ticks = [float(t) for t in np.arange(np.ceil(x_lo / 2) * 2, x_hi, 2)]
    y_ticks = [float(t) for t in np.arange(np.ceil(y_lo), y_hi, 1)]
    probe = pygal.XY(
        style=Style(colors=IMPRINT_PALETTE, **style_args),
        **chart_args,
        xrange=(x_lo, x_hi),
        range=(y_lo, y_hi),
        x_labels=x_ticks,
        y_labels=y_ticks,
        x_labels_major=x_ticks,
        y_labels_major=y_ticks,
    )
    probe.add("probe", [(x_lo, y_lo), (x_hi, y_hi)])
    probe_svg = probe.render().decode("utf-8")
    px, py = (
        float(v)
        for v in re.search(r'<g transform="translate\(([\d.]+),\s*([\d.]+)\)" class="plot"', probe_svg).groups()
    )
    plot_rect = re.search(r'<rect[^>]*class="background"[^>]*/>', probe_svg[probe_svg.index('class="plot"') :]).group(0)
    pw = float(re.search(r'width="([\d.]+)"', plot_rect).group(1))
    ph = float(re.search(r'height="([\d.]+)"', plot_rect).group(1))
    R = pw / GRIDSIZE / math.sqrt(3)
    if _ == 0:
        x_pad = (x_hi - x_lo) * math.sqrt(3) * R / (pw - 2 * math.sqrt(3) * R)
        y_pad = (y_hi - y_lo) * 2 * R / (ph - 4 * R)
        x_lo, x_hi, y_lo, y_hi = x_lo - x_pad, x_hi + x_pad, y_lo - y_pad, y_hi + y_pad

# Hexagonal binning in pixel space: pointy-top cells of circumradius R, nearest centre wins
valid = df[[X, Y]].dropna()  # a missing coordinate draws nothing
u = (valid[X].to_numpy() - x_lo) / (x_hi - x_lo) * pw
v = (valid[Y].to_numpy() - y_lo) / (y_hi - y_lo) * ph
fq = (math.sqrt(3) / 3 * u - v / 3) / R
fr = 2 / 3 * v / R
rq, rr, rs = np.round(fq), np.round(fr), np.round(-fq - fr)
dq, dr, ds = np.abs(rq - fq), np.abs(rr - fr), np.abs(rs - (-fq - fr))
rq = np.where((dq > dr) & (dq > ds), -rr - rs, rq)
rr = np.where((dq <= dr) | (dq <= ds), np.where(dr > ds, -rq - rs, rr), rr)
cells, counts = np.unique(np.stack([rq, rr], axis=1), axis=0, return_counts=True)
cell_x = x_lo + R * math.sqrt(3) * (cells[:, 0] + cells[:, 1] / 2) / pw * (x_hi - x_lo)
cell_y = y_lo + R * 1.5 * cells[:, 1] / ph * (y_hi - y_lo)

# Log-scaled count → one of N_TIERS color steps
log_span = math.log(counts.max()) - math.log(counts.min())
position = np.log(counts / counts.min()) / log_span if log_span > 0 else np.zeros(len(counts))
tiers = np.minimum((position * N_TIERS).astype(int), N_TIERS - 1)
used = sorted(set(tiers.tolist()))
tier_colors = [ramp_color(SEQ_FIELDS, RAMP_START + (1 - RAMP_START) * (t + 0.5) / N_TIERS) for t in used]

chart = pygal.XY(
    style=Style(colors=tier_colors, **style_args),
    **chart_args,
    xrange=(x_lo, x_hi),
    range=(y_lo, y_hi),
    x_labels=x_ticks,
    y_labels=y_ticks,
    x_labels_major=x_ticks,
    y_labels_major=y_ticks,
)
for t in used:
    in_tier = tiers == t
    chart.add(
        f"{counts[in_tier].min()}–{counts[in_tier].max()}",
        [
            {"value": (round(float(x), 4), round(float(y), 4)), "label": f"{c} readings"}
            for x, y, c in zip(cell_x[in_tier], cell_y[in_tier], counts[in_tier], strict=True)
        ],
        dots_size=R * HEX_FILL,
    )
svg = chart.render().decode("utf-8")


# SVG post-processing: pygal has no hexagon marker, so each circle becomes a hexagon polygon
def circle_to_hex(match):
    tag = match.group(0)
    xc, yc, r = (float(re.search(rf'\b{a}="([\d.e+-]+)"', tag).group(1)) for a in ("cx", "cy", "r"))
    pts = " ".join(
        f"{xc + r * math.cos(math.radians(a)):.2f},{yc + r * math.sin(math.radians(a)):.2f}" for a in range(30, 390, 60)
    )
    rest = re.sub(r'\s(cx|cy|r)="[\d.e+-]+"', "", tag)
    return rest.replace("<circle", f'<polygon points="{pts}"', 1)


svg = re.sub(r"<circle[^>]*/>", circle_to_hex, svg)
svg = re.sub(r'<path[^>]*class="axis major line"[^>]*/>', "", svg)  # pygal's zero line, not part of the density field

# Clip the series to the plot area so hexagons never reach the title or the margins
svg = svg.replace(
    "</defs>", f'<clipPath id="hex-clip"><rect x="0" y="0" width="{pw}" height="{ph}"/></clipPath></defs>', 1
)
svg = re.sub(r'<g class="series [^"]*">', lambda m: m.group(0).replace(">", ' clip-path="url(#hex-clip)">'), svg)

# Color bar: a continuous gradient on the log count scale, drawn into the right margin
bar_x, bar_w = px + pw + 60, 56
bar_y, bar_h = py + ph * 0.12, ph * 0.76
stops = "".join(
    f'<stop offset="{s / 40:.4f}" stop-color="{ramp_color(SEQ_FIELDS, RAMP_START + (1 - RAMP_START) * (1 - s / 40))}"/>'
    for s in range(41)
)
ticks = [m * 10**e for e in range(8) for m in (1, 2, 5) if counts.min() <= m * 10**e <= counts.max()]
tick_svg = "".join(
    f'<line x1="{bar_x + bar_w}" x2="{bar_x + bar_w + 14}" y1="{y:.1f}" y2="{y:.1f}" stroke="{INK_MUTED}" stroke-width="3"/>'
    f'<text x="{bar_x + bar_w + 26}" y="{y + 15:.1f}" font-size="40" fill="{INK}" font-family="sans-serif">{t}</text>'
    for t in ticks
    for y in [bar_y + bar_h * (1 - (math.log(t / counts.min()) / log_span if log_span > 0 else 0))]
)
colorbar = (
    f'<defs><linearGradient id="count-ramp" x1="0" y1="0" x2="0" y2="1">{stops}</linearGradient></defs>'
    f'<rect x="{bar_x}" y="{bar_y:.1f}" width="{bar_w}" height="{bar_h:.1f}" fill="url(#count-ramp)"/>'
    f'<text x="{bar_x}" y="{bar_y - 70:.1f}" font-size="44" fill="{INK}" font-family="sans-serif">Points per bin</text>'
    f'<text x="{bar_x}" y="{bar_y - 22:.1f}" font-size="40" fill="{INK_MUTED}" font-family="sans-serif">(log scale)</text>'
    f"{tick_svg}"
)
svg = svg.replace("</svg>", colorbar + "</svg>")

# Save the interactive HTML and the static PNG
with open(f"plot-{THEME}.html", "w", encoding="utf-8") as f:
    f.write(svg)
cairosvg.svg2png(bytestring=svg.encode("utf-8"), write_to=f"plot-{THEME}.png")
