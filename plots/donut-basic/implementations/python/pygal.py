""" anyplot.ai
donut-basic: Basic Donut Chart
Library: pygal 3.1.0 | Python 3.14.4
Quality: 88/100 | Updated: 2026-04-24
"""

import os
import re
import sys


# Script filename shadows the installed `pygal` package when run as `python pygal.py`;
# dropping the script directory from sys.path lets the real package resolve.
sys.path.pop(0)

import cairosvg  # noqa: E402
import pygal  # noqa: E402
from pygal.style import Style  # noqa: E402


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
INK_MUTED = "#6B6A63" if THEME == "light" else "#A8A79F"

# Okabe-Ito categorical palette — first series is always brand green
OKABE_ITO = ("#009E73", "#D55E00", "#0072B2", "#CC79A7", "#E69F00", "#56B4E9", "#F0E442")

# Data — Annual budget allocation by department (USD thousands)
categories = ["Engineering", "Operations", "Marketing", "Sales", "Support"]
values = [480, 210, 155, 125, 55]
total = sum(values)

font = "DejaVu Sans, Helvetica, Arial, sans-serif"

custom_style = Style(
    background=PAGE_BG,
    plot_background=PAGE_BG,
    foreground=INK_SOFT,
    foreground_strong=INK,
    foreground_subtle=INK_MUTED,
    colors=OKABE_ITO,
    font_family=font,
    title_font_family=font,
    label_font_family=font,
    major_label_font_family=font,
    legend_font_family=font,
    tooltip_font_family=font,
    value_font_family=font,
    title_font_size=72,
    label_font_size=48,
    major_label_font_size=42,
    legend_font_size=48,
    tooltip_font_size=36,
    value_font_size=52,
    value_colors=["#F0EFE8"] * len(categories),
    opacity=1,
    opacity_hover=0.85,
    transition="200ms ease-in",
)

# Square canvas — 3600 × 3600 works best for circular charts at ~13 MP
chart = pygal.Pie(
    width=3600,
    height=3600,
    style=custom_style,
    inner_radius=0.58,
    title="Budget by Department · donut-basic · pygal · anyplot.ai",
    show_legend=True,
    legend_at_bottom=True,
    legend_at_bottom_columns=len(categories),
    legend_box_size=52,
    margin=40,
    print_values=True,
    print_values_position="inside",
    print_labels=False,
    value_formatter=lambda v: f"{v / total * 100:.1f}%",
    truncate_legend=-1,
)

for cat, val in zip(categories, values, strict=True):
    chart.add(cat, val)

# Render to SVG, then inject center-label text (pygal has no native donut-hole label).
svg_text = chart.render(is_unicode=True)

# Locate plot-group translate and the first slice's top-of-arc anchor so we can
# compute the exact donut center in SVG coordinates.
plot_match = re.search(r'<g transform="translate\(([\d.\-]+),\s*([\d.\-]+)\)"\s+class="plot"', svg_text)
plot_x = float(plot_match.group(1))
plot_y = float(plot_match.group(2))

slice_match = re.search(r'<path d="M([\d.\-]+)\s+([\d.\-]+)\s+A([\d.\-]+)', svg_text)
top_x = float(slice_match.group(1))
top_y = float(slice_match.group(2))
outer_r = float(slice_match.group(3))

cx = plot_x + top_x
cy = plot_y + top_y + outer_r

# Center metric: "Total budget" (secondary label, above) + formatted total
# (primary headline, below). Baselines spaced to avoid visual collision at 180px.
center_text = (
    f'<g class="center-metric">'
    f'<text x="{cx:.2f}" y="{cy - 80:.2f}" text-anchor="middle" '
    f'fill="{INK_SOFT}" style="font-size:72px;letter-spacing:3px;'
    f'text-transform:uppercase;font-family:{font};">Total Budget</text>'
    f'<text x="{cx:.2f}" y="{cy + 120:.2f}" text-anchor="middle" '
    f'fill="{INK}" style="font-size:220px;font-weight:700;font-family:{font};">${total:,}K</text>'
    f"</g>"
)

output_svg = svg_text.replace("</svg>", f"{center_text}</svg>")

cairosvg.svg2png(bytestring=output_svg.encode("utf-8"), write_to=f"plot-{THEME}.png", output_width=3600)

html_content = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>donut-basic · pygal · anyplot.ai</title>
    <style>
        body {{ margin: 0; background: {PAGE_BG}; display: flex;
                justify-content: center; align-items: center; min-height: 100vh; }}
        .chart {{ max-width: 100%; height: auto; }}
    </style>
</head>
<body>
    <figure class="chart">
        {output_svg}
    </figure>
</body>
</html>
"""

with open(f"plot-{THEME}.html", "w", encoding="utf-8") as f:
    f.write(html_content)
