""" pyplots.ai
heatmap-stripes-climate: Climate Warming Stripes
Library: pygal 3.1.0 | Python 3.14.3
Quality: 69/100 | Created: 2026-03-06
"""

import importlib
import sys

import numpy as np


# Import pygal avoiding name collision with this filename
_cwd = sys.path[0]
sys.path[:] = [p for p in sys.path if p != _cwd]
_pygal = importlib.import_module("pygal")
_Style = importlib.import_module("pygal.style").Style
_cairosvg = importlib.import_module("cairosvg")
sys.path.insert(0, _cwd)

# Data - Simulated global temperature anomalies (relative to 1961-1990 baseline)
np.random.seed(42)
years = list(range(1850, 2025))
n_years = len(years)

# Build realistic warming trend: slight cooling mid-century, strong warming post-1980
base_trend = np.concatenate(
    [
        np.linspace(-0.35, -0.15, 50),
        np.linspace(-0.15, -0.25, 30),
        np.linspace(-0.25, -0.05, 30),
        np.linspace(-0.05, 0.30, 25),
        np.linspace(0.30, 1.20, 40),
    ]
)
noise = np.random.normal(0, 0.10, n_years)
anomalies = base_trend + noise
anomalies = np.round(anomalies, 2)

# Diverging blue-to-red color stops (symmetric around 0)
vmax = max(abs(anomalies.min()), abs(anomalies.max()))
vmin = -vmax

color_stops = [
    (0.00, (8, 48, 107)),
    (0.15, (33, 102, 172)),
    (0.30, (103, 169, 207)),
    (0.45, (209, 229, 240)),
    (0.50, (247, 247, 247)),
    (0.55, (253, 219, 199)),
    (0.70, (239, 138, 98)),
    (0.85, (214, 47, 39)),
    (1.00, (103, 0, 13)),
]

# Build SVG directly for maximum control over this minimalist visualization
W, H = 4800, 1600
bar_w = W / n_years

svg_parts = [
    f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}">',
    f'<rect width="{W}" height="{H}" fill="white"/>',
]

# Title area
title_y = 80
svg_parts.append(
    f'<text x="{W / 2}" y="{title_y}" text-anchor="middle" fill="#333333" '
    f'style="font-size:48px;font-weight:600;font-family:sans-serif">'
    f"heatmap-stripes-climate \u00b7 pygal \u00b7 pyplots.ai</text>"
)

# Stripes area
stripe_top = 140
stripe_bottom = H - 160
stripe_h = stripe_bottom - stripe_top

for i, anomaly in enumerate(anomalies):
    t = max(0.0, min(1.0, (anomaly - vmin) / (vmax - vmin)))
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
    x = i * bar_w
    svg_parts.append(
        f'<rect x="{x:.2f}" y="{stripe_top}" width="{bar_w + 0.5:.2f}" height="{stripe_h}" fill="{hex_color}"/>'
    )

# Year labels at start and end
label_y = stripe_bottom + 55
svg_parts.append(
    f'<text x="{bar_w * 2:.0f}" y="{label_y}" text-anchor="start" fill="#555555" '
    f'style="font-size:38px;font-family:sans-serif">{years[0]}</text>'
)
svg_parts.append(
    f'<text x="{W - bar_w * 2:.0f}" y="{label_y}" text-anchor="end" fill="#555555" '
    f'style="font-size:38px;font-family:sans-serif">{years[-1]}</text>'
)

svg_parts.append("</svg>")
svg = "\n".join(svg_parts)

# Save PNG
_cairosvg.svg2png(bytestring=svg.encode("utf-8"), write_to="plot.png", output_width=W, output_height=H)

# Save SVG
with open("plot.svg", "w", encoding="utf-8") as fout:
    fout.write(svg)

# Interactive HTML with pygal bar chart for tooltip support
custom_style = _Style(
    background="white",
    plot_background="white",
    foreground="#333333",
    foreground_strong="#222222",
    foreground_subtle="#cccccc",
    colors=("#306998",),
    title_font_size=36,
    label_font_size=14,
    major_label_font_size=18,
    legend_font_size=16,
    value_font_size=12,
    font_family="sans-serif",
)

chart = _pygal.Bar(
    width=4800,
    height=1600,
    style=custom_style,
    title="heatmap-stripes-climate \u00b7 pygal \u00b7 pyplots.ai",
    show_legend=False,
    show_y_guides=False,
    show_x_guides=False,
    margin=0,
    margin_top=120,
    margin_bottom=100,
    spacing=0,
    show_y_labels=False,
)

# Show x labels every 25 years
chart.x_labels = [str(y) if y % 25 == 0 else "" for y in years]

# Add each year as individual series for per-bar coloring
for i, (year, anomaly) in enumerate(zip(years, anomalies, strict=True)):
    t = max(0.0, min(1.0, (anomaly - vmin) / (vmax - vmin)))
    r, g, b = color_stops[-1][1]
    for k in range(len(color_stops) - 1):
        t0, c0 = color_stops[k]
        t1, c1 = color_stops[k + 1]
        if t <= t1:
            frac = (t - t0) / (t1 - t0) if t1 > t0 else 0
            r = int(c0[0] + (c1[0] - c0[0]) * frac)
            g = int(c0[1] + (c1[1] - c0[1]) * frac)
            b = int(c0[2] + (c1[2] - c0[2]) * frac)
            break
    hex_color = f"#{r:02x}{g:02x}{b:02x}"
    data = [None] * i + [{"value": anomaly, "color": hex_color}] + [None] * (n_years - i - 1)
    chart.add(str(year), data)

interactive_svg = chart.render(is_unicode=True)
html_content = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>heatmap-stripes-climate - pygal</title>
    <style>
        body {{ margin: 0; display: flex; justify-content: center; align-items: center;
               min-height: 100vh; background: #f5f5f5; }}
        .chart {{ max-width: 100%; height: auto; }}
    </style>
</head>
<body>
    <figure class="chart">
        {interactive_svg}
    </figure>
</body>
</html>
"""

with open("plot.html", "w", encoding="utf-8") as fout:
    fout.write(html_content)
