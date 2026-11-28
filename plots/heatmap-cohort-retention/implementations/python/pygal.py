""" anyplot.ai
heatmap-cohort-retention: Cohort Retention Heatmap
Library: pygal 3.1.3 | Python 3.14.10
Quality: 84/100 | Updated: 2026-11-28
"""

import math
import os
import sys
from itertools import pairwise

import numpy as np
import pandas as pd


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
INK_MUTED = "#6B6A63" if THEME == "light" else "#A8A79F"

# Imprint palette: all eight positions in canonical order
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

# Imprint sequential ramp for filled cells (fields): light = low retention, dark = high
SEQ_FIELDS = (
    [(0.0, "#66E2B2"), (0.369, "#009E73"), (0.803, "#024582"), (1.0, "#351E45")]
    if THEME == "light"
    else [(0.0, "#404C02"), (0.487, "#009E73"), (1.0, "#CDD9FF")]
)

# Remove script dir so "pygal" resolves to the installed package, not this file
_cwd = sys.path.pop(0)
import cairosvg
import pygal
from pygal.style import Style


sys.path.insert(0, _cwd)

# Columns: set these to your table's column names
COHORT = "Signup Cohort"  # role: cohort
PERIOD = "Months Since Signup"  # role: period
RETENTION = "Retention %"  # role: retention_rate
COHORT_SIZE = "Cohort size"  # role: cohort_size

# Data: replace this block with your own table, for example df = pd.read_csv("retention.csv")
np.random.seed(42)
cohort_names = [f"{m} 2024" for m in ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct"]]
sizes = [1200, 1350, 980, 1520, 1100, 1430, 1280, 1050, 1380, 1150]
base_retention = [100.0, 65.0, 48.0, 40.0, 34.0, 30.0, 27.0, 25.0, 23.5, 22.0]

rows = []
for i, (name, size) in enumerate(zip(cohort_names, sizes, strict=True)):
    for j in range(len(base_retention) - i):
        if j == 0:
            rate = 100.0
        else:
            lift = -4.0 if i == 3 else i * 1.8
            rate = round(float(np.clip(base_retention[j] + lift + np.random.uniform(-2.0, 2.0), 5.0, 100.0)), 1)
        rows.append({COHORT: name, PERIOD: j, RETENTION: rate, COHORT_SIZE: size})
df = pd.DataFrame(rows)


# Plot
def ramp_color(stops, t):
    """The hex at t (0 to 1) along (position, hex) stops, blended linearly in sRGB."""
    if not math.isfinite(t):
        return "none"
    t = min(max(t, 0.0), 1.0)
    (p0, c0), (p1, c1) = next((a, b) for a, b in pairwise(stops) if t <= b[0])
    share = (t - p0) / (p1 - p0)
    return "#" + "".join(
        f"{round(int(c0[i : i + 2], 16) * (1 - share) + int(c1[i : i + 2], 16) * share):02X}" for i in (1, 3, 5)
    )


def lum(hex_color):
    lin = [(c / 255) ** 2.2 for c in (int(hex_color[i : i + 2], 16) for i in (1, 3, 5))]
    return 0.2126 * lin[0] + 0.7152 * lin[1] + 0.0722 * lin[2]


def contrast(a, b):
    return (max(lum(a), lum(b)) + 0.05) / (min(lum(a), lum(b)) + 0.05)


def text_on(bg):
    """Dark or light ink, whichever has the higher contrast on the cell color."""
    return "#F0EFE8" if contrast(bg, "#F0EFE8") >= contrast(bg, "#1A1A17") else "#1A1A17"


def svg_text(x, y, size, fill, text, anchor="middle", weight="400", extra=""):
    return (
        f'<text x="{x:.1f}" y="{y:.1f}" text-anchor="{anchor}" fill="{fill}" {extra} '
        f"style=\"font-size:{size}px;font-weight:{weight};font-family:'Segoe UI',Roboto,sans-serif\">{text}</text>"
    )


# Cohorts as rows, periods as columns; later cohorts have fewer periods, the rest stays empty
table = df.pivot_table(index=COHORT, columns=PERIOD, values=RETENTION, sort=False)
cohort_sizes = df.drop_duplicates(COHORT, keep="first")[COHORT_SIZE].tolist()
n_rows, n_cols = table.shape
min_val, max_val = df[RETENTION].min(), df[RETENTION].max()
span = max_val - min_val

# Grid geometry on the 2400 x 2400 canvas
x0, y0, gap = 400, 330, 4
cw = (2400 - x0 - 330) / n_cols - gap
ch = (2400 - 60 - y0) / n_rows - gap
gw = n_cols * (cw + gap) - gap
gh = n_rows * (ch + gap) - gap

parts = [svg_text(x0 + gw / 2, y0 - 120, 44, INK_SOFT, PERIOD, weight="600")]
for j, period in enumerate(table.columns):
    parts.append(svg_text(x0 + j * (cw + gap) + cw / 2, y0 - 25, 32, INK, f"Month {period}", weight="700"))

for i, (cohort, size) in enumerate(zip(table.index, cohort_sizes, strict=True)):
    ry = y0 + i * (ch + gap) + ch / 2
    parts.append(svg_text(x0 - 22, ry + 2, 38, INK, cohort, anchor="end", weight="600"))
    parts.append(svg_text(x0 - 22, ry + 42, 34, INK_MUTED, f"n={size:,}", anchor="end", extra='font-style="italic"'))

ytx, yty = x0 - 300, y0 + gh / 2
parts.append(svg_text(ytx, yty, 44, INK_SOFT, COHORT, weight="600", extra=f'transform="rotate(-90, {ytx}, {yty})"'))

for i, cohort in enumerate(table.index):
    for j, v in enumerate(table.loc[cohort]):
        if math.isnan(v):
            continue
        color = ramp_color(SEQ_FIELDS, (v - min_val) / span)
        cx, cy = x0 + j * (cw + gap), y0 + i * (ch + gap)
        parts.append(
            f"<g><title>{cohort}, Month {table.columns[j]}: {v:.1f}%</title>"
            f'<rect x="{cx:.1f}" y="{cy:.1f}" width="{cw:.1f}" height="{ch:.1f}" rx="5" ry="5" '
            f'fill="{color}" stroke="{ELEVATED_BG}" stroke-width="1.5"/>'
            + svg_text(cx + cw / 2, cy + ch / 2 + 14, 40, text_on(color), f"{v:.0f}%", weight="600")
            + "</g>"
        )

# Color bar: high retention on top, round ticks
cb_w, cb_h = 48, gh * 0.8
cb_x, cb_y = x0 + gw + 50, y0 + (gh - cb_h) / 2
stops = "".join(f'<stop offset="{f * 5}%" stop-color="{ramp_color(SEQ_FIELDS, 1.0 - f / 20)}"/>' for f in range(21))
parts.append(
    f'<defs><linearGradient id="cb-gradient" x1="0" y1="0" x2="0" y2="1">{stops}</linearGradient></defs>'
    f'<rect x="{cb_x:.1f}" y="{cb_y:.1f}" width="{cb_w}" height="{cb_h:.1f}" rx="4" ry="4" '
    f'fill="url(#cb-gradient)" stroke="{INK_MUTED}" stroke-width="1"/>'
)
for tick in range(math.ceil(min_val / 20) * 20, int(max_val // 20) * 20 + 1, 20):
    ty = cb_y + cb_h * (max_val - tick) / span
    parts.append(
        f'<line x1="{cb_x + cb_w}" y1="{ty:.1f}" x2="{cb_x + cb_w + 10}" y2="{ty:.1f}" stroke="{INK_SOFT}" stroke-width="1.5"/>'
        + svg_text(cb_x + cb_w + 16, ty + 14, 40, INK, f"{tick}%", anchor="start")
    )
parts.append(svg_text(cb_x - 40, cb_y - 36, 38, INK_SOFT, RETENTION, anchor="start", weight="600"))

custom_style = Style(
    background=PAGE_BG,
    plot_background=PAGE_BG,
    foreground=INK,
    foreground_strong=INK,
    foreground_subtle=INK_MUTED,
    guide_stroke_color=INK_MUTED,
    major_guide_stroke_color=INK_MUTED,
    colors=tuple(IMPRINT_PALETTE),
    title_font_size=66,
    label_font_size=44,
    major_label_font_size=44,
    legend_font_size=44,
    value_font_size=36,
    stroke_width=2.5,
)

# pygal has no heatmap type: an empty pygal chart supplies page and title, the cells are SVG added to it
chart = pygal.Bar(
    width=2400,
    height=2400,
    style=custom_style,
    title="heatmap-cohort-retention · python · pygal · anyplot.ai",
    show_legend=False,
    show_x_labels=False,
    show_y_labels=False,
    show_y_guides=False,
    margin=40,
    margin_top=40,
)
chart.add("data", [0])
svg = chart.render(is_unicode=True)
cut = svg.rindex("</svg>")
svg = svg[:cut] + "<g>" + "".join(parts) + "</g>" + svg[cut:]

# Save
cairosvg.svg2png(bytestring=svg.encode("utf-8"), write_to=f"plot-{THEME}.png")
with open(f"plot-{THEME}.svg", "w", encoding="utf-8") as f:
    f.write(svg)

html_content = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>heatmap-cohort-retention · python · pygal · anyplot.ai</title>
    <style>
        body {{ margin: 0; background: {PAGE_BG}; display: flex; justify-content: center; align-items: center; min-height: 100vh; }}
    </style>
</head>
<body>
    {svg}
</body>
</html>"""

with open(f"plot-{THEME}.html", "w", encoding="utf-8") as f:
    f.write(html_content)
