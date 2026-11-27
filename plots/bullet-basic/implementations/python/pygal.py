"""anyplot.ai
bullet-basic: Basic Bullet Chart
Library: pygal 3.1.0 | Python 3.13.13
Quality: pending | Updated: 2026-05-29
"""

import importlib.util
import os
import re
import sys

import cairosvg
import pandas as pd


# Guard against self-import: this file is named pygal.py, so a plain
# `import pygal` picks up itself instead of the installed package.
pygal_spec = importlib.util.find_spec("pygal")
if pygal_spec and pygal_spec.origin != __file__:
    import pygal
    from pygal.style import Style
else:
    _cwd = os.getcwd()
    sys.path = [p for p in sys.path if os.path.abspath(p) != os.path.abspath(_cwd)]
    try:
        import pygal
        from pygal.style import Style
    finally:
        sys.path.insert(0, _cwd)

# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_MUTED = "#6B6A63" if THEME == "light" else "#A8A79F"

# Imprint palette: all eight positions in canonical order
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

# Qualitative bands: grayscale in a steady light-to-dark progression, theme-adaptive
BANDS = ["#E4E3DC", "#C0BFB8", "#8E8D87"] if THEME == "light" else ["#34342E", "#4D4D46", "#6B6A63"]

# Constants
BAND_EDGES = [50, 75, 100]  # band thresholds in % of each metric's scale maximum

# Columns: set these to your table's column names
METRIC = "Metric"  # role: label
ACTUAL = "Actual"  # role: actual
TARGET = "Target"  # role: target
SCALE_MAX = "Scale maximum"  # role: extra
UNIT = "Unit suffix"  # role: extra
RANGES = "Band edges (% of maximum)"  # role: ranges

# Data: replace this block with your own table, for example df = pd.read_csv("kpis.csv")
df = pd.DataFrame(
    {
        METRIC: [
            "On-Time Delivery",
            "First Pass Yield",
            "OEE",
            "Inventory Turnover",
            "Supplier On-Time",
            "Capacity Utilization",
            "Quality Score",
        ],
        ACTUAL: [91, 88, 72, 8, 87, 82, 94],
        TARGET: [95, 90, 85, 10, 90, 80, 92],
        SCALE_MAX: [100, 100, 100, 12, 100, 100, 100],
        UNIT: ["%", "%", "%", "x", "%", "%", "/100"],
        RANGES: ["50,75,100"] * 7,
    }
)

# Plot: everything below reads only df and the constants above
actual_pct = (df[ACTUAL] / df[SCALE_MAX] * 100).tolist()
target_pct = (df[TARGET] / df[SCALE_MAX] * 100).tolist()
labels = [f"{m} ({a}{u})" for m, u, a in zip(df[METRIC], df[UNIT], df[ACTUAL], strict=True)]
band_widths = [hi - lo for lo, hi in zip([0, *BAND_EDGES[:-1]], BAND_EDGES, strict=True)]
band_names = [
    f"{name} ({lo}–{hi}%)"
    for name, lo, hi in zip(["Poor", "Satisfactory", "Good"], [0, *BAND_EDGES[:-1]], BAND_EDGES, strict=True)
]

custom_style = Style(
    background=PAGE_BG,
    plot_background=PAGE_BG,
    foreground=INK,
    foreground_strong=INK,
    foreground_subtle=INK_MUTED,
    guide_stroke_color=INK_MUTED,
    major_guide_stroke_color=INK_MUTED,
    font_family="DejaVu Sans, Helvetica, Arial, sans-serif",
    colors=(IMPRINT_PALETTE[0], INK, *BANDS),
    title_font_size=66,
    label_font_size=48,
    major_label_font_size=48,
    legend_font_size=44,
    value_font_size=36,
    stroke_width=2.5,
)

chart = pygal.HorizontalStackedBar(
    width=3200,
    height=1800,
    title="bullet-basic · python · pygal · anyplot.ai",
    style=custom_style,
    show_legend=True,
    legend_at_bottom=True,
    legend_box_size=26,
    legend_at_bottom_columns=3,
    truncate_legend=-1,
    margin_bottom=110,
    print_values=False,
    print_zeroes=False,
    show_y_guides=False,
    show_x_guides=True,
    margin=40,
    spacing=0,
    truncate_label=-1,
    x_title="Performance (% of scale maximum)",
    range=(0, 100),
)
chart.x_labels = labels

# Legend-only placeholder series (serie-0/1): measure bar and target marker
chart.add(ACTUAL, [None] * len(df))
chart.add(TARGET, [None] * len(df))

# Background bands: stacked segments (serie-2/3/4)
for name, width in zip(band_names, band_widths, strict=True):
    chart.add(name, [{"value": width, "label": lbl} for lbl in labels])

# Inject the measure bars and target markers into the rendered SVG
svg = chart.render().decode("utf-8")
svg = re.sub(r' stroke-dasharray="[^"]*"', "", svg)  # solid lines only

# The first band's rects are the coordinate reference for the injection
band_start = svg.index('class="series serie-2 color-2"')
band_end = svg.index('class="series serie-3 color-3"')
band_rects = re.findall(
    r'<rect x="([\d.]+)" y="([\d.]+)"[^>]*? width="([\d.]+)" height="([\d.]+)"', svg[band_start:band_end]
)
poor_bars = [tuple(float(v) for v in r) for r in band_rects if float(r[2]) > 1 and float(r[3]) > 1]

injected = ""
for i, (bx, by, bw, bh) in enumerate(poor_bars):
    px_per_pct = bw / band_widths[0]
    cy = by + bh / 2

    # Measure bar: narrower than the bands, from zero to the actual value
    bar_h = bh * 0.42
    injected += (
        f'<rect x="{bx:.1f}" y="{cy - bar_h / 2:.1f}" width="{actual_pct[i] * px_per_pct:.1f}" '
        f'height="{bar_h:.1f}" fill="{IMPRINT_PALETTE[0]}" />'
    )

    # Target marker: thin contrasting line perpendicular to the bar
    tx = bx + target_pct[i] * px_per_pct
    marker_h = bh * 0.75
    injected += f'<rect x="{tx - 4:.1f}" y="{cy - marker_h / 2:.1f}" width="8" height="{marker_h:.1f}" fill="{INK}" />'

# The graph group closes right before the titles group
svg = svg.replace('</g><g class="titles">', injected + '</g><g class="titles">', 1)
svg_modified = svg.encode("utf-8")

# Save PNG and interactive HTML
cairosvg.svg2png(bytestring=svg_modified, write_to=f"plot-{THEME}.png")
with open(f"plot-{THEME}.html", "wb") as f:
    f.write(svg_modified)
