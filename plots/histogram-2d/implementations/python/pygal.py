""" anyplot.ai
histogram-2d: 2D Histogram Heatmap
Library: pygal 3.1.3 | Python 3.14.10
Quality: 80/100 | Updated: 2026-11-15
"""

import os
import re

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

# Imprint palette: all eight positions, in canonical order
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

# Constants
N_BINS = 20  # bins per axis: fine enough for the tilt, coarse enough for a smooth gradient
CMAP_STOPS = ("#009E73", "#4467A3")  # Imprint sequential ramp, single polarity

# Columns: set these to your table's column names
STOCK = "Stock market daily return (%)"  # role: x
BOND = "Bond market daily return (%)"  # role: y

# Data: replace this block with your own table, for example df = pd.read_csv("returns.csv")
rng = np.random.default_rng(42)
common_factor = rng.normal(0, 0.15, 2000)
df = pd.DataFrame(
    {
        STOCK: np.clip(rng.normal(0.08, 1.2, 2000) + common_factor * 0.5, -5, 5),
        BOND: np.clip(rng.normal(0.02, 0.4, 2000) + common_factor * 0.2, -2, 2),
    }
)

# Plot: reads only df and the constants above
valid = df[[STOCK, BOND]].dropna()
counts, x_edges, y_edges = np.histogram2d(valid[STOCK], valid[BOND], bins=N_BINS)
counts = counts.T  # rows = bond bins (bottom to top), columns = stock bins
x_marginal = counts.sum(axis=0)
y_marginal = counts.sum(axis=1)
top_count = counts.max()


def ramp(t):
    """Interpolate the Imprint sequential ramp at t in [0, 1]."""
    c0, c1 = ([int(c[i : i + 2], 16) for i in (1, 3, 5)] for c in CMAP_STOPS)
    return "#" + "".join(f"{round(a + (b - a) * t):02X}" for a, b in zip(c0, c1, strict=True))


def cell_style(count):
    """Fill for one bin: empty bins stay blank, others follow the ramp."""
    if count == 0:
        return f"fill:{PAGE_BG};stroke:{INK_MUTED};stroke-opacity:0.25;stroke-width:1"
    return f"fill:{ramp(count / top_count)};stroke:{PAGE_BG};stroke-opacity:0.35;stroke-width:1"


def axis_ticks(edges, step=4):
    """Bin positions (0..N_BINS) labelled with the data value at that bin edge."""
    return list(range(0, N_BINS + 1, step)), (lambda v: f"{edges[0] + (edges[-1] - edges[0]) * v / N_BINS:.1f}")


class TiledHorizontalStackedBar(pygal.HorizontalStackedBar):
    """Stacked bars without the default gaps, so the bins tile the plot."""

    _series_margin = 0
    _serie_margin = 0


class TiledStackedBar(pygal.StackedBar):
    """Vertical variant of the gapless stacked bar."""

    _series_margin = 0
    _serie_margin = 0


def make_style(**kwargs):
    return Style(
        background=PAGE_BG,
        plot_background=PAGE_BG,
        foreground=INK_SOFT,
        foreground_strong=INK,
        foreground_subtle=INK_MUTED,
        colors=tuple(IMPRINT_PALETTE),
        opacity=1,
        opacity_hover=1,
        font_family="sans-serif",
        label_font_size=40,
        major_label_font_size=40,
        value_font_size=30,
        title_font_size=44,
        stroke_width=2,
        **kwargs,
    )


CANVAS_W, CANVAS_H = 3200, 1800
MAIN_W, MAIN_H = 2100, 1250
MARG_T = 330  # height of the top marginal
MARG_R = 330  # width of the right marginal
BAR_W, BAR_H = 360, 1000

# Heatmap: one stacked-bar row per bond bin, one unit-wide segment per stock bin
ticks_x, fmt_x = axis_ticks(x_edges)
ticks_y, fmt_y = axis_ticks(y_edges)
heatmap = TiledHorizontalStackedBar(
    width=MAIN_W,
    height=MAIN_H,
    style=make_style(),
    show_legend=False,
    x_title=STOCK,
    y_title=BOND,
    range=(0, N_BINS),
    y_labels=ticks_x,
    value_formatter=fmt_x,
    show_y_guides=False,
    show_x_guides=False,
    margin_left=60,
    margin_right=10,
    margin_top=10,
    margin_bottom=20,
    print_values=False,
    tooltip_border_radius=0,
)
heatmap.x_labels = [f"{(y_edges[i] + y_edges[i + 1]) / 2:.2f}" for i in range(N_BINS)]
for j in range(N_BINS):
    heatmap.add(
        f"stock bin {j}",
        [{"value": 1, "style": cell_style(counts[i, j]), "label": f"{int(counts[i, j])} days"} for i in range(N_BINS)],
    )

# Top marginal: stock-return histogram over the same bins
top_marginal = pygal.Bar(
    width=MAIN_W,
    height=MARG_T,
    style=make_style(),
    show_legend=False,
    show_x_labels=False,
    show_y_labels=False,
    show_y_guides=False,
    margin_left=234,
    margin_right=2,
    margin_top=10,
    margin_bottom=10,
    spacing=0,
)
top_marginal.add("Days", [int(v) for v in x_marginal])

# Right marginal: bond-return histogram over the same bins
right_marginal = pygal.HorizontalBar(
    width=MARG_R,
    height=MAIN_H,
    style=make_style(),
    show_legend=False,
    show_y_labels=False,
    show_x_labels=False,
    show_x_guides=False,
    show_y_guides=False,
    margin_left=10,
    margin_right=10,
    margin_top=10,
    margin_bottom=121,
)
right_marginal.add("Days", [int(v) for v in y_marginal])

# Colorbar: a single stacked column of thin ramp segments
N_SEG = 64
colorbar = pygal.StackedBar(
    width=BAR_W,
    height=BAR_H,
    style=make_style(),
    show_legend=False,
    show_x_labels=False,
    range=(0, N_SEG),
    y_labels=[round(k * N_SEG / 4) for k in range(5)],
    value_formatter=lambda v: f"{int(round(v / N_SEG * top_count))}",
    show_y_guides=False,
    margin_left=10,
    margin_right=150,
    margin_top=10,
    margin_bottom=10,
)
for k in range(N_SEG):
    colorbar.add(f"seg {k}", [{"value": 1, "style": f"fill:{ramp((k + 1) / N_SEG)};stroke:none"}])


def inner(chart):
    """Chart SVG without the XML prolog, sized explicitly so it nests in the composite."""
    svg = re.sub(r"^<\?xml[^>]*\?>", "", chart.render(is_unicode=True))
    return svg.replace("<svg ", f'<svg width="{chart.config.width}" height="{chart.config.height}" ', 1)


# Composite: pygal charts placed on one 3200 x 1800 canvas
heat_x, heat_y = 150, CANVAS_H - MAIN_H - 40
parts = [
    f'<svg xmlns="http://www.w3.org/2000/svg" width="{CANVAS_W}" height="{CANVAS_H}" viewBox="0 0 {CANVAS_W} {CANVAS_H}">',
    f'<rect width="{CANVAS_W}" height="{CANVAS_H}" fill="{PAGE_BG}"/>',
    f'<text x="{CANVAS_W / 2}" y="95" text-anchor="middle" fill="{INK}" '
    f'style="font-size:64px;font-weight:600;font-family:sans-serif">'
    f"histogram-2d · python · pygal · anyplot.ai</text>",
    f'<g transform="translate({heat_x},{heat_y - MARG_T})">{inner(top_marginal)}</g>',
    f'<g transform="translate({heat_x},{heat_y})">{inner(heatmap)}</g>',
    f'<g transform="translate({heat_x + MAIN_W},{heat_y})">{inner(right_marginal)}</g>',
    f'<g transform="translate({heat_x + MAIN_W + MARG_R + 30},{heat_y + 120})">{inner(colorbar)}</g>',
    f'<text x="{heat_x + MAIN_W + MARG_R + 120}" y="{heat_y + 90}" text-anchor="middle" fill="{INK}" '
    f'style="font-size:40px;font-weight:600;font-family:sans-serif">Days</text>',
    "</svg>",
]
svg_content = "\n".join(parts)

# Save
with open(f"plot-{THEME}.svg", "w", encoding="utf-8") as f:
    f.write(svg_content)
cairosvg.svg2png(bytestring=svg_content.encode("utf-8"), write_to=f"plot-{THEME}.png")
with open(f"plot-{THEME}.html", "w", encoding="utf-8") as f:
    f.write(
        f'<!DOCTYPE html><html><head><meta charset="utf-8"><title>histogram-2d - pygal</title>'
        f"<style>body{{margin:0;background:{PAGE_BG}}}svg{{max-width:100%;height:auto}}</style></head>"
        f"<body>{svg_content}</body></html>"
    )
