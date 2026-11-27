""" anyplot.ai
heatmap-basic: Basic Heatmap
Library: pygal 3.1.3 | Python 3.14.10
Quality: 77/100 | Updated: 2026-11-27
"""

import importlib
import math
import os
import re
import sys
from itertools import pairwise

import numpy as np
import pandas as pd


# Import pygal avoiding name collision with this filename
_cwd = sys.path[0]
sys.path[:] = [p for p in sys.path if p != _cwd]
_pygal = importlib.import_module("pygal")
_Style = importlib.import_module("pygal.style").Style
_cairosvg = importlib.import_module("cairosvg")
sys.path.insert(0, _cwd)

# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
INK_MUTED = "#6B6A63" if THEME == "light" else "#A8A79F"

# Imprint palette: all eight positions in canonical order
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

# imprint_seq, fields stops (colored cells fill the plot), low -> high, per theme
SEQ_FIELDS = (
    [(0.0, "#66E2B2"), (0.369, "#009E73"), (0.803, "#024582"), (1.0, "#351E45")]
    if THEME == "light"
    else [(0.0, "#404C02"), (0.487, "#009E73"), (1.0, "#CDD9FF")]
)

# Columns: set these to your table's column names
CATEGORY = "Content Category"  # role: y
MONTH = "Month"  # role: x
VISITS = "Visits (k)"  # role: value


def ramp_color(stops, t):
    """The hex at t (0 to 1) along (position, hex) stops, blended linearly in sRGB."""
    if not math.isfinite(t):
        return "none"  # a missing value draws nothing, never the low end
    t = min(max(t, 0.0), 1.0)
    (p0, c0), (p1, c1) = next((a, b) for a, b in pairwise(stops) if t <= b[0])
    share = (t - p0) / (p1 - p0)
    return "#" + "".join(
        f"{round(int(c0[i : i + 2], 16) * (1 - share) + int(c1[i : i + 2], 16) * share):02X}" for i in (1, 3, 5)
    )


# Data: replace this block with your own table, for example df = pd.read_csv("traffic.csv")
np.random.seed(42)
sample_months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
base_traffic = {
    "Tech": [120, 115, 130, 135, 140, 125, 110, 105, 145, 155, 160, 150],
    "Science": [85, 80, 90, 95, 88, 82, 78, 75, 92, 98, 95, 88],
    "Health": [95, 110, 105, 100, 90, 85, 80, 82, 115, 120, 108, 130],
    "Finance": [140, 135, 150, 145, 130, 125, 120, 118, 155, 160, 165, 173],
    "Sports": [70, 65, 80, 85, 95, 100, 105, 110, 90, 75, 72, 68],
    "Travel": [60, 55, 75, 90, 110, 130, 140, 148, 105, 80, 65, 58],
    "Food": [88, 82, 85, 90, 95, 92, 98, 100, 88, 92, 105, 115],
    "Culture": [72, 68, 78, 82, 85, 88, 75, 70, 80, 90, 95, 92],
}
sample_categories = sorted(base_traffic, key=lambda c: sum(base_traffic[c]) / len(sample_months))
rows = [
    (cat, month, max(40, v + np.random.randint(-5, 6)))
    for cat in sample_categories
    for month, v in zip(sample_months, base_traffic[cat], strict=True)
]
df = pd.DataFrame(rows, columns=[CATEGORY, MONTH, VISITS])

# Plot
table = df.pivot_table(index=CATEGORY, columns=MONTH, values=VISITS, sort=False).astype(float)
categories = table.index.tolist()
months = table.columns.tolist()
vmin, vmax = np.nanmin(table.to_numpy()), np.nanmax(table.to_numpy())
span = (vmax - vmin) or 1.0


def cell_color(value):
    return ramp_color(SEQ_FIELDS, (value - vmin) / span)


title = "heatmap-basic · python · pygal · anyplot.ai"
title_font_size = max(44, round(66 * 67 / len(title))) if len(title) > 67 else 66

custom_style = _Style(
    background=PAGE_BG,
    plot_background=PAGE_BG,
    foreground=INK,
    foreground_strong=INK,
    foreground_subtle=INK_MUTED,
    colors=tuple(IMPRINT_PALETTE),
    title_font_size=title_font_size,
    label_font_size=44,
    major_label_font_size=44,
    legend_font_size=44,
    value_font_size=36,
    font_family="sans-serif",
)

chart = _pygal.HorizontalStackedBar(
    width=2400,
    height=2400,
    style=custom_style,
    title=title,
    show_legend=False,
    print_values=True,
    value_font_size=36,
    show_y_guides=False,
    show_x_guides=False,
    show_x_labels=False,
    margin_top=200,
    margin_bottom=100,
    margin_left=300,
    margin_right=450,
    range=(0, len(months)),
    spacing=0,
    rounded_bars=1,
)
chart.x_labels = categories

for month in months:
    chart.add(
        str(month),
        [
            {
                "value": 1,
                "color": cell_color(table.loc[cat, month]),
                "formatter": lambda x, v=table.loc[cat, month]: "" if math.isnan(v) else f"{v:.0f}",
            }
            for cat in categories
        ],
    )

# Render SVG via pygal
svg = chart.render(is_unicode=True)


def text_color_on(hex_color):
    """Ink or white, whichever has the higher contrast against the cell color."""
    if hex_color == "none":
        return INK
    r, g, b = (int(hex_color[i : i + 2], 16) / 255 for i in (1, 3, 5))
    lin = [c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4 for c in (r, g, b)]
    lum = 0.2126 * lin[0] + 0.7152 * lin[1] + 0.0722 * lin[2]
    return "#F0EFE8" if 1.05 / (lum + 0.05) > (lum + 0.05) / 0.0607 else "#1A1A17"


# Post-process SVG: per-cell text color chosen by cell darkness
overlay_match = re.search(
    r'(<g[^>]*class="plot text-overlay">)(.*?)(</g>\s*<g[^>]*class="plot tooltip-overlay")', svg, re.DOTALL
)
if overlay_match:
    overlay_content = overlay_match.group(2)
    for serie_match in re.finditer(r'(<g class="series serie-(\d+)[^"]*">)(.*?)(</g>)', overlay_content, re.DOTALL):
        col_j = int(serie_match.group(2))
        serie_content = serie_match.group(3)
        value_texts = sorted(
            [
                (float(m.group(2)), m)
                for m in re.finditer(
                    r'(<text\s+text-anchor="middle"\s+x="[^"]+"\s+y="([^"]+)"\s+class="value">)(\d+)(</text>)',
                    serie_content,
                )
            ],
            key=lambda x: x[0],
            reverse=True,
        )
        new_serie = serie_content
        for rank, (_, m) in enumerate(value_texts):
            txt_color = text_color_on(cell_color(table.iloc[rank, col_j]))
            new_tag = (
                m.group(1).replace('class="value"', f'class="value" style="fill:{txt_color}"') + m.group(3) + m.group(4)
            )
            new_serie = new_serie.replace(m.group(0), new_tag, 1)
        overlay_content = overlay_content.replace(serie_match.group(3), new_serie, 1)
    svg = svg[: overlay_match.start(2)] + overlay_content + svg[overlay_match.end(2) :]

# Inject month headers, axis titles and colorbar before </svg>
W = 2400

transform_match = re.search(r"translate\(([^,]+),\s*([^)]+)\)", svg)
grid_left = float(transform_match.group(1)) if transform_match else 400
grid_top = float(transform_match.group(2)) if transform_match else 200

bg_rects = re.findall(r'<rect[^>]*width="([^"]+)"[^>]*height="([^"]+)"[^>]*class="background"', svg)
plot_w, plot_h = (float(bg_rects[1][0]), float(bg_rects[1][1])) if len(bg_rects) >= 2 else (1720.0, 2100.0)
grid_right = grid_left + plot_w
grid_bottom = grid_top + plot_h
cell_w = plot_w / len(months)

extra = [
    f'<text x="{W / 2:.0f}" y="{grid_top - 55:.0f}" text-anchor="middle" fill="{INK_SOFT}" '
    f'style="font-size:30px;font-family:sans-serif">'
    f"Monthly website traffic (thousands of visits) by content category</text>"
]

for col_j, mn in enumerate(months):
    mx = grid_left + col_j * cell_w + cell_w / 2
    extra.append(
        f'<text x="{mx:.0f}" y="{grid_top - 18:.0f}" text-anchor="middle" fill="{INK}" '
        f'style="font-size:32px;font-weight:600;font-family:sans-serif">{mn}</text>'
    )

extra.append(
    f'<text x="{(grid_left + grid_right) / 2:.0f}" y="{grid_bottom + 52:.0f}" '
    f'text-anchor="middle" fill="{INK}" '
    f'style="font-size:40px;font-weight:bold;font-family:sans-serif">{MONTH}</text>'
)

mid_y = (grid_top + grid_bottom) / 2
extra.append(
    f'<text x="{grid_left - 230:.0f}" y="{mid_y:.0f}" text-anchor="middle" fill="{INK}" '
    f'style="font-size:40px;font-weight:bold;font-family:sans-serif" '
    f'transform="rotate(-90,{grid_left - 230:.0f},{mid_y:.0f})">{CATEGORY}</text>'
)

# Colorbar: 60 stops, top = vmax, bottom = vmin
N_CB = 60
cb_x = grid_right + 50
cb_w = 36
cb_top = grid_top + 18
cb_h = plot_h - 36
for s in range(N_CB):
    sy = cb_top + cb_h * s / N_CB
    extra.append(
        f'<rect x="{cb_x:.0f}" y="{sy:.1f}" width="{cb_w}" height="{cb_h / N_CB + 1:.1f}" '
        f'fill="{ramp_color(SEQ_FIELDS, 1.0 - s / (N_CB - 1))}"/>'
    )
extra.append(
    f'<rect x="{cb_x:.0f}" y="{cb_top:.0f}" width="{cb_w}" height="{cb_h:.0f}" '
    f'fill="none" stroke="{INK_MUTED}" stroke-width="1.5"/>'
)
for frac, label_val in [(0.0, vmax), (0.5, (vmin + vmax) / 2), (1.0, vmin)]:
    ty = cb_top + cb_h * frac
    extra.append(
        f'<text x="{cb_x + cb_w + 10:.0f}" y="{ty + 12:.0f}" fill="{INK_SOFT}" '
        f'style="font-size:34px;font-family:sans-serif">{label_val:.0f}</text>'
    )
extra.append(
    f'<text x="{cb_x + cb_w / 2:.0f}" y="{cb_top - 40:.0f}" text-anchor="middle" '
    f'fill="{INK}" style="font-size:30px;font-weight:bold;font-family:sans-serif">{VISITS}</text>'
)

svg = svg.replace("</svg>", "\n".join(extra) + "\n</svg>")

# Save
_cairosvg.svg2png(bytestring=svg.encode("utf-8"), write_to=f"plot-{THEME}.png", output_width=2400, output_height=2400)

with open(f"plot-{THEME}.html", "w", encoding="utf-8") as fout:
    fout.write(
        f'<!DOCTYPE html>\n<html>\n<head>\n<meta charset="utf-8">\n'
        f"<title>heatmap-basic - python - pygal - anyplot.ai</title>\n"
        f"<style>body{{margin:0;display:flex;justify-content:center;align-items:center;"
        f"min-height:100vh;background:{PAGE_BG};}}.chart{{max-width:100%;height:auto;}}</style>\n"
        f'</head>\n<body>\n<figure class="chart">\n{chart.render(is_unicode=True)}\n</figure>\n</body>\n</html>\n'
    )
