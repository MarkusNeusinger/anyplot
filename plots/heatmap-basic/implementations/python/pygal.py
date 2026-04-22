""" pyplots.ai
heatmap-basic: Basic Heatmap
Library: pygal 3.1.0 | Python 3.14.3
Quality: 82/100 | Updated: 2026-02-16
"""

import importlib
import re
import sys

import numpy as np


# Import pygal avoiding name collision with this filename
_cwd = sys.path[0]
sys.path[:] = [p for p in sys.path if p != _cwd]
_pygal = importlib.import_module("pygal")
_Style = importlib.import_module("pygal.style").Style
_cairosvg = importlib.import_module("cairosvg")
sys.path.insert(0, _cwd)

# ---------------------------------------------------------------------------
# Data — Monthly website traffic (thousands) across content categories
# ---------------------------------------------------------------------------
np.random.seed(42)

categories = ["Tech", "Science", "Health", "Finance", "Sports", "Travel", "Food", "Culture"]
months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]

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

matrix = []
for cat in categories:
    row = [max(40, v + np.random.randint(-5, 6)) for v in base_traffic[cat]]
    matrix.append(row)

all_vals = [v for row in matrix for v in row]
vmin, vmax = min(all_vals), max(all_vals)

# ---------------------------------------------------------------------------
# Sequential blue colormap — 8 gradient stops
# ---------------------------------------------------------------------------
color_stops = [
    (0.00, (247, 251, 255)),
    (0.15, (222, 235, 247)),
    (0.30, (198, 219, 239)),
    (0.45, (158, 202, 225)),
    (0.60, (107, 174, 214)),
    (0.75, (49, 130, 189)),
    (0.88, (8, 81, 156)),
    (1.00, (8, 48, 107)),
]

# ---------------------------------------------------------------------------
# Build heatmap using pygal HorizontalStackedBar
# Each month is a series (column), each category is a row (x_label).
# Per-value color dicts give each cell its heatmap color.
# ---------------------------------------------------------------------------
custom_style = _Style(
    background="white",
    plot_background="white",
    foreground="#333333",
    foreground_strong="#222222",
    foreground_subtle="#aaaaaa",
    colors=("#306998",) * 12,
    title_font_size=54,
    label_font_size=34,
    major_label_font_size=30,
    legend_font_size=28,
    value_font_size=26,
    font_family="sans-serif",
)

chart = _pygal.HorizontalStackedBar(
    width=4800,
    height=2700,
    style=custom_style,
    title="heatmap-basic \u00b7 pygal \u00b7 pyplots.ai",
    show_legend=False,
    print_values=True,
    value_font_size=26,
    show_y_guides=False,
    show_x_guides=False,
    show_x_labels=False,
    margin_top=220,
    margin_bottom=80,
    margin_left=400,
    margin_right=440,
    range=(0, 12),
    spacing=0,
    rounded_bars=1,
)
chart.x_labels = categories

# Map value to RGB color using sequential blue palette (inline, no function)
cell_rgb = {}
for j, month in enumerate(months):
    series_data = []
    for i in range(len(categories)):
        v = matrix[i][j]
        # Interpolate color inline
        t = max(0.0, min(1.0, (v - vmin) / (vmax - vmin)))
        r, g, b = color_stops[-1][1]
        for k in range(len(color_stops) - 1):
            t0, c0 = color_stops[k]
            t1, c1 = color_stops[k + 1]
            if t <= t1:
                f = (t - t0) / (t1 - t0) if t1 > t0 else 0
                r = int(c0[0] + (c1[0] - c0[0]) * f)
                g = int(c0[1] + (c1[1] - c0[1]) * f)
                b = int(c0[2] + (c1[2] - c0[2]) * f)
                break
        hex_color = f"#{r:02x}{g:02x}{b:02x}"
        cell_rgb[(i, j)] = (r, g, b)
        series_data.append({"value": 1, "color": hex_color, "formatter": lambda x, val=v: str(val)})
    chart.add(month, series_data)

# Render SVG via pygal
svg = chart.render(is_unicode=True)

# ---------------------------------------------------------------------------
# Post-process SVG: brightness-adaptive text colors for value annotations
# pygal renders value texts grouped by series (month). Within each series,
# texts are ordered by y-position; pygal reverses category order so highest-y
# = first category (Tech, index 0). We recolor each value text based on cell
# background brightness for optimal readability.
# ---------------------------------------------------------------------------
overlay_match = re.search(
    r'(<g[^>]*class="plot text-overlay">)(.*?)(</g>\s*<g[^>]*class="plot tooltip-overlay")', svg, re.DOTALL
)
if overlay_match:
    overlay_content = overlay_match.group(2)
    # Process each series group within the text overlay
    for serie_match in re.finditer(r'(<g class="series serie-(\d+)[^"]*">)(.*?)(</g>)', overlay_content, re.DOTALL):
        j = int(serie_match.group(2))
        serie_content = serie_match.group(3)
        # Find all value texts, sort by y-position (descending = category order)
        value_texts = [
            (float(m.group(2)), m)
            for m in re.finditer(
                r'(<text\s+text-anchor="middle"\s+x="[^"]+"\s+y="([^"]+)"\s+class="value">)(\d+)(</text>)',
                serie_content,
            )
        ]
        value_texts.sort(key=lambda x: x[0], reverse=True)
        new_serie = serie_content
        for rank, (_, m) in enumerate(value_texts):
            r, g, b = cell_rgb.get((rank, j), (200, 200, 200))
            brightness = (r * 299 + g * 587 + b * 114) / 1000
            txt_color = "#ffffff" if brightness < 140 else "#1a1a1a"
            old_tag = m.group(0)
            new_tag = m.group(1).replace('class="value"', f'class="value" fill="{txt_color}"') + m.group(3) + m.group(4)
            new_serie = new_serie.replace(old_tag, new_tag, 1)
        overlay_content = overlay_content.replace(serie_match.group(3), new_serie, 1)
    svg = svg[: overlay_match.start(2)] + overlay_content + svg[overlay_match.end(2) :]

# ---------------------------------------------------------------------------
# Inject subtitle, month column headers, colorbar, and peak annotations
# These elements augment the pygal-rendered chart. Insert before </svg>.
# ---------------------------------------------------------------------------
W, H = 4800, 2700
n_rows = len(categories)

# Extract plot area bounds from pygal's rendered SVG
_transform_match = re.search(r"translate\(([^,]+),\s*([^)]+)\)", svg)
plot_x = float(_transform_match.group(1)) if _transform_match else 552
plot_y = float(_transform_match.group(2)) if _transform_match else 224

_bg_rects = re.findall(r'<rect[^>]*width="([^"]+)"[^>]*height="([^"]+)"[^>]*class="background"', svg)
if len(_bg_rects) >= 2:
    plot_w, plot_h = float(_bg_rects[1][0]), float(_bg_rects[1][1])
else:
    plot_w, plot_h = 3887.2, 2252.0

grid_left = plot_x
grid_top = plot_y
grid_right = plot_x + plot_w
grid_bottom = plot_y + plot_h
cell_w = plot_w / 12
cell_h = plot_h / n_rows

extra_svg = []

# Subtitle
extra_svg.append(
    f'<text x="{W / 2}" y="{grid_top - 76}" text-anchor="middle" fill="#666666" '
    f'style="font-size:28px;font-weight:400;font-family:sans-serif">'
    f"Monthly website traffic (thousands of visits) by content category</text>"
)

# Month column headers directly above the grid
for j, month in enumerate(months):
    mx = grid_left + j * cell_w + cell_w / 2
    extra_svg.append(
        f'<text x="{mx:.0f}" y="{grid_top - 24}" text-anchor="middle" fill="#333333" '
        f'style="font-size:30px;font-weight:600;font-family:sans-serif">{month}</text>'
    )

# Axis title: Content Category (rotated, left of row labels)
mid_y = (grid_top + grid_bottom) / 2
extra_svg.append(
    f'<text x="{grid_left - 300}" y="{mid_y:.0f}" text-anchor="middle" fill="#333333" '
    f'style="font-size:38px;font-weight:bold;font-family:sans-serif" '
    f'transform="rotate(-90, {grid_left - 300}, {mid_y:.0f})">Content Category</text>'
)

# Colorbar (right of grid, within margin)
cb_x = grid_right + 30
cb_w = 50
cb_top = grid_top + 30
cb_bot = grid_bottom - 30
cb_h = cb_bot - cb_top
n_segs = 60

for s in range(n_segs):
    sv = vmax - (vmax - vmin) * s / (n_segs - 1)
    sy = cb_top + cb_h * s / n_segs
    t = max(0.0, min(1.0, (sv - vmin) / (vmax - vmin)))
    cr, cg, cb_val = color_stops[-1][1]
    for k in range(len(color_stops) - 1):
        t0, c0 = color_stops[k]
        t1, c1 = color_stops[k + 1]
        if t <= t1:
            frac = (t - t0) / (t1 - t0) if t1 > t0 else 0
            cr = int(c0[0] + (c1[0] - c0[0]) * frac)
            cg = int(c0[1] + (c1[1] - c0[1]) * frac)
            cb_val = int(c0[2] + (c1[2] - c0[2]) * frac)
            break
    hex_c = f"#{cr:02x}{cg:02x}{cb_val:02x}"
    extra_svg.append(f'<rect x="{cb_x}" y="{sy:.1f}" width="{cb_w}" height="{cb_h / n_segs + 1:.1f}" fill="{hex_c}"/>')

extra_svg.append(
    f'<rect x="{cb_x}" y="{cb_top}" width="{cb_w}" height="{cb_h}" fill="none" stroke="#999999" stroke-width="1.5"/>'
)

for frac_pos, label_val in [(0.0, vmax), (0.5, (vmin + vmax) / 2), (1.0, vmin)]:
    ty = cb_top + cb_h * frac_pos
    extra_svg.append(
        f'<text x="{cb_x + cb_w + 14}" y="{ty + 10:.0f}" fill="#333333" '
        f'style="font-size:28px;font-family:sans-serif">{label_val:.0f}</text>'
    )

extra_svg.append(
    f'<text x="{cb_x + cb_w / 2}" y="{cb_top - 20}" text-anchor="middle" '
    f'fill="#333333" style="font-size:30px;font-weight:bold;font-family:sans-serif">'
    f"Visits (k)</text>"
)

# Storytelling: peak annotations with gold highlight
# pygal renders rows bottom-to-top: row 0 (Tech) at bottom, row 7 (Culture) at top
for row_i, col_j, label in [(3, 11, "Year-end peak"), (5, 7, "Summer peak")]:
    svg_row = n_rows - 1 - row_i
    ax = grid_left + col_j * cell_w + cell_w / 2
    ay = grid_top + svg_row * cell_h + cell_h * 0.82
    extra_svg.append(
        f'<text x="{ax:.0f}" y="{ay:.0f}" text-anchor="middle" fill="#b8860b" '
        f'style="font-size:20px;font-weight:bold;font-family:sans-serif;font-style:italic">'
        f"\u25bc {label}</text>"
    )

# Inject extra SVG before closing </svg>
svg = svg.replace("</svg>", "\n".join(extra_svg) + "\n</svg>")

# ---------------------------------------------------------------------------
# Save outputs
# ---------------------------------------------------------------------------
_cairosvg.svg2png(bytestring=svg.encode("utf-8"), write_to="plot.png", output_width=4800, output_height=2700)

with open("plot.svg", "w", encoding="utf-8") as fout:
    fout.write(svg)

# Interactive HTML using pygal's native rendered SVG with tooltips
pygal_interactive_svg = chart.render(is_unicode=True)
html_content = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>heatmap-basic - pygal</title>
    <style>
        body {{ margin: 0; display: flex; justify-content: center; align-items: center;
               min-height: 100vh; background: #f5f5f5; }}
        .chart {{ max-width: 100%; height: auto; }}
    </style>
</head>
<body>
    <figure class="chart">
        {pygal_interactive_svg}
    </figure>
</body>
</html>
"""

with open("plot.html", "w", encoding="utf-8") as fout:
    fout.write(html_content)
